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
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    assert "LLM 根据图谱上下文解释" in streamed


def test_interruption_preserves_debug_graph_rag_html_report_for_llm_graph_answers(tmp_path):
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
    assert tutor_llm.calls == [], "GraphRAG 已用 LLM 生成完整调试报告时，不应再由 tutor_llm 二次整理吞掉结构"
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    streamed = "".join(str(e.data.get("text", "")) for e in sink.events if e.type == "node.stream")
    assert "GraphRAG 调试报告" in streamed
    assert "相关公式与图表" in streamed
    assert "证据" in streamed
    assert "answer-media-block" in streamed
    assert "media-card figure-card" in streamed
    assert "media-card formula-card" in streamed
    assert "formula-math" in streamed
    assert streamed.count('<div class="answer-media-block">') == 1
    assert "式一 [KM015.formula_asset[1]]" not in streamed
    assert '<div class="formula-scroll formula-viewport answer-formula"' not in streamed
    assert "单位阶跃响应曲线</p><p>" not in streamed
    assert "KM013.figure_asset[1]" in streamed
    assert "KM015.summary" in streamed
    assert "不应该吞掉" not in streamed
    assert result["message_history"][-1]["kind"] == "graph_rag_debug_report"
    assert result["message_history"][-1]["data"]["graph_rag_result"]["media_items"]
