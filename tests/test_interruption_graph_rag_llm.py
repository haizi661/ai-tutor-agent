from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.interruption import build_interruption_node


class FakeTutorLLM:
    def __init__(self, text="LLM polished answer"):
        self.text = text
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return self.text

    def stream(self, messages):
        self.calls.append(messages)
        yield self.text


class FakeGraphRAGPipeline:
    def __init__(self):
        self.calls = []

    def ask(self, question, **kwargs):
        self.calls.append((question, kwargs))
        return {
            "answer": "模板式 fallback answer from graph pipeline",
            "context_text": "图谱检索上下文：比较元件的减号表示反馈信号与输入相减，是负反馈判据。",
            "media_items": [],
            "plan": {"used_llm": False},
        }


class FakeDebugGraphRAGPipeline:
    def __init__(self, figure_path: str = ""):
        self.calls = []
        self.figure_path = figure_path

    def ask(self, question, **kwargs):
        self.calls.append((question, kwargs))
        return {
            "question": question,
            "answer": (
                "结论：超调量随阻尼比增大而减小。\n"
                "式一 [KM015.formula_asset[1]]\n"
                "二阶系统的时域分析\n"
                "$$\n"
                r"\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%"
                "\n$$\n"
                "图一 [KM013.figure_asset[1]]\n"
                "系统时间响应的性能指标\n"
                "单位阶跃响应曲线"
            ),
            "context_text": "二阶系统时域分析上下文",
            "evidence_items": [
                {"reference": "KM015.summary", "text": "二阶系统动态过程及典型性能指标。"},
            ],
            "media_items": [
                {
                    "reference": "KM013.figure_asset[1]",
                    "display_label": "图一",
                    "asset_type": "figure",
                    "node_name": "系统时间响应的性能指标",
                    "caption": "单位阶跃响应曲线",
                    "image_paths_abs": [self.figure_path] if self.figure_path else [],
                },
                {
                    "reference": "KM015.formula_asset[1]",
                    "display_label": "式一",
                    "asset_type": "formula",
                    "node_name": "二阶系统的时域分析",
                    "text": r"\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%",
                },
            ],
            "plan": {"used_llm": True},
        }


class FakeFallbackGraphRAGPipelineWithMedia:
    def __init__(self):
        self.calls = []

    def ask(self, question, **kwargs):
        self.calls.append((question, kwargs))
        return {
            "question": question,
            "answer": "式一 [KM015.formula_asset[1]]\n$$\n\\sigma\\%=e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times100\\%\n$$",
            "context_text": "二阶系统超调量公式用于说明阻尼比越大，超调越小。",
            "evidence_items": [{"reference": "KM015.formula", "text": "二阶系统超调量公式。"}],
            "media_items": [
                {
                    "reference": "KM015.formula_asset[1]",
                    "display_label": "式一",
                    "asset_type": "formula",
                    "node_name": "二阶系统的时域分析",
                    "text": "\\sigma\\%=e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times100\\%",
                },
            ],
            "plan": {"used_llm": False},
        }


class NoopKnowledgeProvider:
    def query(self, *args, **kwargs):
        return ""


def test_interruption_polishes_graph_rag_context_with_tutor_llm_when_graph_answer_is_fallback():
    tutor_llm = FakeTutorLLM("LLM 根据图谱上下文解释：减号表示反馈量被减去，所以这是负反馈。")
    graph = FakeGraphRAGPipeline()
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, knowledge_provider=NoopKnowledgeProvider(), graph_rag_pipeline=graph)
    node = build_interruption_node(tutor_llm, runtime)

    result = node(
        {
            "current_topic": "自动控制系统示例",
            "interrupt_query": "比较元件处的减号是什么意思？",
            "learning_resume_target": "temporary_question_collector",
        }
    )

    assert graph.calls
    assert tutor_llm.calls, "临时问答拿到 GraphRAG fallback 检索结果后仍应调用主 tutor LLM 组织答案"
    prompt_text = "\n".join(str(m.content) for m in tutor_llm.calls[0])
    assert "图谱检索上下文" in prompt_text
    assert "模板式 fallback answer" in prompt_text
    assert "短问短答" in prompt_text
    assert "追问" in prompt_text
    assert "不要机械套固定的“结论 -> 分析 -> 举例 -> 拓展 -> 依据”模板" in prompt_text
    assert "[[MEDIA:媒体reference]]" in prompt_text
    assert "不要输出裸数字引用" in prompt_text
    assert "不要引入图谱结果中没有出现的节点编号" in prompt_text
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    assert result["pending_interaction_kind"] == "post_lesson_choice"
    assert result["pending_interaction_recommended"] == "start_test"
    assert "可以继续追问" in result["pending_interaction_prompt"]
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    assert "LLM 根据图谱上下文解释" in streamed


def test_interruption_keeps_media_cards_after_polishing_graph_fallback_answer():
    tutor_llm = FakeTutorLLM("LLM 润色后解释：阻尼比越大，指数项越小，所以超调量越小。")
    graph = FakeFallbackGraphRAGPipelineWithMedia()
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, knowledge_provider=NoopKnowledgeProvider(), graph_rag_pipeline=graph)
    node = build_interruption_node(tutor_llm, runtime)

    result = node(
        {
            "current_topic": "二阶系统时域分析",
            "interrupt_query": "为什么阻尼比越大超调越小？",
            "learning_resume_target": "temporary_question_collector",
        }
    )

    assert tutor_llm.calls
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    assert "LLM 润色后解释" in streamed
    assert "learning-answer-content" in streamed
    assert "graph-rag-answer-panel" not in streamed
    assert "answer-media-block" not in streamed
    assert "media-card" not in streamed
    assert "learning-formula-card" in streamed
    assert "learning-media-group" in streamed
    assert "formula-render" in streamed
    assert result["message_history"][-1]["kind"] == "graph_rag_answer"


def test_interruption_dedupes_polished_formula_payload_after_media_marker():
    tutor_llm = FakeTutorLLM(
        "分析：阻尼比越大，指数衰减越明显。 [[MEDIA:KM015.formula_asset[1]]]\n"
        "$$\n"
        "\\sigma\\%=e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times100\\%\n"
        "$$"
    )
    graph = FakeFallbackGraphRAGPipelineWithMedia()
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, knowledge_provider=NoopKnowledgeProvider(), graph_rag_pipeline=graph)
    node = build_interruption_node(tutor_llm, runtime)

    result = node(
        {
            "current_topic": "二阶系统时域分析",
            "interrupt_query": "为什么阻尼比越大超调越小？",
            "learning_resume_target": "temporary_question_collector",
        }
    )

    prompt_text = "\n".join(str(m.content) for m in tutor_llm.calls[0])
    assert "不要再抄写同一个公式源码" in prompt_text
    assert result["message_history"][-1]["kind"] == "graph_rag_answer"
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    assert streamed.count("learning-formula-card") == 1
    assert "learning-inline-formula-card" not in streamed
    assert "$$" not in streamed


def test_interruption_preserves_graph_rag_media_answer_for_llm_graph_answers(tmp_path):
    image_path = tmp_path / "figure.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    tutor_llm = FakeTutorLLM("不应该吞掉 debug_graph_rag 结构")
    graph = FakeDebugGraphRAGPipeline(str(image_path))
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, knowledge_provider=NoopKnowledgeProvider(), graph_rag_pipeline=graph)
    node = build_interruption_node(tutor_llm, runtime)

    result = node(
        {
            "current_topic": "二阶系统时域分析",
            "interrupt_query": "二阶系统的超调量、调节时间和阻尼比之间有什么关系？",
            "learning_resume_target": "temporary_question_collector",
        }
    )

    assert graph.calls
    assert tutor_llm.calls == [], "GraphRAG 已用 LLM 生成完整媒体回答时，不应再由 tutor_llm 二次整理吞掉结构"
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    stream_kinds = [e.data.get("kind") for e in sink.events if e.type == "node.stream"]
    assert stream_kinds == ["graph_rag_answer"]
    assert "learning-answer-content" in streamed
    assert "graph-rag-answer-panel" not in streamed
    assert "相关公式与图表" not in streamed
    assert "参考依据" in streamed
    assert "learning-evidence-card--source" in streamed
    assert "KM015.summary" not in streamed.split("<details", 1)[0]
    assert "查看来源详情" not in streamed
    assert "answer-media-block" not in streamed
    assert "media-card" not in streamed
    assert "learning-figure-card" in streamed
    assert "learning-formula-card" in streamed
    assert "formula-math" in streamed
    assert streamed.count('learning-media-group') == 1
    assert "式一 [KM015.formula_asset[1]]" not in streamed
    assert '<div class="formula-scroll formula-viewport answer-formula"' not in streamed
    assert "单位阶跃响应曲线</p><p>" not in streamed
    assert any(
        item.get("reference") == "KM013.figure_asset[1]"
        for item in result["message_history"][-1]["data"]["graph_rag_result"]["media_items"]
    )
    assert "不应该吞掉" not in streamed
    assert result["message_history"][-1]["kind"] == "graph_rag_answer"
    assert result["message_history"][-1]["data"]["graph_rag_result"]["media_items"]


class FakeProblematicTemporaryGraphRAGPipeline:
    def __init__(self, figure_path: str = ""):
        self.calls = []
        self.figure_path = figure_path

    def ask(self, question, **kwargs):
        self.calls.append((question, kwargs))
        return {
            "question": question,
            "answer": (
                "结论：自动控制原理是研究反馈控制系统的学问。\n\n"
                "分析：知识图谱中\n4\n明确指出反馈控制，而\n6\n阐明常见控制方式。"
                "从图1-8可以看到输入信号与反馈信号比较。\n\n"
                "// 图1-8 函数记录仪原理示意图\n\n"
                "相关公式与图表\n图表\n图一 · 图 1-8 函数记录仪原理示意图\n放大\n复制引用\n"
                "图 1-8 函数记录仪原理示意图\n来源：自动控制系统示例\n查看来源详情\n\n"
                "拓展：后续可看[KM012.summary]和[KM026.summary]。\n\n"
                "依据：\n1. \n1\n 通过典型实例理解自动控制系统的构成和工作过程。"
            ),
            "context_text": "自动控制系统示例上下文",
            "evidence_items": [
                {"reference": "KM003.summary", "node_id": "KM003", "node_name": "自动控制系统示例", "text": "通过典型实例理解自动控制系统的构成和工作过程。"},
                {"reference": "KM006.summary", "node_id": "KM006", "node_name": "自动控制的基本原理与方式", "text": "说明自动控制实现的基本机制与常见控制方式。"},
            ],
            "media_items": [
                {
                    "reference": "KM003.figure_asset[1]",
                    "display_label": "图一",
                    "asset_type": "figure",
                    "node_name": "自动控制系统示例",
                    "caption": "图 1-8 函数记录仪原理示意图",
                    "image_paths_abs": [self.figure_path] if self.figure_path else [],
                }
            ],
            "plan": {"used_llm": True},
        }


def test_temporary_graph_rag_answer_strips_report_artifacts_and_debug_details(tmp_path):
    image_path = tmp_path / "figure.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    tutor_llm = FakeTutorLLM("不应该二次调用")
    graph = FakeProblematicTemporaryGraphRAGPipeline(str(image_path))
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, knowledge_provider=NoopKnowledgeProvider(), graph_rag_pipeline=graph)
    node = build_interruption_node(tutor_llm, runtime)

    result = node(
        {
            "current_topic": "自动控制原理",
            "interrupt_query": "自动控制原理到底是什么？",
            "learning_resume_target": "temporary_question_collector",
        }
    )

    assert tutor_llm.calls == []
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    visible_text = streamed.split("<details", 1)[0]
    assert "// 图" not in streamed
    assert "相关公式与图表" not in streamed
    assert "查看来源详情" not in streamed
    assert "参考依据" in streamed
    assert "learning-evidence-card--source" in streamed
    assert "[KM012.summary]" not in visible_text
    assert "[KM026.summary]" not in visible_text
    assert "KM012.summary" not in visible_text
    assert "KM026.summary" not in visible_text
    assert "\n4\n" not in streamed
    assert "\n6\n" not in streamed
    assert "依据：" not in streamed
    assert streamed.count("learning-figure-card") == 1
    assert streamed.count("图 1-8 函数记录仪原理示意图") <= 2
