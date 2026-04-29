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
    assert "document.querySelectorAll('.obj-test-card:not(.submitted-collapsed)').forEach(card => card.remove())" in render_body


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
    assert "grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))" in styles
    assert "align-items: stretch" in styles
    assert "min-height: 230px" in styles
    assert "height: auto" in styles
    assert "min-width: max-content" in styles
    assert "justify-content: center" in styles
    assert "formula-scroll" in styles
    assert "formula-viewport" in styles
    assert "overflow: auto" in styles
    assert "max-height: 420px" in styles
    assert "media-unavailable-card" in styles
    assert "modal-content--wide" in styles
    assert "table-viewport" in styles
    assert ".formula-math" in styles


def test_frontend_locks_confirmation_and_dialog_cards_after_user_action():
    ui_content = UI_JS.read_text(encoding="utf-8")
    session_content = SESSION_JS.read_text(encoding="utf-8")

    assert "app.lockActiveChoiceCard" in ui_content
    assert "choice-card--locked" in ui_content
    assert "dataset.choiceValue" in ui_content
    assert "dataset.choiceLabel" in ui_content
    assert "dataset.cardKind = 'post_eval_selector'" in ui_content
    assert "dataset.cardKind = 'next_step_selector'" in ui_content
    assert "app.lockActiveChoiceCard?.(text, visibleText)" in session_content
    assert "document.querySelector('.post-eval-card')?.remove();" not in session_content
    assert "document.querySelector('.next-step-card')?.remove();" not in session_content
    assert "d.classList.add('locked')" in ui_content
    assert "submitBtn.remove()" in ui_content


def test_frontend_restores_skipped_topic_and_assessment_as_locked_artifacts():
    ui_content = UI_JS.read_text(encoding="utf-8")
    session_content = SESSION_JS.read_text(encoding="utf-8")

    assert "item.kind === 'topic_confirmation_locked'" in ui_content
    assert "tc-locked-content" in ui_content
    assert "item.kind === 'assessment_form'" in ui_content
    assert "locked: isCompletedAssessment || data.locked === true" in ui_content
    assert "statusText: isCompletedAssessment ? '测评已完成，答案已固定' : data.statusText" in ui_content
    assert "_renderLockedAssessmentSummary(div, questions, state.answers, '已跳过学前测评，答案已固定')" in ui_content
    assert "row.wrap.remove();\n                app.submitTopicConfirmation?.(true, 'direct_tutor')" not in ui_content
    assert "startMode === 'direct_tutor' ? '跳过摸底，直接开始'" in session_content
    assert "formatErrorMessage(error)" in session_content
    assert "JSON.stringify(value)" in session_content


def test_frontend_renders_wrong_question_explanations_immediately_from_sse_before_variant_card():
    session_js = SESSION_JS.read_text(encoding="utf-8")

    complete_start = session_js.index("state.eventSource.addEventListener('node.complete'")
    complete_end = session_js.index("state.eventSource.addEventListener('intent.detected'", complete_start)
    complete_handler = session_js[complete_start:complete_end]

    assert "data.source === 'objective_test_scorer'" in complete_handler
    assert "app.renderObjectiveQuizReviewCard?.(data.data.review" in complete_handler
    assert "data.source === 'wrong_question_explainer'" in complete_handler
    assert "wrong_question_explanations" in complete_handler
    assert "app.appendMessage?.('agent'" in complete_handler
    assert complete_handler.index("data.source === 'objective_test_scorer'") < complete_handler.index("data.source === 'wrong_question_explainer'")
    assert complete_handler.index("data.source === 'wrong_question_explainer'") < complete_handler.index("app.clearTypingIndicator")


def test_frontend_quiz_review_reuses_submitted_card_before_rendering_variant_card():
    content = UI_JS.read_text(encoding="utf-8")
    review_start = content.index("app.renderObjectiveQuizReviewCard = function renderObjectiveQuizReviewCard")
    review_end = content.index("function applySessionArtifacts", review_start)
    review_body = content[review_start:review_end]

    assert "candidate.dataset.quizKind === kind && !candidate.dataset.reviewRendered" in review_body
    assert "reviewCard.dataset.reviewRendered = 'true'" in review_body
    assert "reviewCard.classList.add('submitted-collapsed')" in review_body
    assert "app.renderObjectiveTestCard(questions, kind)" in review_body
    assert review_body.index("existingCards.find") < review_body.index("app.renderObjectiveTestCard(questions, kind)")
    assert "card.dataset.quizKind = kind" in content
    assert "data.data?.review" in SESSION_JS.read_text(encoding="utf-8")


def test_frontend_quiz_review_finalizes_before_wrong_explanation_turn():
    content = UI_JS.read_text(encoding="utf-8")
    review_start = content.index("app.renderObjectiveQuizReviewCard = function renderObjectiveQuizReviewCard")
    review_end = content.index("function applySessionArtifacts", review_start)
    review_body = content[review_start:review_end]
    finalize_start = content.index("app.finalizeAgentTurn = function finalizeAgentTurn")
    finalize_end = content.index("app.roleFromMessageKind", finalize_start)
    finalize_body = content[finalize_start:finalize_end]

    assert "app.finalizeAgentTurn?.();" in review_body
    assert "data-contains-objective-review" in review_body
    assert "containsObjectiveReview" in finalize_body
    assert "agent-turn-finalized-review" in finalize_body


def test_frontend_restores_choice_cards_as_locked_from_timeline_data():
    content = UI_JS.read_text(encoding="utf-8")

    assert "app.lockChoiceCard" in content
    assert "renderPostLessonChoice(options = [], renderOptions = {})" in content
    assert "renderContinueOrHomeworkChoice(options = [], renderOptions = {})" in content
    assert "renderHomeworkReviewChoice(options = [], renderOptions = {})" in content
    assert "renderConsolidationChoice(options = [], renderOptions = {})" in content
    assert "app.lockChoiceCard(card, renderOptions.selectedValue || '', renderOptions.selectedLabel || renderOptions.statusText || '')" in content
    assert "item.kind === 'post_lesson_choice_card'" in content
    assert "item.kind === 'continue_or_homework_choice_card'" in content
    assert "item.kind === 'homework_review_choice_card'" in content
    assert "item.kind === 'consolidation_choice_card'" in content
    assert "app.renderPostLessonChoice?.(data.options || [], data)" in content
