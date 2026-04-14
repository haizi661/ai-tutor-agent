from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.tester import build_tester_node


class FakeStreamingLLM:
    def __init__(self, responses):
        if isinstance(responses, str):
            responses = [responses]
        self.responses = list(responses)
        self.messages = []

    def stream(self, messages):
        self.messages.append(messages)
        response = self.responses.pop(0)
        yield SimpleNamespace(content=response)


class FakeAnswerProvider:
    def __init__(self, answers):
        if isinstance(answers, str):
            answers = [answers]
        self.answers = list(answers)
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append({"prompt": prompt, "state": state})
        return self.answers.pop(0)


def _warning_messages(sink):
    return [event for event in sink.events if event.type == "session.warning"]


def test_tester_selects_concept_distinction_for_boundary_confusion():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把稳定性和瞬态性能分清",
  "question": "请分别解释稳定性和瞬态性能，并指出二者最关键的区别。",
  "requirements": ["先分别给出定义", "再说明区别", "最后补一句为什么不能混为一谈"],
  "hint": "先想系统最后状态，再想中间过程。"
}"""
    )
    answer_provider = FakeAnswerProvider("稳定性关注最终状态，瞬态性能关注响应过程。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "控制理论",
            "tutor_content": "本轮讲解聚焦稳定性与瞬态性能。",
            "difficulty_level": 3,
            "attempt_count": 1,
            "coach_content": "先把两个概念分开说。",
            "misconceptions": ["把稳定性和瞬态性能混淆了"],
            "feedback": "你现在主要是把两个概念混在了一起。",
        }
    )

    assert result["tester_question_type"] == "概念辨析题"
    assert result["tester_question_template"] == "定义辨析"
    assert "### 这次题型\n概念辨析题 · 定义辨析" in result["tester_question"]
    assert "本轮题型已确定：概念辨析题" in tester_llm.messages[0][1].content
    assert "本轮子模板已确定：定义辨析" in tester_llm.messages[0][1].content


def test_tester_selects_counterexample_distinction_for_error_statement_round():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能识别一个常见说法为什么不成立",
  "question": "有人说“只要系统响应很快，它就一定稳定”。请判断这句话是否成立，并指出它错在哪里。",
  "requirements": ["先判断正误", "再指出错因", "最后给出更准确的表述"],
  "hint": "先分清响应快慢和最终是否回到平衡点是不是一回事。"
}"""
    )
    answer_provider = FakeAnswerProvider("这句话不成立，因为快不代表最终稳定。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "控制理论",
            "tutor_content": "讲解了稳定性边界和常见误区。",
            "difficulty_level": 4,
            "attempt_count": 1,
            "coach_content": "你现在主要卡在常见误区上。",
            "misconceptions": ["把响应快误当成稳定"],
            "feedback": "这是一个典型误区，这个说法并不成立。",
        }
    )

    assert result["tester_question_type"] == "概念辨析题"
    assert result["tester_question_template"] == "反例辨析"
    assert "概念辨析题 · 反例辨析" in result["tester_question"]
    assert "本轮子模板已确定：反例辨析" in tester_llm.messages[0][1].content


def test_tester_selects_calculation_analysis_for_quantitative_topics():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把条件、公式和步骤串起来",
  "question": "已知一个二阶系统阻尼比为 0.5，请结合超调量关系说明应该如何估计响应特征，并给出你的分析过程。",
  "requirements": ["先列出关键关系", "再说明分析步骤", "最后给出结论"],
  "hint": "先从阻尼比和超调量的关系入手。"
}"""
    )
    answer_provider = FakeAnswerProvider("我会先写出阻尼比和超调量的关系。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "二阶系统分析",
            "tutor_content": "已讲解阻尼比、超调量和 Mp=e^(-πζ/sqrt(1-ζ^2)) 之间的关系。",
            "difficulty_level": 4,
            "attempt_count": 0,
            "teaching_strategy": "stepbystep",
            "coach_content": "",
        }
    )

    assert result["tester_question_type"] == "计算分析题"
    assert result["tester_question_template"] == "带数值的计算分析"
    assert "### 这次题型\n计算分析题 · 带数值的计算分析" in result["tester_question"]
    assert "本轮题型已确定：计算分析题" in tester_llm.messages[0][1].content
    assert "本轮子模板已确定：带数值的计算分析" in tester_llm.messages[0][1].content


def test_tester_selects_relation_derivation_analysis_without_explicit_numbers():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把变量关系和趋势说清楚",
  "question": "请说明阻尼比变化时，系统超调量会呈现什么趋势，并解释背后的关系。",
  "requirements": ["先写关键关系", "再说明趋势", "最后给出结论"],
  "hint": "先想阻尼比变大时系统振荡会怎样变化。"
}"""
    )
    answer_provider = FakeAnswerProvider("阻尼比变大时，超调量通常会减小。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "二阶系统分析",
            "tutor_content": "讲解了阻尼比与超调量的关系，以及为什么二者会呈现此消彼长。",
            "difficulty_level": 4,
            "attempt_count": 0,
            "coach_content": "",
        }
    )

    assert result["tester_question_type"] == "计算分析题"
    assert result["tester_question_template"] == "关系推导分析"
    assert "计算分析题 · 关系推导分析" in result["tester_question"]
    assert "本轮子模板已确定：关系推导分析" in tester_llm.messages[0][1].content


def test_tester_defaults_to_scenario_judgment_for_application_round():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把判断标准放进实际场景里",
  "question": "某个闭环系统受到扰动后会先振荡几次，但振幅逐渐减小并最终回到平衡点。请判断它是否稳定，并说明依据。",
  "requirements": ["先给出判断", "再说明依据", "最后补一句你会优先观察哪个信号"],
  "hint": "先看系统最终会不会回到平衡点。"
}"""
    )
    answer_provider = FakeAnswerProvider("我会先看系统最终能不能回到平衡点。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "闭环稳定性判断",
            "tutor_content": "讲解了如何根据系统受到扰动后的最终状态判断稳定性。",
            "difficulty_level": 3,
            "attempt_count": 0,
            "coach_content": "",
        }
    )

    assert result["tester_question_type"] == "场景判断题"
    assert result["tester_question_template"] == "工程场景判断"
    assert "### 这次题型\n场景判断题 · 工程场景判断" in result["tester_question"]
    assert "本轮题型已确定：场景判断题" in tester_llm.messages[0][1].content
    assert "本轮子模板已确定：工程场景判断" in tester_llm.messages[0][1].content


def test_tester_selects_strategy_selection_judgment_for_tradeoff_topics():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能在多种方案间做出取舍",
  "question": "一个高并发接口既担心数据库压力，又担心缓存一致性。你会优先选旁路缓存还是写穿策略？请说明理由。",
  "requirements": ["先明确选择", "再说明理由", "最后补一句为什么另一种方案不更合适"],
  "hint": "先想你最怕的瓶颈和最不能接受的代价是什么。"
}"""
    )
    answer_provider = FakeAnswerProvider("我会先看数据库压力和一致性要求，再选方案。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "缓存策略选择",
            "tutor_content": "讲解了旁路缓存和写穿策略的适用场景与取舍。",
            "difficulty_level": 3,
            "attempt_count": 0,
            "coach_content": "",
        }
    )

    assert result["tester_question_type"] == "场景判断题"
    assert result["tester_question_template"] == "方案选择判断"
    assert "场景判断题 · 方案选择判断" in result["tester_question"]
    assert "本轮子模板已确定：方案选择判断" in tester_llm.messages[0][1].content


def test_tester_resume_keeps_existing_question_type_and_normalizes_heading():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM([])
    answer_provider = FakeAnswerProvider("稳定性关注系统最终状态。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "控制理论",
            "tester_question": "### 题目\n请解释稳定性，并说明你的判断依据。",
            "tester_question_type": "概念辨析题",
            "tester_question_template": "定义辨析",
            "difficulty_level": 3,
            "resume_tester": True,
        }
    )

    assert result["tester_question_type"] == "概念辨析题"
    assert result["tester_question_template"] == "定义辨析"
    assert result["tester_question"].startswith("### 这次题型\n概念辨析题 · 定义辨析")
    assert tester_llm.messages == []


def test_tester_same_type_mode_reuses_last_passed_template():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "继续看你能不能把稳定性和瞬态性能分清",
  "question": "请再换一个角度说明稳定性和瞬态性能的区别，并补一句为什么二者不能混为一谈。",
  "requirements": ["先说稳定性", "再说瞬态性能", "最后补一句关键区别"],
  "hint": "先想最终状态，再想中间过程。"
}"""
    )
    answer_provider = FakeAnswerProvider("稳定性看最终状态，瞬态性能看过程表现。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "控制理论",
            "tutor_content": "本轮讲解聚焦稳定性与瞬态性能。",
            "difficulty_level": 3,
            "attempt_count": 0,
            "practice_generation_mode": "same_type",
            "tester_question_type": "概念辨析题",
            "tester_question_template": "定义辨析",
        }
    )

    assert result["tester_question_type"] == "概念辨析题"
    assert result["tester_question_template"] == "定义辨析"
    assert "沿用你刚才已经通过的题型" in tester_llm.messages[0][1].content
    assert result["practice_generation_mode"] == ""


def test_tester_guardrails_rewrite_double_prompt_questions():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把稳定性和瞬态性能分清",
  "question": "请解释稳定性是什么？它和瞬态性能有什么区别？另外再举个例子说明。",
  "requirements": ["先解释稳定性", "再说区别", "最后举例"],
  "hint": "先分清最终状态和过程表现。"
}"""
    )
    answer_provider = FakeAnswerProvider("稳定性关注最终状态。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "控制理论",
            "tutor_content": "本轮讲解聚焦稳定性与瞬态性能。",
            "difficulty_level": 3,
            "attempt_count": 1,
            "coach_content": "先把两个概念分开说。",
            "misconceptions": ["把稳定性和瞬态性能混淆了"],
            "feedback": "你现在主要是把两个概念混在了一起。",
        }
    )

    assert "请先说清题目里的核心概念，再指出它和一个容易混淆概念的关键区别" in result["tester_question"]
    assert _warning_messages(sink)


def test_tester_guardrails_rewrite_overly_broad_questions():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把判断标准放进实际场景里",
  "question": "请结合本节内容谈谈你的理解和感受。",
  "requirements": ["自由发挥即可", "想到什么写什么", "不限角度"],
  "hint": "先回想本节内容。"
}"""
    )
    answer_provider = FakeAnswerProvider("我会先看系统最终会不会回到平衡点。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "闭环稳定性判断",
            "tutor_content": "讲解了如何根据系统受到扰动后的最终状态判断稳定性。",
            "difficulty_level": 3,
            "attempt_count": 0,
            "coach_content": "",
        }
    )

    assert "请结合一个具体工程场景做出判断，并说明你是抓住了哪个关键信号或条件才这样判断的。" in result["tester_question"]
    assert _warning_messages(sink)


def test_tester_guardrails_rewrite_numeric_questions_with_missing_conditions():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把条件、公式和步骤串起来",
  "question": "请计算这个系统的结果，并说明你的分析过程。",
  "requirements": ["先算", "再说明", "最后给结论"],
  "hint": "先想公式。"
}"""
    )
    answer_provider = FakeAnswerProvider("我会先列公式。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "二阶系统分析",
            "tutor_content": "已讲解阻尼比、超调量和 Mp=e^(-πζ/sqrt(1-ζ^2)) 之间的关系。",
            "difficulty_level": 4,
            "attempt_count": 0,
            "teaching_strategy": "stepbystep",
            "coach_content": "",
        }
    )

    assert "请根据题目给出的数值条件，写出关键关系或公式，完成必要的计算，并给出最终结论。" in result["tester_question"]
    assert _warning_messages(sink)


def test_tester_injects_graph_objectives_and_common_errors_into_prompt():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        """{
  "focus": "看你能不能把反馈的核心作用说清楚",
  "question": "请解释反馈在控制系统里的核心作用，并指出一个容易混淆的错误理解。",
  "requirements": ["先说核心作用", "再指出误区", "最后补一句为什么会混淆"],
  "hint": "先想输出回到输入以后，系统为什么更容易修正偏差。"
}"""
    )
    answer_provider = FakeAnswerProvider("反馈能帮助系统修正偏差。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    tester_node(
        {
            "current_topic": "反馈",
            "tutor_content": "本轮讲了反馈如何把输出信息回送到输入端，并改善系统表现。",
            "difficulty_level": 3,
            "attempt_count": 0,
            "graph_learning_objectives": ["能解释反馈的作用"],
            "graph_common_errors": ["把反馈和闭环画法混为一谈"],
            "graph_must_know": ["输出回到输入形成比较"],
            "coach_content": "",
        }
    )

    human_content = tester_llm.messages[0][1].content
    assert "该节点学习目标：能解释反馈的作用" in human_content
    assert "该节点常见误区：把反馈和闭环画法混为一谈" in human_content
    assert "该节点必会点：输出回到输入形成比较" in human_content
