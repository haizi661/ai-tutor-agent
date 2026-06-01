from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.tutor import build_tutor_node


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


class FailingThenInvokeLLM:
    def __init__(self, invoke_response):
        self.invoke_response = invoke_response
        self.messages = []
        self.invoke_calls = 0

    def stream(self, messages):
        self.messages.append(messages)
        raise RuntimeError("incomplete chunked read")

    def invoke(self, messages):
        self.messages.append(messages)
        self.invoke_calls += 1
        return SimpleNamespace(content=self.invoke_response)


class DeadLLM:
    def stream(self, _messages):
        raise RuntimeError("stream down")

    def invoke(self, _messages):
        raise RuntimeError("invoke down")


class StubKnowledgeProvider:
    def query(self, query, *, rewrite_request=None):
        del rewrite_request
        del query
        return ""


def test_tutor_formats_json_payload_into_compact_teacher_prose():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住稳定性判断的核心：看系统最终会不会回到平衡点。",
          "steps": [
            "先分清稳定性问的是最终趋势，不是中间抖不抖。",
            "再看系统受到扰动后，输出会不会慢慢回到原来的平衡附近。",
            "最后不要把稳定性和响应快慢混在一起。"
          ],
          "example": "比如温控系统被你突然打开窗户后，如果温度最后还能重新回到设定值附近，我们才说它稳定。",
          "key_points": [
            "稳定性看的是最终是否回到平衡。",
            "响应快慢和超调大小属于瞬态性能，不等于稳定性。"
          ],
          "self_check": "如果一个系统晃了几下但最后回到原位，你会怎么判断它是否稳定？"
        }
        """
    )
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    content = result["tutor_content"]
    assert "先抓住稳定性判断的核心" in content
    assert "比如温控系统被你突然打开窗户后" in content
    assert "你先想一下" in content
    streamed = "".join(event.data.get("text", "") for event in sink.events if event.type == "node.stream")
    assert streamed == content


def test_tutor_fallback_keeps_plain_text_teacher_reply():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        "稳定性先看最终会不会回到平衡点。不要把它和瞬态性能混在一起。比如温控系统扰动后还能回到设定温度附近。核心要点：最终趋势比中间抖动更重要。"
    )
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    content = result["tutor_content"]
    assert content.startswith("稳定性先看最终会不会回到平衡点")
    assert "比如温控系统扰动后还能回到设定温度附近" in content


def test_tutor_passes_rewrite_request_to_knowledge_provider():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住主线。",
          "steps": ["第一步先看整体定义。", "第二步再看关键条件。"],
          "example": "可以先带入一个简单例子。",
          "key_points": ["核心点一", "核心点二"],
          "self_check": ""
        }
        """
    )

    captured = {}

    class CapturingKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            captured["query"] = query
            captured["rewrite_request"] = rewrite_request
            captured["include_debug"] = include_debug
            return {"context": "资料", "citations": []}

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=CapturingKnowledgeProvider()))
    node(
        {
            "current_topic": "控制系统中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 1,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert captured["query"] == "控制系统中的稳定性"
    assert captured["rewrite_request"].channel == "tutor"
    assert captured["rewrite_request"].current_topic == "控制系统中的稳定性"


def test_tutor_uses_current_user_goal_and_filters_uncited_lines():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        "### 先抓关键\n这是没有引用的句子。\n- 能确认的是系统会回到平衡点。[1]\n- 响应快慢不等于稳定性。[2]"
    )

    captured = {}

    class EvidenceKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            captured["query"] = query
            captured["raw_query"] = rewrite_request.raw_query if rewrite_request else ""
            del include_debug
            return {
                "context": "[证据1] guide.pdf\n稳定性看最终是否回到平衡点。",
                "citation_plan": [
                    {"rank": 1, "display_label": "guide.pdf · 第 1 页", "snippet": "稳定性看最终是否回到平衡点。", "filename": "guide.pdf", "page": 1, "source_type": "local_kb"},
                    {"rank": 2, "display_label": "guide.pdf · 第 2 页", "snippet": "响应快慢不等于稳定性。", "filename": "guide.pdf", "page": 2, "source_type": "local_kb"},
                ],
                "evidence": [],
                "needs_follow_up": False,
            }

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=EvidenceKnowledgeProvider()))
    result = node(
        {
            "current_topic": "控制系统中的稳定性",
            "current_user_goal": "稳定性怎么判断",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert captured["query"] == "控制系统中的稳定性 稳定性怎么判断"
    assert captured["raw_query"] == "稳定性怎么判断"
    assert "这是没有引用的句子" not in result["tutor_content"]
    assert "[1]" in result["tutor_content"]
    assert result["tutor_evidence"][0]["rank"] == 1


def test_tutor_respects_seeded_opening_strategy_on_first_round():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住主线。",
          "steps": ["第一步先看整体定义。", "第二步再看关键条件。"],
          "example": "可以先带入一个简单例子。",
          "key_points": ["核心点一", "核心点二"],
          "self_check": ""
        }
        """
    )

    captured = {}

    class CapturingKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            captured["strategy"] = rewrite_request.teaching_strategy if rewrite_request else ""
            del query, include_debug
            return {"context": "", "citations": []}

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=CapturingKnowledgeProvider()))
    node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "先用例子带我入门",
            "teaching_strategy": "analogy",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert captured["strategy"] == "analogy"


def test_tutor_builds_query_from_session_goal_and_turn_goal():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住主线。",
          "steps": ["第一步先看整体定义。", "第二步再看关键条件。"],
          "example": "可以先带入一个简单例子。",
          "key_points": ["核心点一", "核心点二"],
          "self_check": ""
        }
        """
    )

    captured = {}

    class CapturingKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            captured["query"] = query
            captured["raw_query"] = rewrite_request.raw_query if rewrite_request else ""
            del include_debug
            return {"context": "", "citations": []}

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=CapturingKnowledgeProvider()))
    result = node(
        {
            "current_topic": "控制原理",
            "current_user_goal": "有哪些核心概念",
            "session_goal": "先搭一个入门框架",
            "turn_goal": "先搞懂传递函数和框图",
            "topic_focus": "传递函数和框图",
            "topic_background": "零基础入门",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert captured["raw_query"] == "先搞懂传递函数和框图"
    assert captured["query"] == "控制原理 先搞懂传递函数和框图 有哪些核心概念 先搭一个入门框架"
    assert result["turn_goal"] == "先搞懂传递函数和框图"
    final_prompt = llm.messages[-1][-1].content
    assert "当前会话目标：【先搭一个入门框架】" in final_prompt
    assert "当前这一轮先抓：【先搞懂传递函数和框图】" in final_prompt
    assert "用户当前状态：【零基础入门】" in final_prompt


def test_tutor_falls_back_to_starter_option_when_goal_is_still_broad():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住主线。",
          "steps": ["第一步先看整体定义。", "第二步再看关键条件。"],
          "example": "可以先带入一个简单例子。",
          "key_points": ["核心点一", "核心点二"],
          "self_check": ""
        }
        """
    )

    captured = {}

    class CapturingKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            captured["query"] = query
            captured["raw_query"] = rewrite_request.raw_query if rewrite_request else ""
            del include_debug
            return {"context": "", "citations": []}

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=CapturingKnowledgeProvider()))
    result = node(
        {
            "current_topic": "控制原理",
            "current_user_goal": "控制原理",
            "session_goal": "控制原理",
            "turn_goal": "",
            "topic_focus": "",
            "topic_starter_options": ["先搭传递函数和框图这条主线", "先搞懂稳定性到底在看什么"],
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert captured["raw_query"] == "先搭传递函数和框图这条主线"
    assert captured["query"] == "控制原理 先搭传递函数和框图这条主线"
    assert result["current_user_goal"] == "先搭传递函数和框图这条主线"
    assert result["turn_goal"] == "先搭传递函数和框图这条主线"


def test_tutor_uses_current_turn_graph_anchor_for_prompt_and_progress():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住反馈最关键的作用。",
          "steps": ["先看输出信息是怎么回送到输入端的。", "再看它为什么会改变系统整体行为。"],
          "example": "可以先把温控系统的回路看成一个最直观的反馈例子。",
          "key_points": ["反馈会把输出信息重新送回输入侧。", "不要把反馈和控制器本身混在一起。"],
          "self_check": ""
        }
        """
    )

    class GraphAwareKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            del query, rewrite_request, include_debug
            return {
                "context": "",
                "citations": [],
                "graph_context": {
                    "anchor_id": "feedback-loop",
                    "anchor_title": "反馈",
                    "anchor_filename": "feedback.md",
                    "prerequisites": ["系统"],
                    "neighbors": ["负反馈"],
                    "learning_objectives": ["说明反馈如何影响系统行为"],
                    "must_know": ["反馈把输出信息重新送回输入端"],
                    "common_errors": ["把反馈结构和控制器本身混为一谈"],
                    "target_mastery_level": "应用层",
                    "difficulty": "3",
                    "next_steps": [{"target": "负反馈", "relation": "neighbor"}],
                },
            }

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=GraphAwareKnowledgeProvider()))
    result = node(
        {
            "current_topic": "控制原理",
            "current_user_goal": "先搞懂反馈",
            "graph_anchor_title": "系统",
            "user_knowledge_graph": {"系统": {"status": "mastered", "turn_count": 2}},
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert result["graph_anchor_title"] == "反馈"
    assert result["user_knowledge_graph"]["反馈"]["status"] == "in_progress"
    current_event = next(
        event
        for event in sink.events
        if event.type == "graph.node_update" and event.data.get("type") == "current"
    )
    assert current_event.data["title"] == "反馈"
    assert current_event.data["id"] == "feedback-loop"
    system_prompt = llm.messages[-1][0].content
    assert "当前知识节点：反馈" in system_prompt
    assert "图谱 ID: feedback-loop" in system_prompt
    assert "该节点连接的下游概念：负反馈" in system_prompt


def test_tutor_preserves_marker_lines_after_citation_filter_and_advances_graph_anchor():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        "反馈会把输出信息重新送回输入侧。[1]\n[MASTERY_ACHIEVED: feedback-loop]\n[→ 下一概念: 负反馈 | negative-feedback]"
    )

    class MarkerKnowledgeProvider:
        def query_with_sources(self, query, *, rewrite_request=None, include_debug=False):
            del query, rewrite_request, include_debug
            return {
                "context": "[证据1] feedback.md\n反馈会把输出信息重新送回输入侧。",
                "citation_plan": [
                    {
                        "rank": 1,
                        "display_label": "feedback.md · 第 1 页",
                        "snippet": "反馈会把输出信息重新送回输入侧。",
                        "filename": "feedback.md",
                        "page": 1,
                        "source_type": "local_kb",
                    }
                ],
                "graph_context": {
                    "anchor_id": "feedback-loop",
                    "anchor_title": "反馈",
                    "anchor_filename": "feedback.md",
                    "prerequisites": ["系统"],
                    "neighbors": ["负反馈"],
                    "learning_objectives": ["说明反馈会如何改变系统行为"],
                    "must_know": ["反馈把输出信息送回输入端"],
                    "common_errors": ["把反馈和误差消除简单画等号"],
                    "target_mastery_level": "理解层",
                    "difficulty": "3",
                    "next_steps": [{"target": "负反馈", "relation": "neighbor"}],
                },
                "needs_follow_up": False,
            }

        def resolve_graph_context(self, query):
            if query == "negative-feedback":
                return {
                    "anchor_id": "negative-feedback",
                    "anchor_title": "负反馈",
                    "anchor_filename": "negative-feedback.md",
                    "prerequisites": ["反馈"],
                    "neighbors": ["正反馈"],
                    "learning_objectives": ["区分负反馈与正反馈的典型效果"],
                    "must_know": ["负反馈通常提升稳态精度并改善抗扰动能力"],
                    "common_errors": ["把负反馈简单理解成信号取负号"],
                    "target_mastery_level": "应用层",
                    "difficulty": "3",
                    "next_steps": [{"target": "正反馈", "relation": "neighbor"}],
                }
            return {}

    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=MarkerKnowledgeProvider()))
    result = node(
        {
            "current_topic": "控制原理",
            "current_user_goal": "反馈和负反馈什么关系",
            "user_knowledge_graph": {"反馈": {"status": "in_progress", "turn_count": 5}},
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert result["tutor_content"].strip().endswith("[1]")
    assert result["user_knowledge_graph"]["反馈"]["status"] == "mastered"
    assert result["graph_anchor_id"] == "negative-feedback"
    assert result["graph_anchor_title"] == "负反馈"
    assert result["turn_goal"] == "负反馈"
    graph_events = [event for event in sink.events if event.type == "graph.node_update"]
    assert any(event.data.get("title") == "反馈" and event.data.get("status") == "mastered" for event in graph_events)
    assert any(event.data.get("title") == "负反馈" and event.data.get("status") == "upcoming" for event in graph_events)


def test_tutor_outputs_node_content_context_directly_without_graph_search_or_llm_rewrite():
    """主流程有 node_content_context 时，会调 LLM 生成个性化讲解。

    8ab6927: 图谱搜索和知识库仍会被尝试调用以补充证据，但讲解主体来自 LLM。
    如果 LLM 失败，回退到直接输出预置内容。
    """
    sink = BufferedEventSink()
    llm = FakeStreamingLLM("LLM 基于参考材料生成的个性化讲解。")

    class StubGraphPipeline:
        def __init__(self):
            self.node_map = {}
            self.edges = []
        def ask(self, query, *, traversal_mode=None):
            return None

    class StubKnowledgeProvider:
        def query(self, query, *, rewrite_request=None):
            return ""

    node = build_tutor_node(
        llm,
        RuntimeContext(
            event_sink=sink,
            knowledge_provider=StubKnowledgeProvider(),
            graph_rag_pipeline=StubGraphPipeline(),
        ),
    )
    teacher_explanation = "【预置教师讲解】稳定性基础只讲 explanation_teacher_style 字段。"

    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "学习稳定性",
            "current_node_id": "stability",
            "current_node_name": "稳定性",
            "graph_anchor_id": "stability",
            "graph_anchor_title": "稳定性",
            "node_content_context": teacher_explanation,
            "tutor_citations": [],
            "tutor_evidence": [],
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    # LLM 被调用了（一次调用，包含 system + human 两条消息）
    assert len(llm.messages) == 1
    assert len(llm.messages[0]) == 2
    # 输出是 LLM 生成的内容
    assert "个性化讲解" in result["tutor_content"]


def test_tutor_prompt_uses_node_teaching_contract_and_requires_detailed_node_lesson():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        "稳定性要看系统受扰动后的最终趋势，而不是只看中间有没有振荡。比如温控系统开窗后还能回到设定温度附近，就是稳定性的直观判断。"
    )
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "学习稳定性",
            "current_node_id": "stability",
            "current_node_name": "稳定性",
            "graph_anchor_id": "stability",
            "graph_anchor_title": "稳定性",
            "node_content_context": "【预置教师讲解】稳定性基础说明系统受扰动后响应是否保持有界或回到平衡。",
            "node_teaching_contract": {
                "learning_goal": "判断系统响应是否收敛",
                "must_know": ["稳定性的定义", "有界输入有界输出"],
                "common_misconceptions": ["把振荡都当成不稳定"],
                "worked_example": "温控系统开窗后温度能回到设定值附近。",
                "assessment_targets": [
                    {"target_objective": "稳定性的定义", "misconception": "把振荡都当成不稳定", "required": True}
                ],
                "exit_criteria": ["节点客观题总分达到 80 分", "关键目标正确率达到 70%"],
            },
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    system_prompt = llm.messages[0][0].content
    human_prompt = llm.messages[0][1].content
    joined_prompt = system_prompt + "\n" + human_prompt
    assert "【节点教学契约】" in joined_prompt
    assert "学习目标：判断系统响应是否收敛" in joined_prompt
    assert "必会要点：稳定性的定义；有界输入有界输出" in joined_prompt
    assert "常见误区：把振荡都当成不稳定" in joined_prompt
    assert "退出条件：节点客观题总分达到 80 分；关键目标正确率达到 70%" in joined_prompt
    assert "#### 1. 学习目标" in joined_prompt
    assert "#### 2. 核心概念" in joined_prompt
    assert "#### 3. 公式讲解" in joined_prompt
    assert "#### 4. 图表说明" in joined_prompt
    assert "#### 5. 具体例子" in joined_prompt
    assert "#### 6. 常见误区与边界" in joined_prompt
    assert "#### 7. 自检问题" in joined_prompt
    assert "不得省略任何小节" in joined_prompt


def test_tutor_expands_too_brief_node_lesson_with_contract_fallback():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM("稳定性就是最终能稳定。")
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "学习稳定性",
            "current_node_id": "stability",
            "current_node_name": "稳定性",
            "graph_anchor_id": "stability",
            "graph_anchor_title": "稳定性",
            "node_content_context": "稳定性基础说明系统受扰动后响应是否保持有界或回到平衡。",
            "node_teaching_contract": {
                "learning_goal": "判断系统响应是否收敛",
                "must_know": ["稳定性的定义", "有界输入有界输出"],
                "common_misconceptions": ["把振荡都当成不稳定"],
                "worked_example": "温控系统开窗后温度能回到设定值附近。",
                "assessment_targets": [
                    {"target_objective": "稳定性的定义", "misconception": "把振荡都当成不稳定", "required": True}
                ],
                "exit_criteria": ["节点客观题总分达到 80 分", "关键目标正确率达到 70%"],
            },
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    content = result["tutor_content"]
    assert len(content) > 120
    assert "判断系统响应是否收敛" in content
    assert "稳定性的定义" in content
    assert "有界输入有界输出" in content
    assert "把振荡都当成不稳定" in content
    assert "温控系统开窗后温度能回到设定值附近" in content


def test_tutor_retries_with_invoke_when_stream_breaks():
    sink = BufferedEventSink()
    llm = FailingThenInvokeLLM("稳定性先看最终会不会回到平衡点。不要把它和响应快慢混在一起。")
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert llm.invoke_calls == 1
    assert "稳定性先看最终会不会回到平衡点" in result["tutor_content"]
    assert result["llm_stream_disabled"] is True
    assert result["llm_stream_failures"] == 1
    assert not [event for event in sink.events if event.type == "session.warning"]


def test_tutor_uses_local_fallback_when_stream_and_invoke_both_fail():
    sink = BufferedEventSink()
    node = build_tutor_node(DeadLLM(), RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "current_user_goal": "先理解稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    assert "这一轮先抓【先理解稳定性】最关键的判断" in result["tutor_content"]
    assert result["llm_stream_disabled"] is True
    assert result["llm_stream_failures"] == 1
    assert not [event for event in sink.events if event.type == "session.warning"]


def test_tutor_skips_stream_after_session_marked_unstable():
    sink = BufferedEventSink()
    llm = FailingThenInvokeLLM("后续直接非流式回答。")
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
            "llm_stream_disabled": True,
            "llm_stream_failures": 1,
        }
    )

    assert llm.invoke_calls == 1
    assert len(llm.messages) == 1
    assert result["llm_stream_disabled"] is True
    assert result["llm_stream_failures"] == 1
