from pathlib import Path

from ai_tutor_agent.knowledge_map.debug_graph_rag import build_learning_answer_html


def test_build_learning_answer_html_uses_learning_components_for_main_flow():
    result = {
        "question": "二阶系统性能指标怎么理解？",
        "answer": "结论：二阶系统性能指标要先看阻尼比 [KM015.summary]，再结合式一和图一。 [[MEDIA:KM015.formula_asset[1]]] [[MEDIA:KM013.figure_asset[1]]]",
        "evidence_items": [
            {
                "node_id": "KM015",
                "node_name": "二阶系统的时域分析",
                "attribute": "summary",
                "reference": "KM015.summary",
                "text": "二阶系统性能指标。",
            }
        ],
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
    assert "learning-citation" in html_text
    assert "learning-citation-index" in html_text
    assert 'title="知识图谱：二阶系统的时域分析 · 摘要（KM015.summary）"' in html_text
    assert "节点：二阶系统的时域分析 · 摘要" in html_text
    assert "[KM015.summary]" not in html_text.split("<details", 1)[0]

    assert "graph-rag-answer-panel" not in html_text
    assert "graph-rag-evidence-panel" not in html_text
    assert "answer-media-block" not in html_text
    assert "media-card" not in html_text
    assert "learning-derivation-card learning-media-group" not in html_text
    assert "GraphRAG 调试报告" not in html_text
    assert "$$" not in html_text


def test_learning_answer_numbers_km_citations_by_first_appearance_and_hides_raw_refs():
    result = {
        "question": "自动控制原理怎么理解？",
        "answer": (
            "分析：根基由“自动控制的一般概念”[KM001.summary]、"
            "“控制系统的数学模型”[KM007.summary] 和“线性系统的时域分析法”[KM012.summary] 共同构建。\n"
            "依据：\n"
            "1. [KM015.summary] 分析二阶系统动态过程及典型性能指标。\n"
            "2. [E009] 二阶系统的时域分析 --[prerequisite_of]--> 一阶系统的时域分析；关系强度=1.00。"
        ),
        "node_summaries": [
            {"node_id": "KM001", "name": "自动控制的一般概念"},
            {"node_id": "KM007", "name": "控制系统的数学模型"},
            {"node_id": "KM012", "name": "线性系统的时域分析法"},
        ],
        "evidence_items": [
            {"node_id": "KM015", "node_name": "二阶系统的时域分析", "attribute": "summary", "reference": "KM015.summary", "text": "分析二阶系统动态过程及典型性能指标。"},
        ],
        "media_items": [],
    }

    html_text = build_learning_answer_html(result)
    before_details = html_text.split("<details", 1)[0]

    assert "[KM001.summary]" not in before_details
    assert "[KM007.summary]" not in before_details
    assert "[KM012.summary]" not in before_details
    assert "[KM015.summary]" not in before_details
    assert "[E009]" not in before_details
    assert 'learning-citation-index">1<' in before_details
    assert 'learning-citation-index">2<' in before_details
    assert 'learning-citation-index">3<' in before_details
    assert "知识图谱：自动控制的一般概念 · 摘要（KM001.summary）" in html_text
    assert "知识图谱：控制系统的数学模型 · 摘要（KM007.summary）" in html_text
    assert "知识图谱：线性系统的时域分析法 · 摘要（KM012.summary）" in html_text
    assert "关系强度=1.00" not in before_details


def test_learning_answer_renders_parenthesized_km_groups_as_citation_chips():
    result = {
        "question": "自动控制原理的基础是什么？",
        "answer": (
            "分析：系统组成可以结合自动控制的一般概念和自动控制系统示例理解（KM001、KM003），"
            "数学表示看控制系统的数学模型（KM007）。"
        ),
        "node_summaries": [
            {"node_id": "KM001", "name": "自动控制的一般概念"},
            {"node_id": "KM003", "name": "自动控制系统示例"},
            {"node_id": "KM007", "name": "控制系统的数学模型"},
        ],
        "evidence_items": [],
        "media_items": [],
    }

    html_text = build_learning_answer_html(result)
    before_details = html_text.split("<details", 1)[0]

    assert "（KM001、KM003）" not in before_details
    assert "(KM001" not in before_details
    assert "(KM007" not in before_details
    assert 'learning-citation-index">1<' in before_details
    assert 'learning-citation-index">2<' in before_details
    assert 'learning-citation-index">3<' in before_details
    assert "知识图谱：自动控制的一般概念 · 摘要（KM001.summary）" in html_text
    assert "知识图谱：自动控制系统示例 · 摘要（KM003.summary）" in html_text
    assert "知识图谱：控制系统的数学模型 · 摘要（KM007.summary）" in html_text


def test_learning_answer_maps_standalone_numeric_citations_to_evidence_order():
    result = {
        "question": "自动控制原理是什么？",
        "answer": (
            "分析：根据图谱证据，自动控制的核心在于反馈。\n"
            "1\n"
            "指出自动控制涉及基本原理和系统组成，而\n"
            "6\n"
            "强调通过典型实例理解系统构成。\n"
            "依据：\n"
            "1.\n"
            "1\n"
            "介绍自动控制的基本原理。\n"
            "2.\n"
            "6\n"
            "通过典型实例理解自动控制系统。"
        ),
        "evidence_items": [
            {
                "node_id": f"KM00{idx}",
                "node_name": name,
                "attribute": "summary",
                "reference": f"KM00{idx}.summary",
                "text": text,
            }
            for idx, name, text in [
                (1, "自动控制的一般概念", "介绍自动控制的基本原理。"),
                (2, "控制系统分类", "介绍控制系统分类。"),
                (3, "控制系统要求", "介绍控制系统要求。"),
                (4, "控制系统分析工具", "介绍分析设计工具。"),
                (5, "控制系统基本方式", "介绍控制方式。"),
                (6, "自动控制系统示例", "通过典型实例理解自动控制系统。"),
            ]
        ],
        "media_items": [],
    }

    html_text = build_learning_answer_html(result)
    before_details = html_text.split("<details", 1)[0]

    assert "\n1\n" not in before_details
    assert "\n6\n" not in before_details
    assert 'learning-citation-index">1<' in before_details
    assert 'learning-citation-index">2<' in before_details
    assert "知识图谱：自动控制的一般概念 · 摘要（KM001.summary）" in html_text
    assert "知识图谱：自动控制系统示例 · 摘要（KM006.summary）" in html_text


def test_learning_answer_attaches_media_when_text_mentions_formula_or_figure_alias():
    result = {
        "question": "自动控制原理是什么？",
        "answer": (
            "分析：以函数记录仪（如图1-8）为例，可以说明反馈闭环结构。"
            "典型输入如阶跃信号（式1-1）用于考察系统响应。\n"
            "f\n(\nt\n)\n=\n{\n0\n,\nt\n<\n0\nR\n,\nt\n≥\n0"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM003.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制系统示例",
                "caption": "图 1-8 函数记录仪原理示意图",
                "image_paths_abs": [],
            },
            {
                "asset_type": "formula",
                "reference": "KM003.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制系统示例",
                "text": r"f(t)=\left\{\begin{array}{ll}0,&t<0\\R,&t\geqslant0\end{array}\right.\tag{1-1}",
            },
        ],
    }

    html_text = build_learning_answer_html(result)

    assert html_text.count("learning-reference-block") == 1
    assert "learning-figure-card" in html_text
    assert "learning-formula-card" in html_text
    assert "图 1-8 函数记录仪原理示意图" in html_text
    assert 'data-latex="f(t)=\\left\\{\\begin{array}{ll}0,&amp;t&lt;0\\\\R,&amp;t\\geqslant0\\end{array}\\right.\\tag{1-1}"' in html_text
    assert "<p>f</p>" not in html_text


def test_temporary_question_binds_precise_figure_and_formula_aliases_without_media_tokens():
    result = {
        "question": "图和公式怎么对应？",
        "answer": "这里看图1-5的反馈通道，再用式1-1理解阶跃输入；不要把旁边的式1-2混进来。",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM001.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制的一般概念",
                "caption": "图 1-5 典型反馈控制系统方框图",
                "image_paths": [],
            },
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制的一般概念",
                "text": r"f(t)=R\cdot 1(t)\tag{1-1}",
            },
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[2]",
                "display_label": "式二",
                "node_name": "自动控制的一般概念",
                "text": r"g(t)=0\tag{1-2}",
            },
        ],
    }

    html_text = build_learning_answer_html(result, answer_context="temporary_question")

    assert html_text.count("learning-reference-block") == 1
    assert "learning-media-temporary" in html_text
    assert "图 1-5 典型反馈控制系统方框图" in html_text
    assert "f(t)=R" in html_text
    assert "g(t)=0" not in html_text
    assert "更多可参考的公式与图表" not in html_text
    assert "查看来源详情" not in html_text


def test_temporary_question_keeps_concise_learning_references_without_raw_debug_refs():
    result = {
        "question": "为什么要看反馈？",
        "answer": "分析：反馈通道决定系统如何根据偏差修正输出。",
        "evidence_items": [
            {
                "node_id": "KM001",
                "node_name": "自动控制的一般概念",
                "attribute": "summary",
                "reference": "KM001.summary",
                "text": "反馈控制系统通过比较输入与输出形成偏差，并据此修正控制作用。",
            },
            {
                "node_id": "KM003",
                "node_name": "自动控制系统示例",
                "attribute": "definition",
                "reference": "KM003.definition",
                "text": "具体系统示例展示了反馈信号如何回到比较环节。",
            },
        ],
        "media_items": [],
    }

    html_text = build_learning_answer_html(result, answer_context="temporary_question")
    visible_text = html_text.split("<details", 1)[0]

    assert "参考依据" in html_text
    assert "learning-evidence-card--source" in html_text
    assert "反馈控制系统通过比较输入与输出形成偏差" in html_text
    assert "节点：自动控制的一般概念 · 摘要" in html_text
    assert "节点：自动控制系统示例 · 定义" in html_text
    assert 'learning-citation-index">1<' in html_text
    assert 'learning-citation-index">2<' in html_text
    assert "查看来源详情" not in html_text
    assert "KM001.summary" not in visible_text
    assert "KM003.definition" not in visible_text


def test_temporary_question_inserts_media_in_prose_mention_order():
    result = {
        "question": "先看哪个？",
        "answer": "先看式1-1确定输入形式，再看图1-5理解反馈通路。",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "figure",
                "reference": "KM001.figure_asset[1]",
                "display_label": "图一",
                "node_name": "自动控制的一般概念",
                "caption": "图 1-5 典型反馈控制系统方框图",
                "image_paths": [],
            },
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制的一般概念",
                "text": r"f(t)=R\cdot 1(t)\tag{1-1}",
            },
        ],
    }

    html_text = build_learning_answer_html(result, answer_context="temporary_question")

    assert html_text.index("先看式1-1") < html_text.index("learning-reference-media")
    assert html_text.index("learning-formula-card") < html_text.index("learning-figure-card")


def test_learning_answer_strips_embedded_learning_html_from_llm_override():
    result = {
        "question": "q",
        "answer": (
            "分析：先看式一。 [[MEDIA:KM001.formula_asset[1]]]\n"
            '<section class="learning-evidence-card learning-evidence-card--formula learning-formula-card">'
            '<div class="learning-formula-viewport"><div class="formula-render">x</div></div>'
            "</section>\n"
            "拓展：回到概念。"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制的一般概念",
                "text": "x",
            }
        ],
    }

    html_text = build_learning_answer_html(result)

    assert html_text.count("learning-formula-card") == 1
    assert "&lt;section" not in html_text
    assert "<p>拓展：回到概念。</p>" not in html_text
    assert "回到概念" in html_text


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


def test_learning_answer_omits_raw_html_table_from_evidence_summary():
    raw_table = "<table><tr><td>系统编号</td><td>超调量</td></tr><tr><td>1</td><td>13.8%</td></tr></table>"
    escaped_table = raw_table.replace("<", "&lt;").replace(">", "&gt;")
    result = {
        "question": "表格怎么读？",
        "answer": "分析：见表一。 [[MEDIA:KM020.table_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM020.table_asset[1]",
                "display_label": "表一",
                "node_name": "一阶系统的时域分析",
                "caption": "系统时间响应的性能指标",
                "analysis_hint": escaped_table,
                "text": raw_table,
            }
        ],
    }

    html_text = build_learning_answer_html(result)

    assert escaped_table not in html_text
    assert "&lt;table" not in html_text
    assert "learning-evidence-summary" not in html_text.split("learning-table-viewport", 1)[0]
    assert "<table>" in html_text


def test_learning_answer_repairs_malformed_table_html_and_drops_ocr_row_numbers():
    malformed_table = (
        "<table><tr><td>系统编号</td><td>系统闭环传递函数</td><td>超调量</td></tr>"
        "<tr>16<tr>17<td>\\( G(s) \\)</td><td>13.8%</td></tr>"
        "<tr>30<td>31<td>\\( H(s) \\)</td><td>15.9%</td></tr></table>"
    )
    result = {
        "question": "表格怎么读？",
        "answer": "分析：见表一。 [[MEDIA:KM020.table_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "table",
                "reference": "KM020.table_asset[1]",
                "display_label": "表一",
                "node_name": "一阶系统的时域分析",
                "caption": "系统时间响应的性能指标",
                "text": malformed_table,
            }
        ],
    }

    html_text = build_learning_answer_html(result)
    table_view = html_text.split("learning-table-viewport", 1)[1].split("learning-source-line", 1)[0]

    assert "<table><tbody>" in table_view
    assert "<tr>16" not in table_view
    assert "<tr>17" not in table_view
    assert "<tr>30" not in table_view
    assert "<td>31" not in table_view
    assert "\\( G(s) \\)" in table_view
    assert "13.8%" in table_view
    assert "\\( H(s) \\)" in table_view
    assert "15.9%" in table_view


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
    assert "扩展知识：可选公式与图表" in html_text
    assert "这些材料不是本段正文的必需引用" in html_text
    assert "KM001.formula_asset[1]" in html_text
    assert html_text.count('class="learning-reference-media"') == 1


def test_learning_answer_appends_unreferenced_related_media_as_extension_knowledge():
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

    assert "扩展知识：可选公式与图表" in html_text
    assert "这些材料不是本段正文的必需引用" in html_text
    assert overview.count("learning-formula-card") == 3
    assert "KM001.formula_asset[1]" in overview
    assert "KM001.formula_asset[3]" in overview
    assert "KM001.formula_asset[4]" not in overview
    assert html_text.count("learning-figure-card") == 1


def test_learning_answer_places_formula_extension_after_no_formula_lesson():
    result = {
        "question": "讲解自动控制的一般概念",
        "answer": (
            "**3. 公式讲解**\n"
            "本节点不涉及新数学公式，但要记住偏差来自输入与反馈的比较。\n"
            "**4. 图表说明**\n"
            "这里先用文字说明测量、比较、执行三步。"
        ),
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "自动控制的一般概念",
                "text": r"\dot y(t)+y(t)=r(t)",
                "formula_meaning": "给出变量之间的定量关系。",
            },
        ],
    }

    html_text = build_learning_answer_html(result)

    assert html_text.index("本节点不涉及新数学公式") < html_text.index("learning-related-overview")
    assert "扩展知识：可选公式与图表" in html_text
    assert "这些材料不是本段正文的必需引用" in html_text
    assert "learning-formula-card" in html_text
    assert "KM001.formula_asset[1]" in html_text
    assert r"\dot y" in html_text


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
