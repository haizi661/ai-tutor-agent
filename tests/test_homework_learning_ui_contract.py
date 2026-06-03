from pathlib import Path


UI_JS = Path("frontend/assets/js/ui.js")
STYLES = Path("frontend/assets/styles.css")
HOMEWORK_GENERATOR = Path("ai_tutor_agent/nodes/homework_generator.py")
HOMEWORK_ANSWER = Path("ai_tutor_agent/nodes/homework_answer.py")
TUTOR = Path("ai_tutor_agent/nodes/tutor.py")
INTERRUPTION = Path("ai_tutor_agent/nodes/interruption.py")


def test_tutor_and_interruption_use_learning_answer_html_for_main_flow_graph_rag():
    tutor = TUTOR.read_text(encoding="utf-8")
    interruption = INTERRUPTION.read_text(encoding="utf-8")

    assert "build_learning_answer_html" in tutor
    assert "build_learning_answer_html" in interruption
    assert "build_answer_media_html" in interruption  # debug/legacy renderer remains available
    assert "full_response = build_learning_answer_html(graph_payload).strip()" in tutor
    assert 'return build_learning_answer_html(payload, answer_context="temporary_question")' in interruption
    assert "build_answer_media_html(payload)" not in interruption.split("def _build_graph_rag_answer_html", 1)[1].split("def ", 1)[0]


def test_homework_generator_and_explainer_emit_structured_learning_homework_html():
    generator = HOMEWORK_GENERATOR.read_text(encoding="utf-8")
    answer = HOMEWORK_ANSWER.read_text(encoding="utf-8")

    assert "def build_homework_assignment_html" in generator
    assert "learning-answer-content homework-answer-content" in generator
    assert "homework-assignment-card" in generator
    assert "homework-item-card" in generator
    assert "homework-rubric-list" in generator
    assert "tutor_content = build_homework_assignment_html(homework_items)" in generator

    assert "def build_homework_feedback_html" in answer
    assert "homework-feedback-card" in answer
    assert "homework-result-card" in answer
    assert "homework-score-badge" in answer
    assert "tutor_content = build_homework_feedback_html(results, score)" in answer
    assert "_format_explanation(results, score)" not in answer


def test_frontend_allows_and_styles_homework_learning_components_with_local_overflow():
    ui = UI_JS.read_text(encoding="utf-8")
    css = STYLES.read_text(encoding="utf-8")

    for marker in [
        "homework-answer-content",
        "homework-assignment-card",
        "homework-item-card",
        "homework-feedback-card",
        "homework-result-card",
        "homework-rubric-list",
        "homework-score-badge",
    ]:
        assert marker in ui
        assert marker in css

    assert "rawText.includes('homework-answer-content')" not in ui
    assert "allowLearningHtml: options.allowLearningHtml === true || options.kind === 'graph_rag_answer' || options.kind === 'homework_answer_prompt'" in ui
    assert "app.renderHomeworkAnswerCard" in ui
    assert "app.renderHomeworkAnswerCard?.(stateSnapshot.homework_items || [], stateSnapshot)" in ui
    assert "item.kind === 'homework_answer_prompt'" in ui
    assert "app.renderHomeworkAnswerCard?.(data.homework_items || data.items || stateSnapshot?.homework_items || [], data)" in ui
    assert ".homework-answer-viewport" in css
    assert "overflow-x: auto" in css
    assert ".msg-wrapper.agent .bubble-wrap:has(.homework-answer-content)" in css
    assert ".homework-answer-content" in css and "max-width: min(100%, 1040px)" in css
