from pathlib import Path

from ai_tutor_agent.knowledge_map import debug_graph_rag


def _sample_result() -> dict:
    return {
        "plan": {},
        "anchor_nodes": [],
        "traversed_nodes": [],
        "question": "q",
        "answer": "结论：看式一。 [[MEDIA:KM001.formula_asset[1]]]",
        "evidence_items": [{"reference": "KM001.summary", "text": "依据摘要。"}],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "一阶系统",
                "text": r"c(t)=1-e^{-t/T}",
            }
        ],
    }


def test_debug_graph_rag_can_write_learning_html_separately_from_debug_report(tmp_path):
    result = _sample_result()
    debug_path = tmp_path / "debug.html"
    learning_path = tmp_path / "learning.html"

    written_debug = debug_graph_rag.write_html_report(result, str(debug_path))
    written_learning = debug_graph_rag.write_learning_html(result, str(learning_path))

    debug_html = Path(written_debug).read_text(encoding="utf-8")
    learning_html = Path(written_learning).read_text(encoding="utf-8")

    assert "GraphRAG 调试报告" in debug_html
    assert "answer-media-block" in debug_html
    assert "learning-answer-content" not in debug_html

    assert "learning-answer-content" in learning_html
    assert "learning-formula-card" in learning_html
    assert "learning-evidence-card" in learning_html
    assert "graph-rag-answer-panel" not in learning_html
    assert "answer-media-block" not in learning_html


def test_debug_graph_rag_cli_exposes_learning_html_option():
    args = debug_graph_rag.parse_args(["--once", "q", "--learning-html", "data/out.html"])

    assert args.once == "q"
    assert args.learning_html == "data/out.html"
