from pathlib import Path


UI_JS = Path("frontend/assets/js/ui.js")
SESSION_JS = Path("frontend/assets/js/session.js")


def test_objective_test_card_has_collapsible_submitted_review_ui():
    content = UI_JS.read_text(encoding="utf-8")

    assert "obj-test-review-toggle" in content
    assert "obj-test-review-body" in content
    assert "默认收起，点击展开查看作答情况" in content
    assert "你的答案" in content
    assert "正确答案" in content
    assert "aria-expanded" in content


def test_submitting_objective_answers_does_not_remove_card():
    content = SESSION_JS.read_text(encoding="utf-8")

    assert "document.querySelector('.obj-test-card')?.remove();" not in content
    assert "app.collapseSubmittedObjectiveTestCard" in content


def test_objective_and_variant_cards_are_not_globally_removed_when_next_card_renders():
    content = UI_JS.read_text(encoding="utf-8")

    render_start = content.index("app.renderObjectiveTestCard = function renderObjectiveTestCard")
    render_end = content.index("function applySessionArtifacts", render_start)
    render_body = content[render_start:render_end]

    assert "document.querySelector('.obj-test-card')?.remove()" not in render_body
    assert "app.renderObjectiveQuizReviewCard" in content
    assert "objective_quiz_review" in content
    assert "variant_test_answers" in content


def test_frontend_restores_persistent_quiz_review_and_wrong_explanations_from_timeline():
    content = UI_JS.read_text(encoding="utf-8")

    assert "item.kind === 'objective_quiz_review'" in content
    assert "app.renderObjectiveQuizReviewCard" in content
    assert "item.kind === 'wrong_question_explanations'" in content
    assert "错题订正讲解" in content


def test_frontend_allows_graphrag_debug_report_html_and_math_assets():
    ui_content = UI_JS.read_text(encoding="utf-8")
    session_content = SESSION_JS.read_text(encoding="utf-8")

    assert "graph_rag_debug_report" in session_content or "graph_rag_debug_report" in ui_content
    assert "allowGraphRagHtml" in ui_content
    assert "GraphRAG 调试报告" in ui_content
    assert "answer-media-block" in ui_content
    assert "media-card" in ui_content
    assert "app.renderMath" in ui_content
    assert "{ left: '\\\\[', right: '\\\\]', display: true }" in ui_content
    assert "{ left: '\\\\(', right: '\\\\)', display: false }" in ui_content
    styles = Path("frontend/assets/styles.css").read_text(encoding="utf-8")
    assert 'data-role="graph_rag_debug_report"' in styles
    assert ".media-grid" in styles
    assert ".formula-math" in styles


def test_frontend_renders_wrong_question_explanations_immediately_from_sse_before_variant_card():
    session_js = SESSION_JS.read_text(encoding="utf-8")

    complete_start = session_js.index("state.eventSource.addEventListener('node.complete'")
    complete_end = session_js.index("state.eventSource.addEventListener('intent.detected'", complete_start)
    complete_handler = session_js[complete_start:complete_end]

    assert "data.source === 'wrong_question_explainer'" in complete_handler
    assert "wrong_question_explanations" in complete_handler
    assert "app.appendMessage?.('agent'" in complete_handler
    assert complete_handler.index("data.source === 'wrong_question_explainer'") < complete_handler.index("app.clearTypingIndicator")
