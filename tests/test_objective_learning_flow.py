from langchain_core.messages import AIMessage

from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.objective_test import (
    build_objective_test_generator_node,
    build_objective_test_scorer_node,
)
from ai_tutor_agent.nodes.post_lesson_choice import build_post_lesson_choice_node
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeAnswerProvider:
    def __init__(self, answer: str):
        self.answer = answer
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append({"prompt": prompt, "state": state})
        return self.answer


class FakeQuestionBank:
    def __init__(self):
        self.objective_calls = []
        self.variant_calls = []

    def get_objective_questions(self, node_id: str, k: int = 10):
        self.objective_calls.append({"node_id": node_id, "k": k})
        return [
            {
                "question_id": f"Q-{i}",
                "node_id": node_id,
                "stem": f"题目{i}",
                "options": {"A": "对", "B": "错"},
                "answer_key": "A" if i <= 8 else "B",
                "explanation": f"解析{i}",
                "wrong_option_analysis": {"A": "", "B": f"错因{i}"},
            }
            for i in range(1, k + 1)
        ]

    def get_variant_question(self, wrong_item: dict):
        self.variant_calls.append(wrong_item)
        return {
            "question_id": f"V-{wrong_item['question_id']}",
            "node_id": wrong_item.get("node_id", ""),
            "stem": "变式题",
            "options": {"A": "对", "B": "错"},
            "answer_key": "A",
            "explanation": "变式解析",
        }


class FakeLLM:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return AIMessage(content=self.content)


class SequenceLLM:
    def __init__(self, contents):
        self.contents = list(contents)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        index = min(len(self.calls) - 1, len(self.contents) - 1)
        return AIMessage(content=self.contents[index])


AI_OBJECTIVE_JSON = """
{
  "questions": [
    {"question_id": "AI-Q1", "stem": "概念题1", "options": {"A": "正确", "B": "错误", "C": "无关", "D": "相反"}, "answer_key": "A", "explanation": "解析1"},
    {"question_id": "AI-Q2", "stem": "概念题2", "options": {"A": "错误", "B": "正确", "C": "无关", "D": "相反"}, "answer_key": "B", "explanation": "解析2"}
  ]
}
"""


class StubStudentStateStore:
    def __init__(self):
        self.updated = []

    def load(self, student_id: str):
        from ai_tutor_agent.knowledge_map.student_state import StudentState

        state = StudentState(student_id=student_id)
        state.current_node_id = "KM001"
        return state

    def save(self, state):
        self.updated.append(state.to_dict())


def test_post_lesson_choice_pauses_and_can_route_to_objective_test():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("开始测试")
    node = build_post_lesson_choice_node(sink, provider)

    first = node({"current_node_id": "KM001", "current_node_name": "稳定性"})
    assert first["flow_status"] == "awaiting_post_lesson_choice"
    assert first["learning_phase"] == "post_lesson_choice"
    assert first["pending_interaction_kind"] == "post_lesson_choice"

    resumed = node(
        {
            "flow_status": "awaiting_post_lesson_choice",
            "pending_interaction_answer": "开始测试",
            "pending_interaction_options": first["pending_interaction_options"],
            "current_node_id": "KM001",
            "current_node_name": "稳定性",
        }
    )
    assert resumed["post_lesson_choice"] == "start_test"
    assert resumed["learning_resume_target"] == "objective_test_generator"


def test_post_lesson_direct_question_routes_to_temporary_question_channel():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("")
    node = build_post_lesson_choice_node(sink, provider)

    resumed = node(
        {
            "flow_status": "awaiting_post_lesson_choice",
            "pending_interaction_answer": "为什么稳定系统也会出现振荡？",
            "current_node_id": "KM001",
            "current_node_name": "稳定性",
        }
    )

    assert resumed["post_lesson_choice"] == "temporary_question"
    assert resumed["interrupt_query"] == "为什么稳定系统也会出现振荡？"
    assert resumed["learning_resume_target"] == "temporary_question_collector"
    assert resumed["learning_phase"] == "temporary_question_collecting"
    assert resumed["message_history"][-1]["data"]["selected_value"] == "temporary_question"
    assert resumed["message_history"][-1]["data"]["direct_question"] is True


def test_post_lesson_choice_accepts_freeform_hesitation_as_temporary_question():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("")
    node = build_post_lesson_choice_node(sink, provider)

    resumed = node(
        {
            "flow_status": "awaiting_post_lesson_choice",
            "pending_interaction_answer": "还是没太明白这个负反馈判断",
            "current_node_id": "KM001",
            "current_node_name": "稳定性",
        }
    )

    assert resumed["post_lesson_choice"] == "temporary_question"
    assert resumed["interrupt_query"] == "还是没太明白这个负反馈判断"
    assert resumed["learning_resume_target"] == "temporary_question_collector"
    assert resumed["learning_phase"] == "temporary_question_collecting"


def test_post_lesson_choice_prompt_is_not_binary_or_rigid():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("")
    node = build_post_lesson_choice_node(sink, provider)

    result = node({"current_node_name": "稳定性"})

    assert result["flow_status"] == "awaiting_post_lesson_choice"
    prompt = result["pending_interaction_prompt"]
    assert "还有临时问题，还是开始测试" not in prompt
    assert "可以直接追问" in prompt
    assert "一句话说卡点" in prompt
    assert "进入小测" in prompt
    labels = [item["label"] for item in result["pending_interaction_options"]]
    assert labels == ["继续追问", "我懂了，进入小测"]


def test_objective_test_generator_uses_ai_to_create_objective_questions_without_question_bank():
    sink = BufferedEventSink()
    llm = FakeLLM(AI_OBJECTIVE_JSON)
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm)

    result = node({"current_node_id": "KM001", "current_node_name": "稳定性", "teaching_content": "稳定性表示系统扰动后能回到平衡状态。"})

    assert len(llm.calls) == 1
    assert len(result["node_quiz_items"]) == 2
    assert result["node_quiz_items"][0]["source"] == "ai_generated"
    assert result["node_quiz_items"][0]["answer_key"] == "A"
    assert result["node_quiz_items"][0]["assessment_focus"]
    assert result["node_quiz_items"][0]["target_objective"]
    assert result["node_quiz_items"][0]["misconception"]
    assert 1 <= result["node_quiz_items"][0]["difficulty"] <= 5
    assert result["node_quiz_items"][1]["answer_key"] == "B"
    assert result["flow_status"] == "awaiting_objective_answers"
    assert result["learning_resume_target"] == "objective_test_scorer"
    assert result["pending_interaction_kind"] == "objective_test_answers"


def test_objective_test_generator_raises_when_no_bank_and_ai_fails():
    """题库和 AI 都失败时应抛出 RuntimeError，不再用硬编码兜底。"""
    sink = BufferedEventSink()
    llm = FakeLLM("not json")
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm)

    import pytest
    with pytest.raises(RuntimeError, match="出题失败"):
        node({"current_node_id": "KM001", "current_node_name": "稳定性"})

    assert len(llm.calls) == 1


def test_fallback_removed_raises_error_for_ten_questions():
    """题库和 AI 都失败时抛出 RuntimeError。"""
    sink = BufferedEventSink()
    llm = FakeLLM("not json")
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm, count=10)

    import pytest
    with pytest.raises(RuntimeError, match="出题失败"):
        node({"current_node_id": "KM001", "current_node_name": "自动控制系统示例"})


def test_fallback_removed_raises_error_for_long_node_fields():
    """题库和 AI 都失败时抛出 RuntimeError。"""
    sink = BufferedEventSink()
    llm = FakeLLM("not json")
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm, count=2)

    import pytest
    with pytest.raises(RuntimeError, match="出题失败"):
        node({
            "current_node_id": "KM-LONG",
            "current_node_name": "自动控制系统示例",
            "graph_learning_objectives": ["长文本目标"],
        })


def test_fallback_removed_raises_error_instead_of_generic_templates():
    """题库和 AI 都失败时抛出 RuntimeError。"""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_generator_node(runtime, llm=FakeLLM("not json"), count=3)

    import pytest
    with pytest.raises(RuntimeError, match="出题失败"):
        node({
            "current_node_id": "KM003",
            "current_node_name": "自动控制系统示例",
            "graph_must_know": ["测量输出并送回输入端参与比较"],
            "graph_common_errors": ["只看到执行机构而忽略测量反馈"],
        })
        assert "正确理解" in explanation
        assert "易错点" in explanation
        assert item.get("target_objective")
        assert item.get("misconception")


def test_ai_question_metadata_replaces_generic_or_raw_textbook_objectives():
    ai_json = """
    {
      "questions": [
        {
          "question_id": "AI-Q1",
          "stem": "在恒温箱温度控制中，哪一项说明反馈参与了控制？",
          "options": {
            "A": "测量实际温度，并与设定温度比较后调节加热功率",
            "B": "只按固定功率加热，不测量实际温度",
            "C": "只记录室外温度，不改变控制动作",
            "D": "把设定温度直接改成当前温度"
          },
          "answer_key": "A",
          "target_objective": "反馈控制系统是由各种结构不同的元部件组成的。从完成自动控制这一功能来看，一个系统必然包含被控对象和控制装置两大部分。",
          "misconception": "一般概念",
          "explanation": "反馈控制要把输出测量结果送回比较环节。"
        }
      ]
    }
    """
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_generator_node(runtime, llm=FakeLLM(ai_json), count=1)

    result = node(
        {
            "current_node_id": "KM003",
            "current_node_name": "自动控制系统示例",
            "graph_must_know": ["测量输出并送回输入端参与比较"],
            "graph_common_errors": ["只看到执行机构而忽略测量反馈"],
        }
    )

    item = result["node_quiz_items"][0]
    assert item["target_objective"] == "测量输出并送回输入端参与比较"
    assert item["misconception"] == "只看到执行机构而忽略测量反馈"
    assert "反馈控制系统是由各种结构不同的元部件组成" not in item["target_objective"]
    assert item["misconception"] != "一般概念"


def test_objective_test_scorer_scores_deterministically_and_generates_variants_for_wrong_items():
    sink = BufferedEventSink()
    question_bank = FakeQuestionBank()
    store = StubStudentStateStore()
    runtime = RuntimeContext(event_sink=sink, student_state_store=store)
    runtime.question_bank_provider = question_bank
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    items = question_bank.get_objective_questions("KM001", 10)

    result = node(
        {
            "student_id": "student_a",
            "current_node_id": "KM001",
            "node_quiz_items": items,
            "node_quiz_answers": {f"Q-{i}": "A" for i in range(1, 11)},
        }
    )

    assert result["node_quiz_score"] == 80
    assert result["score"] == 80
    assert result["current_node_status"] == "passed"
    assert result["learning_resume_target"] == "next_node_planner"
    assert result["node_quiz_wrong_items"][0]["question_id"] == "Q-9"
    assert result["node_quiz_wrong_items"][0]["target_objective"]
    assert result["node_quiz_wrong_items"][0]["misconception"]
    assert len(result["node_quiz_wrong_items"]) == 2
    assert result["student_state_snapshot"]["visited_nodes"] == ["KM001"]


def test_objective_test_scorer_failing_score_routes_to_explicit_remediation_nodes():
    question_bank = FakeQuestionBank()
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    runtime.question_bank_provider = question_bank
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    items = question_bank.get_objective_questions("KM001", 10)

    result = node(
        {
            "student_id": "student_a",
            "current_node_id": "KM001",
            "node_quiz_items": items,
            "node_quiz_answers": {f"Q-{i}": "B" for i in range(1, 11)},
        }
    )

    assert result["node_quiz_score"] == 20
    assert result["current_node_status"] == "quizzing"
    assert result["learning_phase"] == "node_quiz_remediation"
    assert result["learning_resume_target"] == "wrong_question_explainer"
    assert len(result["node_quiz_wrong_items"]) == 8
    assert result["variant_questions"] == []
    assert result["pending_interaction_kind"] == ""
    assert result["message_history"][-1]["kind"] == "objective_quiz_review"
    assert result["message_history"][-1]["data"]["kind"] == "objective_test_answers"
    event = runtime.event_sink.events[-1]
    assert event.source == "objective_test_scorer"
    assert event.data["review"]["kind"] == "objective_test_answers"
    assert event.data["review"]["review_state"] == "graded"
    assert event.data["review"]["locked"] is True
    assert event.data["review"]["node_id"] == "KM001"
    assert event.data["review"]["pass_score"] == 80
    assert event.data["review"]["question_count"] == 10
    assert event.data["review"]["correct_count"] == 2
    assert event.data["review"]["wrong_count"] == 8
    assert event.data["review"]["questions"][0]["question_id"] == items[0]["question_id"]
    assert event.data["review"]["questions"][0]["target_objective"]
    assert event.data["review"]["questions"][0]["locked"] is True
    assert "chosen_answer" in event.data["review"]["questions"][0]
    assert "is_correct" in event.data["review"]["questions"][0]
    assert "客观测评批改" in event.data["review_content"]


def test_ai_generated_objective_questions_are_scored_by_embedded_answer_key_not_llm():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    items = [
        {"question_id": "AI-Q1", "stem": "题1", "options": {"A": "对", "B": "错"}, "answer_key": "A", "source": "ai_generated"},
        {"question_id": "AI-Q2", "stem": "题2", "options": {"A": "对", "B": "错"}, "answer_key": "B", "source": "ai_generated"},
    ]

    result = node({"current_node_id": "KM001", "node_quiz_items": items, "pending_interaction_answer": "A B"})

    assert result["node_quiz_score"] == 100
    assert result["current_node_status"] == "passed"
    assert result["learning_resume_target"] == "next_node_planner"


def test_objective_test_scorer_second_variant_round_can_pass_and_reach_post_eval():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    variant_items = [
        {"question_id": f"V-{i}", "node_id": "KM001", "stem": f"变式{i}", "options": {"A": "对", "B": "错"}, "answer_key": "A"}
        for i in range(1, 6)
    ]

    result = node(
        {
            "student_id": "student_a",
            "current_node_id": "KM001",
            "node_quiz_items": variant_items,
            "node_quiz_answers": {f"V-{i}": "A" for i in range(1, 6)},
            "learning_phase": "node_quiz_remediation",
        }
    )

    assert result["node_quiz_score"] == 100
    assert result["current_node_status"] == "passed"
    assert result["learning_resume_target"] == "next_node_planner"


def test_objective_scorer_uses_variant_quiz_kind_after_dialog_collected_answers():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    variant_items = [
        {"question_id": "V-Q1", "node_id": "KM001", "stem": "变式1", "options": {"A": "对", "B": "错"}, "answer_key": "A"}
    ]

    result = node(
        {
            "current_node_id": "KM001",
            "current_node_name": "自动控制系统示例",
            "node_quiz_items": variant_items,
            "node_quiz_answers": {"V-Q1": "A"},
            "node_quiz_kind": "variant_test_answers",
            "pending_interaction_kind": "",
        }
    )

    reviews = [item for item in result["message_history"] if item.get("kind") == "objective_quiz_review"]
    assert len(reviews) == 1
    assert reviews[0]["data"]["kind"] == "variant_test_answers"
    assert reviews[0]["data"]["title"] == "变式练习"
    assert reviews[0]["data"]["questions"][0]["locked"] is True
    assert result["pending_interaction_kind"] == ""


def test_scorer_accepts_json_dict_answers_from_frontend():
    """Frontend sends JSON string like '{"AI-Q1":"A","AI-Q2":"B"}' via pending_interaction_answer."""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    items = [
        {"question_id": "AI-Q1", "stem": "题1", "options": {"A": "对", "B": "错"}, "answer_key": "A", "source": "ai_generated"},
        {"question_id": "AI-Q2", "stem": "题2", "options": {"A": "对", "B": "错"}, "answer_key": "B", "source": "ai_generated"},
    ]

    result = node({"current_node_id": "KM001", "node_quiz_items": items, "pending_interaction_answer": '{"AI-Q1":"A","AI-Q2":"B"}'})

    assert result["node_quiz_score"] == 100
    assert result["current_node_status"] == "passed"
    assert result["learning_resume_target"] == "next_node_planner"


def test_ai_question_generator_uses_node_content_context():
    """AI question generation should use node_content_context (from node_content_loader) as source content."""
    sink = BufferedEventSink()
    llm = FakeLLM(AI_OBJECTIVE_JSON)
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm)

    result = node({
        "current_node_id": "KM001",
        "current_node_name": "稳定性",
        "node_content_context": "稳定性是自动控制系统的核心指标，用于衡量系统受扰动后能否回到平衡。",
    })

    assert len(llm.calls) == 1
    prompt_content = llm.calls[0][1].content
    assert "稳定性是自动控制系统" in prompt_content
    assert len(result["node_quiz_items"]) == 2


def test_ai_question_generator_includes_structured_current_node_fields_in_prompt():
    """客观题生成应显式输入当前节点字段，而不是只给泛化主题和一段讲解文本。"""
    sink = BufferedEventSink()
    llm = FakeLLM(AI_OBJECTIVE_JSON)
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm)

    node({
        "current_node_id": "KM-AUTO-SYS-EXAMPLE",
        "current_node_name": "自动控制系统示例",
        "node_content_context": "自动控制系统示例强调被控对象、测量、比较、控制器、执行机构和反馈通道如何构成闭环。",
        "graph_learning_objectives": ["能识别水箱液位控制中的反馈闭环", "能区分开环示例与闭环控制示例"],
        "graph_must_know": ["给定值与测量值比较形成偏差", "控制器依据偏差产生控制作用"],
        "graph_common_errors": ["把人工观察后的手动调节误认为自动反馈", "只看到执行机构而忽略测量反馈"],
        "graph_prerequisites": ["反馈控制基本概念"],
        "graph_neighbors": ["开环控制", "闭环控制"],
        "graph_target_mastery_level": "应用",
        "graph_difficulty": "基础",
    })

    prompt_content = llm.calls[0][1].content
    assert "学习目标：能识别水箱液位控制中的反馈闭环；能区分开环示例与闭环控制示例" in prompt_content
    assert "必会要点：给定值与测量值比较形成偏差；控制器依据偏差产生控制作用" in prompt_content
    assert "常见误区：把人工观察后的手动调节误认为自动反馈；只看到执行机构而忽略测量反馈" in prompt_content
    assert "前置节点：反馈控制基本概念" in prompt_content
    assert "相邻/对照节点：开环控制；闭环控制" in prompt_content
    assert "禁止生成“第 1 个核心判断”这类占位题" in prompt_content


def test_fallback_removed_raises_error_with_node_context():
    """LLM 失败时抛出 RuntimeError，不再用节点字段拼凑兆底题。"""
    sink = BufferedEventSink()
    llm = FakeLLM("not json")
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm, count=3)

    import pytest
    with pytest.raises(RuntimeError, match="出题失败"):
        node({
            "current_node_id": "KM-AUTO-SYS-EXAMPLE",
            "current_node_name": "自动控制系统示例",
            "graph_learning_objectives": ["能识别水箱液位控制中的反馈闭环"],
            "graph_must_know": ["给定值与测量值比较形成偏差"],
            "graph_common_errors": ["只看到执行机构而忽略测量反馈"],
        })


def test_objective_generator_rejects_low_quality_ai_questions_and_raises():
    low_quality_json = """
    {
      "questions": [
        {
          "question_id": "AI-BAD-1",
          "stem": "在“自动控制系统示例”中，哪一项最能体现本节点要求掌握的“实例”？",
          "options": {
            "A": "符合本节点：实例",
            "B": "只看表面动作，忽略本节点给出的关键条件或反馈关系",
            "C": "把“自动控制系统示例”与相邻概念混同，未说明“实例”的作用条件",
            "D": "认为“实例”与本节点无关，结论方向和节点要点相反"
          },
          "answer_key": "A",
          "explanation": "泛化解析"
        },
        {
          "question_id": "AI-BAD-2",
          "stem": "在“自动控制系统示例”中，哪一项最能体现本节点要求掌握的“自动控制”？",
          "options": {
            "A": "围绕“自动控制”判断：反馈控制系统是由各种结构不同的元部件组成的。从完成“自动控制”这一功能来看，一个系统必然包含被控对象和控制装置两大部分，而控制装置是由具有一定功能的各种基本元件组成的。在不同系统中，结构完全不同的元部件却可以具有相同的功能，因此，将组成系统的元部件按功能分类主要有以下几种：图1-5典型反馈控制系统方框图。通常加到反馈控制系统上的外作用有两种类型，一种是有用输入，一种是扰动。",
            "B": "只看表面动作，忽略本节点给出的关键条件或反馈关系",
            "C": "把“自动控制系统示例”与相邻概念混同，未说明“自动控制”的作用条件",
            "D": "认为“自动控制”与本节点无关，结论方向和节点要点相反"
          },
          "answer_key": "A",
          "explanation": "整段材料塞进选项"
        }
      ]
    }
    """
    sink = BufferedEventSink()
    llm = FakeLLM(low_quality_json)
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm, count=2)

    import pytest
    with pytest.raises(RuntimeError, match="出题失败"):
        node({
            "current_node_id": "KM-AUTO-SYS-EXAMPLE",
            "current_node_name": "自动控制系统示例",
            "graph_learning_objectives": ["能根据函数记录仪方框图判断自动控制系统的闭环组成"],
            "graph_must_know": ["比较元件把输入量与测量反馈量比较并形成偏差信号"],
            "graph_common_errors": ["只看到输出记录动作，忽略测量元件把输出量反馈到输入端"],
        })

def test_first_attempt_always_uses_full_count_not_reduced():
    """首次测验（非 node_retest）统一使用 count=10，不复用 2/5 缩减。"""
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink)
    from unittest.mock import MagicMock
    provider = MagicMock()
    provider.get_objective_questions.return_value = [
        {"stem": f"Q{i}", "options": {"A":"a","B":"b","C":"c","D":"d"}, "answer_key": "A"}
        for i in range(10)
    ]
    runtime.question_bank_provider = provider
    node = build_objective_test_generator_node(runtime, count=10)
    # quick_check 首次也应是 10 题
    result = node({"current_node_id": "KM001", "current_node_name": "测试", "node_quiz_kind": "quick_check"})
    assert len(result["node_quiz_items"]) == 10, f"quick_check 首次也应是 10 题, 实际 {len(result['node_quiz_items'])}"

def test_objective_generator_repairs_missing_ai_questions_before_fallback():
    first_response = """
    {
      "questions": [
        {
          "question_id": "AI-BAD-1",
          "stem": "在“自动控制系统示例”中，哪一项最能体现本节点要求掌握的“实例”？",
          "options": {
            "A": "符合本节点：实例",
            "B": "只看表面动作",
            "C": "与本节点无关",
            "D": "结论方向和节点要点相反"
          },
          "answer_key": "A"
        },
        {
          "question_id": "AI-GOOD-1",
          "stem": "在液位自动控制中，哪一项最能说明反馈已经参与控制？",
          "options": {
            "A": "只设置目标液位，不测量实际液位",
            "B": "测量实际液位，并与给定液位比较后调节阀门",
            "C": "人工观察液位后手动关阀",
            "D": "只按固定时间开关阀门"
          },
          "answer_key": "B",
          "target_objective": "识别液位控制中的反馈闭环",
          "misconception": "把手动调节误认为自动反馈",
          "explanation": "反馈控制必须把实际输出送回比较环节。"
        }
      ]
    }
    """
    repair_response = """
    {
      "questions": [
        {
          "question_id": "AI-REPAIR-1",
          "stem": "在温度自动控制中，哪一项最准确说明比较元件的作用？",
          "options": {
            "A": "把设定温度与测量温度比较，形成偏差信号",
            "B": "直接改变被控对象，不需要测量",
            "C": "只记录室外扰动，不参与控制器输入",
            "D": "把执行机构输出当成给定量"
          },
          "answer_key": "A",
          "target_objective": "说明比较元件如何形成偏差信号",
          "misconception": "忽略测量反馈参与比较",
          "explanation": "比较元件根据给定量和反馈量形成偏差。"
        },
        {
          "question_id": "AI-REPAIR-2",
          "stem": "判断一个转速系统是否为闭环控制，关键证据是什么？",
          "options": {
            "A": "控制器按固定程序输出",
            "B": "电机功率足够大",
            "C": "测量实际转速并送回与目标转速比较",
            "D": "存在外部负载扰动"
          },
          "answer_key": "C",
          "target_objective": "判断反馈信号是否参与比较",
          "misconception": "只看执行机构而忽略测量反馈",
          "explanation": "闭环控制的关键是输出测量回到输入比较环节。"
        }
      ]
    }
    """
    llm = SequenceLLM([first_response, repair_response])
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_generator_node(runtime, llm=llm, count=3)

    result = node({
        "current_node_id": "KM001",
        "current_node_name": "自动控制系统示例",
        "graph_learning_objectives": ["识别液位控制中的反馈闭环", "说明比较元件如何形成偏差信号"],
        "graph_common_errors": ["把手动调节误认为自动反馈", "忽略测量反馈参与比较"],
        "node_content_context": "液位传感器测量实际液位，与给定液位比较形成偏差后调节阀门。",
    })

    assert len(llm.calls) == 2
    assert [item["source"] for item in result["node_quiz_items"]] == ["ai_generated", "ai_generated", "ai_generated"]
    assert [item["question_id"] for item in result["node_quiz_items"]] == ["AI-GOOD-1", "AI-REPAIR-1", "AI-REPAIR-2"]
    assert "符合本节点" not in "\n".join(
        item["stem"] + "\n" + "\n".join(item["options"].values())
        for item in result["node_quiz_items"]
    )


def test_objective_generator_prompt_contains_blueprint_and_balanced_answer_keys():
    llm = FakeLLM(AI_OBJECTIVE_JSON)
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_generator_node(runtime, llm=llm, count=4)

    node({
        "current_node_id": "KM001",
        "current_node_name": "自动控制系统示例",
        "graph_learning_objectives": ["识别闭环结构"],
        "graph_must_know": ["反馈量与给定量比较形成偏差"],
        "graph_common_errors": ["只看执行机构而忽略测量反馈"],
    })

    prompt_content = llm.calls[0][1].content
    assert "【出题蓝图】" in prompt_content
    assert '"assessment_focus": "概念辨析"' in prompt_content
    assert '"answer_key": "A"' in prompt_content
    assert '"answer_key": "B"' in prompt_content
    assert '"answer_key": "C"' in prompt_content
    assert '"answer_key": "D"' in prompt_content


def test_objective_generator_uses_node_teaching_contract_for_coverage_plan():
    """教学契约的 assessment_targets 驱动出题蓝图和 AI prompt。"""
    valid_json = """
    {
      "questions": [
        {
          "question_id": "Q1", "stem": "稳定性定义题",
          "options": {"A":"a","B":"b","C":"c","D":"d"}, "answer_key": "A",
          "target_objective": "稳定性的定义", "assessment_focus": "概念辨析",
          "misconception": "把振荡都当成不稳定", "explanation": "解析"
        },
        {
          "question_id": "Q2", "stem": "有界输入输出题",
          "options": {"A":"a","B":"b","C":"c","D":"d"}, "answer_key": "B",
          "target_objective": "有界输入有界输出", "assessment_focus": "应用迁移",
          "misconception": "只看瞬时振荡", "explanation": "解析"
        },
        {
          "question_id": "Q3", "stem": "综合题",
          "options": {"A":"a","B":"b","C":"c","D":"d"}, "answer_key": "C",
          "explanation": "解析"
        }
      ]
    }
    """
    llm = FakeLLM(valid_json)
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_generator_node(runtime, llm=llm, count=3)

    result = node(
        {
            "current_node_id": "KM001",
            "current_node_name": "稳定性基础",
            "node_teaching_contract": {
                "node_id": "KM001",
                "node_name": "稳定性基础",
                "learning_goal": "判断系统响应是否收敛",
                "must_know": ["稳定性的定义", "有界输入有界输出"],
                "common_misconceptions": ["把振荡都当成不稳定"],
                "assessment_targets": [
                    {
                        "target_objective": "稳定性的定义",
                        "assessment_focus": "概念辨析",
                        "misconception": "把振荡都当成不稳定",
                        "required": True,
                    },
                    {
                        "target_objective": "有界输入有界输出",
                        "assessment_focus": "应用迁移",
                        "misconception": "只看瞬时振荡，不看最终是否有界",
                        "required": True,
                    },
                ],
                "exit_criteria": ["节点客观题总分达到 80 分", "关键目标正确率达到 70%"],
            },
        }
    )

    targets = [item.get("target_objective", "") for item in result["node_quiz_items"]]
    assert targets[:2] == ["稳定性的定义", "有界输入有界输出"]
    assert result["node_quiz_coverage_plan"][0]["target_objective"] == "稳定性的定义"
    assert result["node_quiz_coverage_plan"][0]["required"] is True
    prompt_content = llm.calls[0][1].content
    assert "节点教学契约" in prompt_content
    assert "退出条件：节点客观题总分达到 80 分；关键目标正确率达到 70%" in prompt_content


def test_objective_scorer_blocks_passing_when_required_contract_target_is_wrong():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_scorer_node(runtime, pass_score=80)
    items = [
        {
            "question_id": f"Q{i}",
            "stem": f"题{i}",
            "options": {"A": "对", "B": "错", "C": "干扰", "D": "干扰"},
            "answer_key": "A",
            "target_objective": "稳定性的定义" if i == 1 else "有界输入有界输出",
            "assessment_focus": "概念辨析",
            "misconception": "把振荡都当成不稳定",
        }
        for i in range(1, 6)
    ]

    result = node(
        {
            "current_node_id": "KM001",
            "current_node_name": "稳定性基础",
            "node_teaching_contract": {
                "assessment_targets": [
                    {"target_objective": "稳定性的定义", "required": True},
                    {"target_objective": "有界输入有界输出", "required": True},
                ]
            },
            "node_quiz_items": items,
            "node_quiz_answers": {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "A", "Q5": "A"},
        }
    )

    assert result["node_quiz_score"] == 80
    assert result["current_node_status"] == "quizzing"
    assert result["learning_resume_target"] == "wrong_question_explainer"
    assert result["objective_mastery_summary"]["required_failed_targets"] == ["稳定性的定义"]
    assert "关键目标未达标" in result["feedback"]


def test_workflow_routes_tutor_to_post_lesson_choice_and_objective_scorer_to_next_node_planner():
    assert workflow_module.route_after_tutor({"interrupt_query": ""}) == "post_lesson_choice"
    assert workflow_module.route_after_post_lesson_choice({"post_lesson_choice": "start_test"}) == "objective_test_generator"
    assert workflow_module.route_after_post_lesson_choice({"post_lesson_choice": "temporary_question"}) == "temporary_question_collector"
    assert workflow_module.route_after_objective_test_scorer({"current_node_status": "passed"}) == "next_node_planner"
    assert workflow_module.route_after_objective_test_scorer({"current_node_status": "quizzing", "flow_status": "awaiting_objective_answers"}) == "pause"


def test_post_lesson_choice_resets_stale_post_lesson_choice_on_first_run():
    """When returning from temporary Q&A, post_lesson_choice may still be
    'temporary_question' from the previous interaction.  The first-run path
    must reset it to '' so routing does not mis-fire."""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("")
    node = build_post_lesson_choice_node(sink, provider)

    # Simulate restoring a session where post_lesson_choice is stale
    first = node({
        "current_node_id": "KM001",
        "current_node_name": "稳定性",
        "post_lesson_choice": "temporary_question",  # stale from previous run
    })
    assert first["flow_status"] == "awaiting_post_lesson_choice"
    assert first["post_lesson_choice"] == "", "stale post_lesson_choice must be reset"

    # After reset, routing should NOT go to temporary_question_collector
    from ai_tutor_agent.orchestration import workflow as workflow_module
    routing_state = {"flow_status": "normal", "post_lesson_choice": first["post_lesson_choice"]}
    assert workflow_module.route_after_post_lesson_choice(routing_state) == "objective_test_generator"


def test_post_lesson_choice_start_test_routing_with_stale_state():
    """Full round-trip: stale temporary_question -> first run (reset) -> user
    answers start_test -> must route to objective_test_generator."""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("")
    node = build_post_lesson_choice_node(sink, provider)

    # First run with stale state
    first = node({
        "current_node_id": "KM001",
        "current_node_name": "稳定性",
        "post_lesson_choice": "temporary_question",
    })
    assert first["post_lesson_choice"] == ""

    # User answers "start_test"
    resumed = node({
        "flow_status": "awaiting_post_lesson_choice",
        "pending_interaction_answer": "start_test",
        "pending_interaction_options": first["pending_interaction_options"],
        "current_node_id": "KM001",
        "current_node_name": "稳定性",
        "post_lesson_choice": "",  # was reset
    })
    assert resumed["post_lesson_choice"] == "start_test"
    assert resumed["learning_resume_target"] == "objective_test_generator"
