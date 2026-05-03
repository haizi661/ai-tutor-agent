from pathlib import Path


UI_JS = Path("frontend/assets/js/ui.js")
SESSION_JS = Path("frontend/assets/js/session.js")
STYLES = Path("frontend/assets/styles.css")


def test_main_learning_answer_html_is_supported_without_graphrag_debug_role():
    ui_content = UI_JS.read_text(encoding="utf-8")
    session_content = SESSION_JS.read_text(encoding="utf-8")

    assert "allowLearningHtml" in ui_content
    assert "sanitizeLearningHtml" in ui_content
    assert "learning-answer-content" in ui_content
    assert "learning-reference-block" in ui_content
    assert "learning-media-ref" in ui_content
    assert "learning-evidence-card--formula" in ui_content
    assert "learning-evidence-card--figure" in ui_content
    assert "learning-debug-details" in ui_content
    assert "learning-formula-card" in ui_content
    assert "learning-inline-formula-card" in ui_content
    assert "learning-figure-card" in ui_content
    assert "learning-table-card" in ui_content
    assert "learning-derivation-card" in ui_content

    render_start = ui_content.index("function renderMarkdown")
    render_end = ui_content.index("function extractGraphRagReportBody", render_start)
    render_body = ui_content[render_start:render_end]
    assert "allowLearningHtml" in render_body
    assert "sanitizeLearningHtml" in render_body
    assert "extractGraphRagReportBody" in render_body
    assert "if (kind === 'graph_rag_answer') return 'graph_rag_answer';" in ui_content
    assert "streamKind === 'graph_rag_answer'" in session_content


def test_learning_content_components_have_readable_width_and_local_overflow_only():
    styles = STYLES.read_text(encoding="utf-8")

    assert "/* Main learning answer content components */" in styles
    assert ".learning-answer-content" in styles
    assert "max-width: min(100%, 1040px);" in styles
    assert "overflow-x: hidden;" in styles
    assert ".learning-media-ref" in styles
    assert ".learning-evidence-type" in styles
    assert ".learning-source-line" in styles
    assert ".learning-debug-details" in styles
    assert ".learning-figure-unavailable" in styles

    for selector in [
        ".learning-formula-card",
        ".learning-figure-card",
        ".learning-table-card",
        ".learning-derivation-card",
    ]:
        assert selector in styles

    for selector in [
        ".learning-formula-viewport",
        ".learning-table-viewport",
        ".learning-code-viewport",
    ]:
        assert selector in styles

    assert "overflow-x: auto;" in styles
    assert "max-width: 100%;" in styles
    assert "width: max-content;" in styles
    assert "object-fit: contain;" in styles
    assert "max-height: min(70vh, 560px);" in styles
    assert "position: sticky;" in styles
    assert "white-space: nowrap;" in styles
    assert "scrollbar-gutter: stable;" in styles
    assert "overscroll-behavior-x: contain;" in styles
    assert ".learning-reference-block" in styles
    assert ".learning-answer-content .learning-formula-card" in styles
    assert ".learning-media-group" in styles
    assert "grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr));" in styles
    assert ".learning-media-group > .learning-formula-card" in styles
    assert "overflow-wrap: anywhere;" in styles
    assert "word-break: break-word;" in styles
    assert ".msg-wrapper.agent .bubble-wrap" in styles
    assert ".msg-wrapper.agent .agent-turn" in styles
    assert ".msg-wrapper.agent .agent-body" in styles
    assert ".msg-wrapper.agent .bubble-wrap:has(.learning-answer-content)" in styles
    assert "min-width: 0 !important;" in styles
    assert "width: 100% !important;" in styles
    assert "box-sizing: border-box;" in styles


def test_frontend_limits_restored_related_media_overview_noise():
    ui_content = UI_JS.read_text(encoding="utf-8")

    assert "normalizeLearningRelatedOverview(target)" in ui_content
    assert "root.querySelectorAll?.('.learning-related-overview')" in ui_content
    assert "kept >= 3" in ui_content
    assert "seen.has(key)" in ui_content


def test_learning_evidence_cards_hide_debug_details_and_keep_local_overflow_contract():
    styles = STYLES.read_text(encoding="utf-8")
    ui_content = UI_JS.read_text(encoding="utf-8")

    sanitizer = ui_content.split("function sanitizeLearningHtml", 1)[1].split("function extractGraphRagReportBody", 1)[0]
    for class_name in [
        "learning-evidence-card--formula",
        "learning-evidence-card--figure",
        "learning-evidence-card--table",
        "learning-evidence-type",
        "learning-source-line",
        "learning-debug-details",
        "learning-latex-details",
        "learning-figure-unavailable",
    ]:
        assert class_name in sanitizer

    assert ".learning-debug-details summary" in styles
    assert ".learning-latex-details pre" in styles
    assert "overflow-x: auto;" in styles
    assert ".learning-figure-unavailable" in styles
    assert "border: 1px dashed" in styles
    assert "text-align: center;" in styles


def test_temporary_question_entry_uses_freeform_coaching_not_rigid_option_copy():
    ui_content = UI_JS.read_text(encoding="utf-8")
    session_content = SESSION_JS.read_text(encoding="utf-8")

    render_start = ui_content.index("app.renderPostLessonChoice = function renderPostLessonChoice")
    render_end = ui_content.index("app.renderContinueOrHomeworkChoice", render_start)
    render_body = ui_content[render_start:render_end]

    assert "接下来做什么" not in render_body
    assert "选一个继续。" not in render_body
    assert "还有哪里卡住？" in render_body
    assert "可以直接打一整句问题" in render_body
    assert "继续追问" in render_body
    assert "我懂了，进入小测" in render_body
    for marker in [
        "if (payload.interaction_kind === 'post_lesson_choice')",
        "if (endKind === 'post_lesson_choice')",
    ]:
        start = session_content.index(marker)
        end = session_content.index("return;", start)
        branch = session_content[start:end]
        assert "比如：为什么这里要看符号？/ 能不能换个例子？" in branch
        assert "也可以直接输入选项" not in branch


def test_learning_viewer_modal_and_copy_actions_are_available():
    styles = STYLES.read_text(encoding="utf-8")
    ui_content = UI_JS.read_text(encoding="utf-8")

    assert "openLearningViewer" in ui_content
    assert "closeLearningViewer" in ui_content
    assert "copyLearningBlock" in ui_content
    assert "updateFormulaViewportOverflow" in ui_content
    assert ".formula-scroll, .learning-formula-viewport" in ui_content
    assert "learning-viewer-overlay" in ui_content
    assert "learning-viewer-body" in ui_content
    assert "navigator.clipboard.writeText" in ui_content

    assert ".learning-viewer-overlay" in styles
    assert ".learning-viewer-panel" in styles
    assert ".learning-viewer-body" in styles
    assert "max-width: min(1120px, calc(100vw - 48px));" in styles
    assert "max-height: min(86vh, 760px);" in styles
    assert "overflow: auto;" in styles


def test_existing_graphrag_debug_media_contract_is_not_removed():
    styles = STYLES.read_text(encoding="utf-8")
    ui_content = UI_JS.read_text(encoding="utf-8")

    assert 'data-role="graph_rag_debug_report"' in styles
    assert "answer-media-block" in styles
    assert "media-card" in styles
    assert "allowGraphRagHtml: options.allowGraphRagHtml === true" in ui_content
    assert "allowGraphRagHtml" in ui_content
