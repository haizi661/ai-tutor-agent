from pathlib import Path

from ai_tutor_agent.knowledge_map.debug_graph_rag import build_html_report, write_html_report


def test_build_html_report_contains_modal_markup():
    result = {
        "question": "????????????????????",
        "answer": "???????????????????",
        "evidence_items": [
            {
                "reference": "KM014.summary",
                "text": "???????????????????",
            }
        ],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM014.formula_asset[1]",
                "node_name": "?????????",
                "text": "c(t)=1-e^{-t/T}",
            },
            {
                "asset_type": "figure",
                "reference": "KM014.figure_asset[1]",
                "node_name": "?????????",
                "caption": "? 3-3 ?????????????",
                "image_paths_abs": [str(Path("tests/sample.png").resolve())],
            },
        ],
    }

    html_text = build_html_report(result)

    assert "openModal" in html_text
    assert "mathjax@3/es5/tex-svg.js" in html_text
    assert "formula-math" in html_text
    assert "KM014.formula_asset[1]" in html_text
    assert "? 3-3 ?????????????" in html_text


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
