from pathlib import Path


UI_JS = Path("frontend/assets/js/ui.js")


def test_learning_html_trust_requires_explicit_options_not_marker_sniffing():
    ui = UI_JS.read_text(encoding="utf-8")
    render_markdown = ui.split("function renderMarkdown", 1)[1].split("function sanitizeLearningHtml", 1)[0]

    assert "rawText.includes('learning-answer-content')" not in render_markdown
    assert "rawText.includes('homework-answer-content')" not in render_markdown
    assert "rawText.includes('media-card')" not in render_markdown
    assert "options.allowLearningHtml === true" in render_markdown
    assert "options.allowGraphRagHtml === true" in render_markdown


def test_learning_html_sanitizer_uses_tag_and_attribute_allowlists():
    ui = UI_JS.read_text(encoding="utf-8")
    sanitizer = ui.split("function sanitizeLearningHtml", 1)[1].split("function extractGraphRagReportBody", 1)[0]

    assert "allowedTags" in sanitizer
    assert "allowedAttributes" in sanitizer
    assert "node.removeAttribute(attr.name)" in sanitizer
    for dangerous in ["script", "iframe", "svg", "math", "form", "input"]:
        assert f"'{dangerous}'" not in sanitizer.split("allowedTags", 1)[1].split("];", 1)[0]
    for dangerous_attr in ["style", "srcdoc", "formaction", "xlink:href"]:
        assert f"'{dangerous_attr}'" not in sanitizer.split("allowedAttributes", 1)[1].split("];", 1)[0]
    assert "'data-learning-action'" in sanitizer.split("allowedAttributes", 1)[1].split("];", 1)[0]


def test_learning_html_actions_use_event_delegation_not_inline_onclick():
    ui = UI_JS.read_text(encoding="utf-8")

    assert "[data-learning-action]" in ui
    assert "dataset.learningAction" in ui
    assert "window.openLearningViewer?.(block)" in ui
    assert "window.copyLearningBlock?.(block)" in ui
    assert "catch (_error)" in ui


def test_marked_output_is_sanitized_for_plain_user_and_system_messages():
    ui = UI_JS.read_text(encoding="utf-8")

    assert "function sanitizeRenderedHtml" in ui
    assert "sanitizeRenderedHtml(marked.parse(rawText))" in ui
    assert "bubble.innerHTML = sanitizeRenderedHtml(marked.parse(text));" in ui
    assert "${sanitizeRenderedHtml(marked.parse(text))}" in ui


def test_homework_answer_card_does_not_interpolate_prompt_or_qid_into_inner_html():
    ui = UI_JS.read_text(encoding="utf-8")
    card_fn = ui.split("app.renderHomeworkAnswerCard = function renderHomeworkAnswerCard", 1)[1].split("app.renderObjectiveTestCard", 1)[0]

    assert "field.innerHTML" not in card_fn
    assert "${item.prompt" not in card_fn
    assert "data-qid=\"${qid}\"" not in card_fn
    assert ".textContent = `${idx + 1}. ${promptText}`" in card_fn
    assert "textarea.dataset.qid = qid" in card_fn
    assert "textarea.placeholder = `填写 ${qid} 的答案`" in card_fn
