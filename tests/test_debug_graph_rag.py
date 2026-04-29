from pathlib import Path

from ai_tutor_agent.knowledge_map.debug_graph_rag import (
    _render_answer_html,
    build_html_report,
    write_html_report,
)


def test_build_html_report_contains_modal_markup():
    result = {
        "question": "二阶系统有什么典型公式和图表？",
        "answer": "结论：可以结合式一与图一理解。",
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
                "display_label": "式一",
                "node_name": "一阶系统的时域分析",
                "text": r"c(t)=1-e^{-t/T}",
            },
            {
                "asset_type": "figure",
                "reference": "KM014.figure_asset[1]",
                "display_label": "图一",
                "node_name": "一阶系统的时域分析",
                "caption": "图 4-3 单位阶跃响应曲线",
                "image_paths_abs": [str(Path("tests/sample.png").resolve())],
            },
        ],
    }

    html_text = build_html_report(result)

    assert "openModal" in html_text
    assert "katex@0.16.9" in html_text
    assert "mathjax@3/es5/tex-svg.js" not in html_text
    assert "formula-math" in html_text
    assert "KM014.formula_asset[1]" in html_text
    assert "图 4-3 单位阶跃响应曲线" in html_text
    assert "相关公式与图表" in html_text
    assert "式一" in html_text
    assert "图一" in html_text
    assert "typesetMath(document)" in html_text


def test_build_html_report_embeds_figure_images_as_browser_safe_data_uri(tmp_path):
    image_path = tmp_path / "figure.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    result = {
        "question": "q",
        "answer": "结论：见图一。\n[[MEDIA:KM003.figure_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM003.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制系统示例",
                "caption": "图 1-8 函数记录仪原理示意图",
                "image_paths_abs": [str(image_path)],
            }
        ],
    }

    html_text = build_html_report(result)

    assert "figure-card" in html_text
    assert "data:image/png;base64," in html_text
    assert "file://" not in html_text


def test_build_html_report_renders_table_media_cards():
    result = {
        "question": "q",
        "answer": "分析：典型输入可见表一。\n[[MEDIA:KM013.table_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM013.table_asset[1]",
                "display_label": "表一",
                "node_name": "系统时间响应的性能指标",
                "caption": "典型输入信号",
                "text": "<table><tr><th>输入</th><th>表达式</th></tr><tr><td>阶跃</td><td>1(t)</td></tr></table>",
            }
        ],
    }

    html_text = build_html_report(result)

    assert "media-card table-card" in html_text
    assert "table-preview" in html_text
    assert "<table>" in html_text
    assert "典型输入信号" in html_text


def test_build_html_report_uses_card_grid_media_layout_and_non_distorting_visual_styles():
    result = {
        "question": "q",
        "answer": "结论：结合式一和图一。",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制系统的分类",
                "text": r"f(t)=\lim_{t_0 \to 0}\frac{A}{t_0}[1(t)-1(t-t_0)]",
            },
            {
                "asset_type": "figure",
                "reference": "KM007.figure_asset[1]",
                "display_label": "图一",
                "node_name": "控制系统的数学模型",
                "caption": "图 4-3 单位阶跃响应曲线",
                "image_paths_abs": [],
            },
        ],
    }

    html_text = build_html_report(result)

    assert "grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))" in html_text
    assert "align-items: stretch" in html_text
    assert "min-height: 230px" in html_text
    assert "height: auto" in html_text
    assert "max-width: 100%" in html_text
    assert "min-width: max-content" in html_text
    assert "overflow: auto" in html_text


def test_render_answer_html_converts_plain_media_reference_lines_into_one_card_grid():
    media_cards_by_ref = {
        "chapter_01.formula_asset[1]": '<button class="media-card formula-card">式一</button>',
        "chapter_01.formula_asset[2]": '<button class="media-card formula-card">式二</button>',
        "KM002.figure_asset[1]": '<button class="media-card figure-card">图一</button>',
    }
    media_labels_by_ref = {
        "chapter_01.formula_asset[1]": "式一",
        "chapter_01.formula_asset[2]": "式二",
        "KM002.figure_asset[1]": "图一",
    }
    answer = """式一 [chapter_01.formula_asset[1]]
自动控制的一般概念
$$
\\ddot{y}(t)+y(t)\\dot{y}(t)+y^2(t)=r(t)
$$
式二 [chapter_01.formula_asset[2]]
自动控制系统的分类
$$
f(t)=\\lim_{t_0\\to0}\\frac{A}{t_0}[1(t)-1(t-t_0)]
$$
图一 [KM002.figure_asset[1]]
自动控制的基本原理与方式
图 1-1 人取书的反馈控制系统方框图"""

    html_text = _render_answer_html(answer, media_cards_by_ref, media_labels_by_ref)

    assert html_text.count('class="answer-media-block"') == 1
    assert 'class="media-grid"' in html_text
    assert 'formula-card' in html_text
    assert 'figure-card' in html_text
    assert "chapter_01.formula_asset[1]" not in html_text
    assert "KM002.figure_asset[1]" not in html_text
    assert "\\ddot{y}(t)" not in html_text
    assert "图 1-1 人取书的反馈控制系统方框图" not in html_text


def test_build_html_report_embedded_formula_uses_katex_not_mathjax_or_raw_delimiters():
    result = {
        "question": "q",
        "answer": "见式一。 [[MEDIA:KM001.formula_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制系统的分类",
                "text": r"f(t)=\lim_{t_0 \to 0}\frac{A}{t_0}[1(t)-1(t-t_0)]",
            },
        ],
    }

    html_text = build_html_report(result)

    assert "katex@0.16.9" in html_text
    assert "katex.render" in html_text
    assert "mathjax@3" not in html_text
    assert r"\[" not in html_text
    assert r"\]" not in html_text
    assert "formula-scroll" in html_text


def test_build_html_report_skips_figure_card_when_image_source_missing():
    result = {
        "question": "q",
        "answer": "图一说明响应曲线。 [[MEDIA:KM007.figure_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM007.figure_asset[1]",
                "display_label": "图一",
                "node_name": "控制系统的数学模型",
                "caption": "图 4-3 单位阶跃响应曲线",
                "image_paths_abs": [],
            },
        ],
    }

    html_text = build_html_report(result)

    assert "figure-card" not in html_text
    assert "media-placeholder" not in html_text
    assert "media-unavailable-card" in html_text
    assert "图像文件暂不可用" in html_text


def test_build_html_report_keeps_missing_figure_reference_visible_as_unavailable_notice():
    result = {
        "question": "q",
        "answer": "图一说明响应曲线。 [[MEDIA:KM007.figure_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM007.figure_asset[1]",
                "display_label": "图一",
                "node_name": "控制系统的数学模型",
                "caption": "图 4-3 单位阶跃响应曲线",
                "image_paths_abs": [],
            },
        ],
    }

    html_text = build_html_report(result)

    assert "figure-card" not in html_text
    assert "media-unavailable-card" in html_text
    assert "图像文件暂不可用" in html_text
    assert "KM007.figure_asset[1]" in html_text
    assert "图 4-3 单位阶跃响应曲线" in html_text


def test_build_html_report_formula_and_figure_viewports_scroll_both_axes():
    result = {
        "question": "q",
        "answer": "见式一。 [[MEDIA:KM001.formula_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "复杂闭环传递函数",
                "text": r"\frac{U_o}{U_i}=\frac{abcd+e(1-gc-bf)}{1-db-gc-fb+dbgc+fbgc+bfdb}",
            },
        ],
    }

    html_text = build_html_report(result)

    assert "formula-viewport" in html_text
    assert "overflow: auto" in html_text
    assert "max-height: 420px" in html_text


def test_build_html_report_table_modal_uses_wide_viewer_for_full_table():
    result = {
        "question": "q",
        "answer": "见表一。 [[MEDIA:KM001.table_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM001.table_asset[1]",
                "display_label": "表一",
                "node_name": "自动控制的一般概念",
                "caption": "典型输入信号",
                "text": "<table><tr>" + "".join(f"<th>列{i}</th>" for i in range(12)) + "</tr><tr>" + "".join(f"<td>值{i}</td>" for i in range(12)) + "</tr></table>",
            },
        ],
    }

    html_text = build_html_report(result)

    assert "modal-content modal-content--wide" in html_text
    assert "table-viewport" in html_text
    assert "table-card" in html_text


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
            "结论：一阶系统的典型响应可以先从式一判断。",
            "[[MEDIA:KM014.formula_asset[1]]]",
            "分析：再结合图一观察时间常数与稳态值。",
            "[[MEDIA:KM014.figure_asset[1]]]",
        ]
    )
    media_cards_by_ref = {
        "KM014.formula_asset[1]": "<div>formula-card</div>",
        "KM014.figure_asset[1]": "<div>figure-card</div>",
    }
    media_labels_by_ref = {
        "KM014.formula_asset[1]": "式一",
        "KM014.figure_asset[1]": "图一",
    }

    html_text = _render_answer_html(answer, media_cards_by_ref, media_labels_by_ref)

    assert html_text.index("结论") < html_text.index("formula-card")
    assert html_text.index("分析") < html_text.index("figure-card")
    assert "补充公式与图表" not in html_text
    assert "式一" in html_text
    assert "图一" in html_text


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

    assert 'class="formula-scroll formula-viewport answer-formula"' in html_text
    assert "formula-render" in html_text
    assert r"\sigma\%" in html_text
