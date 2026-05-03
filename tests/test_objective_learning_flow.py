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
    assert result["node_quiz_items"][1]["answer_key"] == "B"
    assert result["flow_status"] == "awaiting_objective_answers"
    assert result["learning_resume_target"] == "objective_test_scorer"
    assert result["pending_interaction_kind"] == "objective_test_answers"


def test_objective_test_generator_falls_back_when_no_bank_and_ai_fails():
    sink = BufferedEventSink()
    llm = FakeLLM("not json")
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm)

    result = node({"current_node_id": "KM001", "current_node_name": "稳定性"})

    assert len(llm.calls) == 1
    assert len(result["node_quiz_items"]) == 10
    assert result["node_quiz_items"][0]["source"] == "contextual_fallback"
    assert result["flow_status"] == "awaiting_objective_answers"


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
    assert event.data["review"]["questions"] == items
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


def test_fallback_objective_questions_are_contextualized_by_current_node_fields():
    """LLM 失败时也不应退回截图里的泛化占位题，应至少用节点字段生成可用的临时题。"""
    sink = BufferedEventSink()
    llm = FakeLLM("not json")
    runtime = RuntimeContext(event_sink=sink)
    node = build_objective_test_generator_node(runtime, llm=llm, count=3)

    result = node({
        "current_node_id": "KM-AUTO-SYS-EXAMPLE",
        "current_node_name": "自动控制系统示例",
        "graph_learning_objectives": ["能识别水箱液位控制中的反馈闭环"],
        "graph_must_know": ["给定值与测量值比较形成偏差", "控制器依据偏差产生控制作用"],
        "graph_common_errors": ["只看到执行机构而忽略测量反馈"],
        "node_content_context": "水箱液位自动控制中，液位传感器测量实际液位，与给定液位比较得到偏差。",
    })

    stems = [item["stem"] for item in result["node_quiz_items"]]
    options_text = "\n".join("\n".join(item["options"].values()) for item in result["node_quiz_items"])
    assert all("第 " not in stem or "核心判断" not in stem for stem in stems)
    assert "给定值与测量值比较形成偏差" in options_text
    assert "只看到执行机构而忽略测量反馈" in options_text
    assert {item["source"] for item in result["node_quiz_items"]} == {"contextual_fallback"}


def test_objective_generator_rejects_low_quality_ai_questions_and_uses_stronger_contextual_fallback():
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

    result = node({
        "current_node_id": "KM-AUTO-SYS-EXAMPLE",
        "current_node_name": "自动控制系统示例",
        "graph_learning_objectives": ["能根据函数记录仪方框图判断自动控制系统的闭环组成"],
        "graph_must_know": [
            "比较元件把输入量与测量反馈量比较并形成偏差信号",
            "前向通路与主反馈通路共同构成主回路",
        ],
        "graph_common_errors": [
            "只看到输出记录动作，忽略测量元件把输出量反馈到输入端",
            "把扰动当成有用输入，未区分二者对被控量的作用",
        ],
        "node_content_context": "一个典型反馈控制系统中，比较元件将输入量与测量元件检测到的被控量比较；负号表示负反馈；信号从输入端到输出端的通路称前向通路，输出经测量元件反馈到输入端的通路称主反馈通路。",
    })

    assert [item["source"] for item in result["node_quiz_items"]] == ["contextual_fallback", "contextual_fallback"]
    for item in result["node_quiz_items"]:
        option_values = list(item["options"].values())
        assert all("符合本节点" not in option for option in option_values)
        assert all("围绕“" not in option for option in option_values)
        assert all("结论方向和节点要点相反" not in option for option in option_values)
        assert all(len(option) <= 95 for option in option_values)
        assert len(set(option_values)) == 4
        assert item["answer_key"] in item["options"]
    all_text = "\n".join(item["stem"] + "\n" + "\n".join(item["options"].values()) for item in result["node_quiz_items"])
    assert "比较元件" in all_text
    assert "主反馈通路" in all_text
    assert "只看到输出记录动作" in all_text


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
