from pathlib import Path


INDEX_HTML = Path("frontend/index.html")
STYLES = Path("frontend/assets/styles.css")
JS = Path("frontend/assets/js/error_correction.js")


def test_sidebar_exposes_error_correction_entry_and_modal():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "openErrorCorrectionPanel()" in html
    assert "题库加工" in html
    assert 'id="error-correction-overlay"' in html
    assert 'id="error-correction-file-input"' in html
    assert "openErrorCorrectionConfig()" in html
    assert 'data-config-section="error_correction"' in html
    assert '/assets/js/error_correction.js' in html
    assert 'id="paddleocr-config-block"' in html
    assert "focusPaddleOcrConfig()" in html
    assert "data-lib-filter=\"question_bank\"" in html
    assert "data-ec-tab=\"library\"" in html
    assert "runErrorCorrectionPipeline()" in html
    assert "clearQuestionBankFromWorkbench()" in html


def test_error_correction_script_registers_workbench_actions():
    script = JS.read_text(encoding="utf-8")

    assert "app.openErrorCorrectionPanel = openPanel;" in script
    assert "app.runErrorCorrectionOcr = runOcr;" in script
    assert "app.runErrorCorrectionSplit = runSplit;" in script
    assert "app.runErrorCorrectionPipeline = runPipeline;" in script
    assert "app.exportErrorCorrectionQuestions = saveQuestionsToLibrary;" in script
    assert "app.saveErrorCorrectionQuestionsToLibrary = saveQuestionsToLibrary;" in script
    assert "app.clearErrorCorrectionQuestionBank = clearQuestionBank;" in script
    assert "app.openErrorCorrectionConfig = openErrorCorrectionConfig;" in script
    assert "app.openLocalConfigPanel?.('error_correction');" in script
    assert "window.openErrorCorrectionPanel = () => app.openErrorCorrectionPanel();" in script
    assert "window.runErrorCorrectionPipeline = () => app.runErrorCorrectionPipeline();" in script
    assert "selected_page_indices" in script
    assert "selected_ids: Array.from(localState.selectedQuestionIds)" in script
    assert "renderQuestionBlocks(question, body);" in script
    assert "appendRenderedImage" in script
    assert "app.renderMath?.(block);" in script
    assert "openQuestionPreview(displayQuestion);" in script
    assert "error-correction-question-preview" in script
    assert "app.openErrorCorrectionQuestionPreview = openQuestionPreview;" in script


def test_config_script_keeps_error_correction_section_addressable():
    script = Path("frontend/assets/js/config.js").read_text(encoding="utf-8")

    assert "normalizeConfigSectionId" in script
    assert "error-correction" in script
    assert "error_correction" in script
    assert "bindLocalConfigSectionNav" in script
    assert 'document.getElementById(\'local-config-nav\')' in script
    assert "app.focusPaddleOcrConfig = function focusPaddleOcrConfig()" in script
    assert "window.focusPaddleOcrConfig = () => app.focusPaddleOcrConfig();" in script


def test_error_correction_styles_reuse_main_visual_language():
    styles = STYLES.read_text(encoding="utf-8")

    assert "Error Correction Workbench" in styles
    assert ".error-workbench-panel" in styles
    assert ".error-workbench-chip-row" in styles
    assert ".error-workbench-question-card" in styles
    assert ".error-workbench-page-card" in styles
    assert "#config-overlay" in styles
    assert ".error-workbench-image" in styles
    assert ".error-workbench-answer-card" in styles
    assert ".error-workbench-question-card--clickable" in styles
    assert ".error-workbench-preview-content" in styles


def test_library_script_supports_question_bank_view():
    script = Path("frontend/assets/js/knowledge.js").read_text(encoding="utf-8")

    assert "questionBankItems" in script
    assert "fetchQuestionBankItems" in script
    assert "question_bank" in script
    assert "renderQuestionBankCard" in script
    assert "待补充知识板块" in script


def test_app_bootstrap_refreshes_question_bank_items():
    script = Path("frontend/assets/app.js").read_text(encoding="utf-8")

    assert "app.fetchQuestionBankItems?.();" in script
