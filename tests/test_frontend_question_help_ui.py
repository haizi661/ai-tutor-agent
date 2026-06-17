from pathlib import Path


INDEX_HTML = Path("frontend/index.html")
QUESTION_HELP_JS = Path("frontend/assets/js/question-help.js")
CONFIG_JS = Path("frontend/assets/js/config.js")
STYLES = Path("frontend/assets/styles.css")


def test_question_help_sidebar_button_modal_and_script_contract():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="open-question-help-btn"' in html
    assert 'onclick="openQuestionHelpModal()"' in html
    assert 'aria-controls="question-help-modal"' in html
    assert 'aria-haspopup="dialog"' in html
    assert ">题目答疑<" in html
    assert 'id="question-help-modal"' in html
    assert 'class="unified-dialog unified-dialog--question-help"' in html
    assert 'id="question-help-text"' in html
    assert 'id="question-help-images"' in html
    assert 'id="question-help-records"' in html
    assert 'id="question-help-model-select"' in html
    assert 'qwen-vl-max' in html
    assert '/assets/js/question-help.js' in html


def test_question_help_modal_prioritizes_current_answer_workspace():
    html = INDEX_HTML.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert 'id="question-help-answer-mode"' in html
    assert ">快速解答<" in html
    assert ">深度解析<" in html
    assert ">图片题专用<" in html
    assert 'id="question-help-current"' in html
    assert 'id="question-help-current-body"' in html
    assert 'id="question-help-current-empty"' in html
    assert ">当前解答<" in html
    assert ">最近解答<" in html
    assert ".qh-workspace" in styles
    assert ".qh-current-answer" in styles
    assert ".qh-current-body" in styles
    assert ".qh-history--recent" in styles


def test_question_help_js_submits_text_images_and_keeps_history():
    js = QUESTION_HELP_JS.read_text(encoding="utf-8")

    assert "window.QuestionHelp = QuestionHelp" in js
    assert "state.studentId || state.student_id || 'default_student'" in js
    assert "FormData" in js
    assert "question_text" in js
    assert "images" in js
    assert "/question-help" in js
    assert "current_node_id" in js
    assert "current_node_name" in js
    assert "answer_mode" in js
    assert "_renderCurrentPending" in js
    assert "_renderCurrentRecord" in js
    assert "_emphasizeAnswerSections" in js
    assert "marked" in js
    assert "_fetchAndRenderRecords" in js
    assert "_renderRecords" in js
    assert "_readErrorDetail" in js
    assert "解答记录" in js
    assert "qh-record-header" in js
    assert "qh-record-node-tag" in js
    assert "qh-toggle-btn" in js


def test_question_help_answers_use_shared_markdown_sanitizer_and_math_renderer():
    js = QUESTION_HELP_JS.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert "app.renderMarkdownContent?.(answer, answerText" in js
    assert "allowLearningHtml: true" in js
    assert "app.renderMath?.(answer)" in js
    assert "marked.parse(answerText)" not in js
    assert ".qh-answer .katex-display" in styles
    assert ".qh-answer .katex" in styles


def test_question_help_record_separates_question_and_answer_for_review():
    js = QUESTION_HELP_JS.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert "qh-question-panel" in js
    assert "qh-question-label" in js
    assert "qh-answer-shell" in js
    assert "qh-answer-head" in js
    assert "qh-answer-kicker" in js
    assert "考点 · 步骤 · 答案 · 易错提醒" in js
    assert ".qh-question-panel" in styles
    assert ".qh-answer-shell" in styles
    assert ".qh-answer-head" in styles
    assert ".qh-answer h2" in styles
    assert ".qh-answer h3" in styles
    assert "qh-answer-heading--final" in js
    assert "qh-answer-final-block" in js
    assert ".qh-answer-heading--final" in styles
    assert ".qh-answer-final-block" in styles
    assert ".qh-answer table" in styles
    assert "display: block;" in styles


def test_question_help_styles_match_compact_modal_layout():
    styles = STYLES.read_text(encoding="utf-8")

    assert ".unified-dialog--question-help" in styles
    assert ".question-help-layout" in styles
    assert ".qh-composer" in styles
    assert ".qh-record-list" in styles
    assert ".qh-answer" in styles
    assert ".qh-record-header" in styles
    assert ".qh-record-node-tag" in styles
    assert ".qh-toggle-btn" in styles
    assert ".qh-record--collapsible" in styles
    assert ".qh-record--collapsed" in styles


def test_local_config_saves_independent_question_help_model():
    js = CONFIG_JS.read_text(encoding="utf-8")

    assert "question_help_model_name" in js
    assert "question-help-model-select" in js
