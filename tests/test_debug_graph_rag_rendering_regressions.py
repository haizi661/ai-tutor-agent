from ai_tutor_agent.knowledge_map.debug_graph_rag import _render_answer_html, build_html_report


def test_unreferenced_debug_media_is_appended_after_main_answer_sections():
    media_cards_by_ref = {
        "KM013.figure_asset[1]": '<button class="media-card figure-card">figure</button>',
        "KM015.formula_asset[1]": '<button class="media-card formula-card">formula</button>',
    }
    media_labels_by_ref = {
        "KM013.figure_asset[1]": "图一",
        "KM015.formula_asset[1]": "式一",
    }
    answer = (
        "结论：先说明反馈抑制扰动的结论。\n"
        "分析：再解释误差驱动修正的原因。\n"
        "拓展：最后补充稳定性与带宽边界。"
    )

    html_text = _render_answer_html(answer, media_cards_by_ref, media_labels_by_ref)

    assert html_text.count('class="answer-media-block"') == 1
    assert "图谱检索到的相关公式与图表" in html_text
    assert html_text.index("拓展：") < html_text.index('class="answer-media-block"')
    assert html_text.index("figure-card") < html_text.index("formula-card")


def test_inline_formula_in_prose_is_rendered_without_raw_delimiters():
    html_text = _render_answer_html(
        "分析：偏差信号可写成 $$E(s)=R(s)-H(s)C(s)$$，因此能驱动纠偏。",
        {},
        {},
    )

    assert "inline-formula-render" in html_text
    assert 'data-display-mode="false"' in html_text
    assert 'data-latex="E(s)=R(s)-H(s)C(s)"' in html_text
    assert "$$E(s)=R(s)-H(s)C(s)$$" not in html_text


def test_formula_media_hint_strips_formula_noise_and_keeps_explanation():
    result = {
        "question": "q",
        "answer": "分析：见公式。[[MEDIA:KM001.formula_asset[1]]]",
        "evidence_items": [],
        "media_items": [
            {
                "asset_type": "formula",
                "reference": "KM001.formula_asset[1]",
                "display_label": "式一",
                "node_name": "反馈控制",
                "text": r"E(s)=R(s)-H(s)C(s)",
                "formula_meaning": "$$E(s)=R(s)-H(s)C(s)$$ 用于表示偏差信号。",
            },
        ],
    }

    html_text = build_html_report(result)

    assert "media-hint" in html_text
    assert "用于表示偏差信号" in html_text
    assert "$$E(s)=R(s)-H(s)C(s)$$" not in html_text
