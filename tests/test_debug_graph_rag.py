from pathlib import Path

from ai_tutor_agent.knowledge_map.debug_graph_rag import (
    _render_answer_html,
    build_html_report,
    write_html_report,
)


def test_build_html_report_contains_modal_markup():
    result = {
        "question": "二阶系统有什么典型公式和图表？",
        "answer": "结论：可以结合式1与图1理解。",
        "evidence_items": [
            {
                "reference": "KM014.summary",
                "text": "这是摘要。",
            }
        ],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM014.formula_asset[1]",
                "display_label": "式1",
                "node_name": "一阶系统的时域分析",
                "text": "c(t)=1-e^{-t/T}",
            },
            {
                "asset_type": "figure",
                "reference": "KM014.figure_asset[1]",
                "display_label": "图1",
                "node_name": "一阶系统的时域分析",
                "caption": "图3-3 单位阶跃响应曲线",
                "image_paths_abs": [str(Path("tests/sample.png").resolve())],
            },
        ],
    }

    html_text = build_html_report(result)

    assert "openModal" in html_text
    assert "mathjax@3/es5/tex-svg.js" in html_text
    assert "formula-math" in html_text
    assert "KM014.formula_asset[1]" in html_text
    assert "图3-3 单位阶跃响应曲线" in html_text
    assert "相关公式与图表" in html_text
    assert "式1" in html_text
    assert "图1" in html_text
    assert "document.body" in html_text


def test_write_html_report_creates_file():
    result = {
        "question": "q",
        "answer": "a",
        "evidence_items": [],
        "media_items": [],
    }

    output_path = Path("data/test_outputs/debug_graph_rag_report_test.html")
    output = write_html_report(result, str(output_path))

    assert output.exists()
    assert output.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_render_answer_html_inserts_media_at_marked_positions():
    answer = "\n".join(
        [
            "结论：一阶系统的典型响应可以先从式1判断。",
            "[[MEDIA:KM014.formula_asset[1]]]",
            "分析：再结合图1观察时间常数与稳态值。",
            "[[MEDIA:KM014.figure_asset[1]]]",
        ]
    )
    media_cards_by_ref = {
        "KM014.formula_asset[1]": "<div>formula-card</div>",
        "KM014.figure_asset[1]": "<div>figure-card</div>",
    }
    media_labels_by_ref = {
        "KM014.formula_asset[1]": "式1",
        "KM014.figure_asset[1]": "图1",
    }

    html_text = _render_answer_html(answer, media_cards_by_ref, media_labels_by_ref)

    assert html_text.index("结论") < html_text.index("formula-card")
    assert html_text.index("分析") < html_text.index("figure-card")
    assert "补充公式与图表" not in html_text
    assert "式1" in html_text
    assert "图1" in html_text


def test_render_answer_html_keeps_multiline_block_math_together():
    answer = "\n".join(
        [
            "分析：超调量可写成如下形式。",
            "$$",
            r"\sigma\% = e^{-\pi\zeta/\sqrt{1-\zeta^2}} \times 100\%",
            "$$",
        ]
    )

    html_text = _render_answer_html(answer, {}, {})

    assert "<div class=\"formula-math answer-formula\">" in html_text
    assert r"\sigma\%" in html_text
