from langchain_core.messages import AIMessage

from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.objective_remediation import (
    build_variant_question_generator_node,
    build_wrong_question_explainer_node,
)

FORBIDDEN_VISIBLE_VARIANT_META_TEXT = [
    "变式验证",
    "换成另一个",
    "抓住关键关系",
    "在新情境中仍能判断",
    "沿用原错因",
]


def _visible_variant_text(variant):
    return " ".join([variant.get("stem", ""), *(variant.get("options") or {}).values()])


class FakeLLM:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return AIMessage(content=self.text)


class SequenceLLM:
    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        index = min(len(self.calls) - 1, len(self.texts) - 1)
        return AIMessage(content=self.texts[index])


WRONG_ITEM = {
    "question_id": "Q1",
    "node_id": "KM001",
    "stem": "比较元件处标注为“-”表示哪种反馈方式？",
    "options": {
        "A": "负反馈",
        "B": "正反馈",
        "C": "开环控制",
        "D": "前馈补偿",
    },
    "answer_key": "A",
    "user_answer": "B",
    "explanation": "",
}


def test_wrong_question_explainer_uses_llm_with_question_user_answer_and_correct_answer():
    llm = FakeLLM(
        '{"explanations":[{"question_id":"Q1","explanation":"比较点的减号表示反馈信号要从给定输入中相减，因此是负反馈；你选 B 是把反馈极性反过来了。"}]}'
    )
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_wrong_question_explainer_node(runtime, llm=llm)

    result = node({"node_quiz_wrong_items": [WRONG_ITEM], "node_quiz_score": 0})

    assert len(llm.calls) == 1
    prompt_text = "\n".join(str(m.content) for m in llm.calls[0])
    assert "比较元件处标注为“”" not in prompt_text  # guard against malformed quote stripping
    assert "比较元件处标注为\"-\"表示哪种反馈方式" in prompt_text or "比较元件处标注为“-”表示哪种反馈方式" in prompt_text
    assert "用户选择：B" in prompt_text
    assert "正确答案：A" in prompt_text
    assert "负反馈" in prompt_text
    assert "把反馈极性反过来了" in result["wrong_question_explanations"][0]["explanation"]


def test_wrong_question_explainer_outputs_card_ready_structured_explanation_parts():
    llm = FakeLLM(
        '{"explanations":[{"question_id":"Q1","wrong_reason":"concept_confusion","target_objective":"判断比较点负号对应的反馈极性","misconception":"把负号理解成正反馈","why_user_wrong":"你选择 B，是把比较点处反馈量相减的关系误认为反馈量相加。","why_correct":"正确答案 A 成立，因为负号表示反馈信号从给定输入中扣除，形成负反馈偏差信号。","key_rule":"看比较点符号时，先判断反馈量是相加还是相减，再判断反馈极性。","review_action":"回看比较点与偏差信号的节点说明，再做 1 道反馈极性变式题。","explanation":"比较点的减号表示反馈信号要从给定输入中相减，因此是负反馈。","wrong_option_analysis":{"B":"正反馈对应相加关系，不符合题干负号。"},"recommended_review":{"suggestion":"复习比较点负号与负反馈的关系"}}]}'
    )
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_wrong_question_explainer_node(runtime, llm=llm)

    result = node({"node_quiz_wrong_items": [WRONG_ITEM], "node_quiz_score": 0})

    prompt_text = "\n".join(str(m.content) for m in llm.calls[0])
    assert "why_user_wrong" in prompt_text
    assert "why_correct" in prompt_text
    assert "key_rule" in prompt_text
    assert "review_action" in prompt_text
    explanation = result["wrong_question_explanations"][0]
    assert explanation["why_user_wrong"].startswith("你选择 B")
    assert explanation["why_correct"].startswith("正确答案 A")
    assert "比较点符号" in explanation["key_rule"]
    assert "反馈极性变式题" in explanation["review_action"]
    history_content = result["message_history"][-1]["content"]
    assert "你错在：" in history_content
    assert "正确理解：" in history_content
    assert "判断依据：" in history_content
    assert "下一步：" in history_content


def test_fallback_variant_is_not_original_wrong_question_copy_and_hides_generation_meta_text():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_variant_question_generator_node(runtime)

    result = node(
        {
            "current_node_id": "KM001",
            "current_node_name": "自动控制系统示例",
            "graph_must_know": ["负反馈通过比较给定值与反馈量形成偏差信号"],
            "graph_common_errors": ["把比较点的减号误解为输出为负"],
            "node_quiz_wrong_items": [WRONG_ITEM],
        }
    )

    variant = result["variant_questions"][0]
    visible_text = _visible_variant_text(variant)
    assert variant["stem"] != WRONG_ITEM["stem"]
    assert variant["options"] != WRONG_ITEM["options"]
    assert "把比较点的减号误解为输出为负" in visible_text
    for forbidden in FORBIDDEN_VISIBLE_VARIANT_META_TEXT:
        assert forbidden not in visible_text
    assert variant["source"] == "contextual_fallback_variant"


def test_variant_generator_uses_llm_to_create_natural_questions_from_wrong_answer_context():
    llm = FakeLLM(
        '{"questions":[{"question_id":"V-Q1","stem":"在恒温箱控制中，传感器测得温度高于设定值时，控制器应如何利用反馈信号？","options":{"A":"减小加热功率，使偏差趋于减小","B":"继续增大加热功率，让温度更快上升","C":"只记录传感器读数，不参与控制","D":"把设定温度改成当前温度"},"answer_key":"A","explanation":"测量值高于设定值时，负反馈应促使执行环节降低加热，使输出回到设定附近。"}]}'
    )
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_variant_question_generator_node(runtime, llm=llm)

    result = node(
        {
            "current_node_id": "KM001",
            "current_node_name": "自动控制系统示例",
            "node_content_context": "本节点要求理解自动控制系统中的给定量、反馈量、比较点与偏差信号。",
            "graph_must_know": ["负反馈通过比较给定值与反馈量形成偏差信号"],
            "graph_common_errors": ["把比较点的减号误解为输出为负"],
            "node_quiz_wrong_items": [WRONG_ITEM],
        }
    )

    assert len(llm.calls) == 1
    prompt_text = "\n".join(str(m.content) for m in llm.calls[0])
    assert "原题题干" in prompt_text
    assert "用户选择：B" in prompt_text
    assert "正确答案：A" in prompt_text
    assert "可以重新设计应用场景" in prompt_text
    assert "不要把这些生成策略写进题干或选项" in prompt_text
    variant = result["variant_questions"][0]
    visible_text = _visible_variant_text(variant)
    assert "恒温箱控制" in visible_text
    assert variant["answer_key"] == "A"
    for forbidden in FORBIDDEN_VISIBLE_VARIANT_META_TEXT:
        assert forbidden not in visible_text


def test_variant_generator_repairs_low_quality_llm_variant_before_fallback():
    bad_response = """
    {"questions":[{"question_id":"V-BAD","stem":"变式验证：换成另一个场景后，抓住关键关系判断反馈极性。","options":{"A":"沿用原错因选择正反馈","B":"负反馈","C":"在新情境中仍能判断","D":"换成另一个说法"},"answer_key":"B","explanation":"bad"}]}
    """
    repair_response = """
    {"questions":[{"question_id":"V-REPAIR","stem":"在恒温箱控制中，比较点标注为负号时，反馈信号应如何进入比较环节？","options":{"A":"与给定量相加，使偏差增大","B":"从给定量中相减，形成负反馈偏差信号","C":"绕过比较点直接驱动执行机构","D":"只记录温度，不参与控制器输入"},"answer_key":"B","explanation":"负号表示反馈量在比较点与给定量相减。"}]}
    """
    llm = SequenceLLM([bad_response, repair_response])
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_variant_question_generator_node(runtime, llm=llm)

    result = node(
        {
            "current_node_id": "KM001",
            "current_node_name": "自动控制系统示例",
            "node_content_context": "比较点的负号表示反馈量从给定输入中相减。",
            "graph_must_know": ["负反馈通过比较给定值与反馈量形成偏差信号"],
            "graph_common_errors": ["把比较点的减号误解为输出为负"],
            "node_quiz_wrong_items": [WRONG_ITEM],
        }
    )

    assert len(llm.calls) == 2
    assert "上一轮被拒绝" in llm.calls[1][1].content
    variant = result["variant_questions"][0]
    assert variant["question_id"] == "V-REPAIR"
    assert variant["source"] == "ai_generated_variant"
    assert variant["answer_key"] == "B"
    visible_text = _visible_variant_text(variant)
    for forbidden in FORBIDDEN_VISIBLE_VARIANT_META_TEXT:
        assert forbidden not in visible_text
