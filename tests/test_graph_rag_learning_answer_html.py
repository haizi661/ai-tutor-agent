from pathlib import Path

from ai_tutor_agent.knowledge_map.debug_graph_rag import build_learning_answer_html


def test_build_learning_answer_html_uses_learning_components_for_main_flow():
    result = {
        "question": "二阶系统性能指标怎么理解？",
        "answer": "结论：先用式一看阻尼比，再看图一的响应曲线。 [[MEDIA:KM015.formula_asset[1]]] [[MEDIA:KM013.figure_asset[1]]]",
        "evidence_items": [{"reference": "KM015.summary", "text": "二阶系统性能指标。"}],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM015.formula_asset[1]",
                "display_label": "式一",
                "node_name": "二阶系统的时域分析",
                "text": "\n$$\n\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%\n$$\n",
                "formula_meaning": "阻尼比越大，超调量越小。",
            },
            {
                "asset_type": "figure",
                "reference": "KM013.figure_asset[1]",
                "display_label": "图一",
                "node_name": "二阶系统响应曲线",
                "caption": "单位阶跃响应曲线",
                "image_paths_abs": [str(Path("tests/sample.png").resolve())],
                "visual_summary": "曲线峰值对应超调量。",
            },
        ],
    }

    html_text = build_learning_answer_html(result)

    assert "learning-answer-content" in html_text
    assert "learning-reference-block" in html_text
    assert "learning-reference-text" in html_text
    assert "learning-reference-media" in html_text
    assert "learning-related-overview" not in html_text
    assert "正文引用的相关公式与图表" not in html_text
    assert "位置。 ]" not in html_text
    assert "learning-formula-card" in html_text
    assert "learning-figure-card" in html_text
    assert "learning-formula-viewport" in html_text
    assert "learning-figure-viewport" in html_text
    assert "learning-block-caption" in html_text
    assert "formula-render" in html_text
    assert 'data-learning-action="open"' in html_text
    assert 'data-learning-action="copy"' in html_text
    assert "onclick=" not in html_text
    assert 'data-latex="\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%"' in html_text
    assert "data:image/png;base64," in html_text
    assert "learning-evidence-card" in html_text
    assert "KM015.summary" in html_text

    assert "graph-rag-answer-panel" not in html_text
    assert "graph-rag-evidence-panel" not in html_text
    assert "answer-media-block" not in html_text
    assert "media-card" not in html_text
    assert "learning-derivation-card learning-media-group" not in html_text
    assert "GraphRAG 调试报告" not in html_text
    assert "$$" not in html_text


def test_build_learning_answer_html_renders_inline_math_with_learning_viewport():
    result = {
        "question": "超调量公式是什么？",
        "answer": "分析：下面这个公式给出阻尼比和超调量的关系。\n$$\n\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%\n$$",
        "evidence_items": [],
        "media_items": [],
    }

    html_text = build_learning_answer_html(result)

    assert "learning-inline-formula-card" in html_text
    assert "learning-formula-viewport" in html_text
    assert "formula-render" in html_text
    assert "formula-scroll" not in html_text
    assert "answer-formula" not in html_text
    assert "$$" not in html_text


def test_build_learning_answer_html_embeds_table_as_local_scroll_card():
    result = {
        "question": "表格怎么读？",
        "answer": "结论：见表一。 [[MEDIA:KM020.table_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM020.table_asset[1]",
                "display_label": "表一",
                "node_name": "典型输入信号",
                "caption": "常见输入信号对照",
                "text": "<table><tr><th>输入</th><th>含义</th></tr><tr><td>阶跃</td><td>突变目标</td></tr></table>",
            }
        ],
    }

    html_text = build_learning_answer_html(result)

    assert "learning-table-card" in html_text
    assert "learning-table-viewport" in html_text
    assert 'data-learning-action="open"' in html_text
    assert 'data-learning-action="copy"' in html_text
    assert "onclick=" not in html_text
    assert "<table>" in html_text
    assert "table-viewport" not in html_text.replace("learning-table-viewport", "")


def test_learning_answer_dedupes_media_marker_followed_by_formula_and_figure_payload():
    result = {
        "question": "二阶系统超调量怎么理解？",
        "answer": (
            "分析：先看式一，它给出阻尼比和超调量的关系。 [[MEDIA:KM015.formula_asset[1]]]\n"
            "二阶系统的时域分析\n"
            "$$\n"
            "\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%\n"
            "$$\n"
            "再结合图一看峰值位置。 [[MEDIA:KM013.figure_asset[1]]]\n"
            "系统时间响应的性能指标\n"
            "单位阶跃响应曲线"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM015.formula_asset[1]",
                "display_label": "式一",
                "node_name": "二阶系统的时域分析",
                "text": "\\sigma\\% = e^{-\\pi\\zeta/\\sqrt{1-\\zeta^2}}\\times 100\\%",
                "formula_meaning": "阻尼比越大，超调量越小。",
            },
            {
                "asset_type": "figure",
                "reference": "KM013.figure_asset[1]",
                "display_label": "图一",
                "node_name": "系统时间响应的性能指标",
                "caption": "单位阶跃响应曲线",
                "image_paths_abs": [],
                "visual_summary": "曲线峰值对应超调量。",
            },
        ],
    }

    html_text = build_learning_answer_html(result)

    assert html_text.count("learning-formula-card") == 1
    assert "learning-inline-formula-card" not in html_text
    assert html_text.count("learning-figure-card") == 1
    assert "learning-related-overview" not in html_text
    assert "<p>二阶系统的时域分析</p>" not in html_text
    assert "<p>单位阶跃响应曲线</p>" not in html_text
    assert "$$" not in html_text


def test_learning_answer_dedupes_referenced_table_payload():
    result = {
        "question": "表格怎么读？",
        "answer": (
            "分析：表一列出典型输入信号的含义。 [[MEDIA:KM020.table_asset[1]]]\n"
            "| 输入 | 含义 |\n"
            "| --- | --- |\n"
            "| 阶跃 | 突变目标 |"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM020.table_asset[1]",
                "display_label": "表一",
                "node_name": "典型输入信号",
                "caption": "常见输入信号对照",
                "text": "<table><tr><th>输入</th><th>含义</th></tr><tr><td>阶跃</td><td>突变目标</td></tr></table>",
            }
        ],
    }

    html_text = build_learning_answer_html(result)

    assert html_text.count("learning-table-card") == 1
    assert "answer-table" not in html_text
    assert "learning-related-overview" not in html_text


def test_learning_answer_dedupes_referenced_raw_html_table_payload():
    raw_table = (
        '<table><tr><td></td><td>系统方程</td><td>原点稳定性</td>'
        '<td>充分必要条件或充分条件</td></tr>'
        '<tr><td rowspan="2">间接法</td><td rowspan="2">\\dot{x}=Ax,t≥0 x(0)=x0</td>'
        '<td>稳定</td><td>A的所有特征值均具有非正实部</td></tr>'
        '<tr><td>渐近稳定</td><td>A的所有特征值均具有负实部</td></tr></table>'
    )
    result = {
        "question": "稳定性判据表怎么读？",
        "answer": (
            "分析：表二十五总结了不同系统的稳定性判据。 [[MEDIA:KM025.table_asset[1]]]\n"
            f"{raw_table}"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM025.table_asset[1]",
                "display_label": "表二十五",
                "node_name": "自动控制系统稳定性",
                "caption": "表二十五：对自动控制系统的基本要求",
                "text": raw_table,
            }
        ],
    }

    html_text = build_learning_answer_html(result)
    before_card = html_text.split("learning-table-card", 1)[0]

    assert html_text.count("learning-table-card") == 1
    assert "learning-table-viewport" in html_text
    assert "&lt;table&gt;" not in before_card
    assert "&lt;tr&gt;" not in before_card
    assert "<table>" in html_text
    assert 'rowspan="2"' in html_text
    assert "表一 · 自动控制系统稳定性" in html_text
    assert "表一：对自动控制系统的基本要求" in html_text
    default_flow = html_text.split("<details", 1)[0]
    assert "表二十五" not in default_flow
    assert "分析：" not in default_flow
    assert "总结了不同系统的稳定性判据" not in default_flow


def test_learning_answer_uses_user_facing_evidence_cards_and_hides_debug_metadata():
    result = {
        "question": "临时问答里的公式图表怎么展示？",
        "answer": "分析：先看式一，再看图一。 [[MEDIA:chapter_01_p009-032_自动控制的一般概念__8a418239:formula:f380d1fcf3da]] [[MEDIA:KM002.figure_asset[1]]]",
        "evidence_items": [
            {"reference": "chapter_01_p009-032_自动控制的一般概念__8a418239:chunk:001", "text": "自动控制的一般概念。"}
        ],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "chapter_01_p009-032_自动控制的一般概念__8a418239:formula:f380d1fcf3da",
                "display_label": "式一",
                "node_name": "自动控制的一般概念",
                "text": r"\dot{y}(t)+y(t)\dot{y}(t)+y^2(t)=r(t)",
                "formula_meaning": "给出输出变量及其导数与输入之间的定量关系。",
            },
            {
                "asset_type": "figure",
                "reference": "KM002.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制的基本原理与方式",
                "caption": "图 1-1 人取书的反馈控制系统方框图",
                "image_paths_abs": [],
                "visual_summary": "说明反馈控制系统的组成和信号流向。",
            },
        ],
    }

    html_text = build_learning_answer_html(result)
    before_details = html_text.split("<details", 1)[0]

    assert "learning-evidence-card--formula" in html_text
    assert "learning-evidence-card--figure" in html_text
    assert 'learning-evidence-type">公式' in html_text
    assert 'learning-evidence-type">图表' in html_text
    assert "learning-evidence-title" in html_text
    assert "learning-evidence-summary" in html_text
    assert "learning-source-line" in html_text
    assert "learning-debug-details" in html_text
    assert "查看来源详情" in html_text
    assert "查看 LaTeX" in html_text
    assert "learning-figure-unavailable" in html_text
    assert "图表暂时无法预览" in html_text

    assert "chapter_01_p009-032_自动控制的一般概念__8a418239" not in before_details
    assert "KM002.figure_asset[1]" not in before_details
    assert "[KM002.figure_asset[1]]" not in before_details
    assert "<pre>" not in before_details
    assert "查看 LaTeX" not in before_details



def test_graph_rag_debug_report_contract_remains_separate():
    from ai_tutor_agent.knowledge_map.debug_graph_rag import build_answer_media_html

    result = {
        "question": "q",
        "answer": "见式一。 [[MEDIA:KM001.formula_asset[1]]]",
        "evidence_items": [],
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

    html_text = build_answer_media_html(result)

    assert "graph-rag-answer-panel" in html_text
    assert "answer-media-block" in html_text
    assert "media-card" in html_text
    assert "learning-answer-content" not in html_text


def test_learning_answer_keeps_unreferenced_media_as_compact_overview_after_text_sections():
    result = {
        "question": "什么是自动控制原理？",
        "answer": (
            "结论：自动控制原理研究反馈调节。\n"
            "分析：核心是测量输出、比较偏差、再修正输入。图一能说明闭环结构。 [[MEDIA:KM002.figure_asset[1]]]\n"
            "举例：恒温热水器会根据温差调节加热功率。"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM002.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制的基本原理与方式",
                "caption": "反馈控制系统方框图",
                "image_paths_abs": [],
                "visual_summary": "展示输入、比较、控制器、被控对象和反馈通道。",
            },
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制的一般概念",
                "text": r"e(t)=r(t)-y(t)",
                "formula_meaning": "偏差等于期望输入与实际输出之差。",
            },
        ],
    }

    html_text = build_learning_answer_html(result)

    assert html_text.index("核心是测量输出") < html_text.index("learning-reference-media")
    assert html_text.index("举例：") < html_text.index("learning-related-overview")
    assert "更多可参考的公式与图表" in html_text
    assert "KM001.formula_asset[1]" in html_text
    assert html_text.count('class="learning-reference-media"') == 1


def test_learning_answer_limits_unreferenced_related_media_to_reduce_noise():
    result = {
        "question": "什么是自动控制原理？",
        "answer": "分析：图一说明闭环结构。 [[MEDIA:KM002.figure_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM002.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制的基本原理与方式",
                "caption": "反馈控制系统方框图",
                "image_paths_abs": [],
            },
            *[
                {
                    "asset_type": "formula",
                    "reference": f"KM001.formula_asset[{idx}]",
                    "display_label": f"式{idx}",
                    "node_name": "自动控制的一般概念",
                    "text": rf"e_{idx}(t)=r(t)-y(t)",
                }
                for idx in range(1, 6)
            ],
        ],
    }

    html_text = build_learning_answer_html(result)
    overview = html_text.split("learning-related-overview", 1)[1]

    assert "更多可参考的公式与图表" in html_text
    assert overview.count("learning-formula-card") == 3
    assert "KM001.formula_asset[1]" in overview
    assert "KM001.formula_asset[3]" in overview
    assert "KM001.formula_asset[4]" not in overview
    assert html_text.count("learning-figure-card") == 1


def test_learning_answer_binds_bare_bracket_media_reference_in_prose():
    result = {
        "question": "图怎么理解？",
        "answer": "分析：这个闭环结构可以直接看[KM002.figure_asset[1]]，它展示反馈通道。",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM002.figure_asset[1]",
                "display_label": "图一",
                "node_name": "反馈控制",
                "caption": "反馈控制系统方框图",
                "image_paths_abs": [],
                "visual_summary": "展示输入、比较、执行与反馈。",
            }
        ],
    }

    html_text = build_learning_answer_html(result)

    assert "learning-reference-block" in html_text
    assert "learning-reference-media" in html_text
    assert "更多可参考的公式与图表" not in html_text
    assert "[KM002.figure_asset[1]]" not in html_text.split("learning-media-ref", 1)[0]
