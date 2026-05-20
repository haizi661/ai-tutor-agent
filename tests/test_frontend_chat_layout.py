from pathlib import Path


STYLES = Path("frontend/assets/styles.css")
UI_JS = Path("frontend/assets/js/ui.js")
HISTORY_JS = Path("frontend/assets/js/history.js")


def test_main_chat_lane_uses_available_width_and_hides_horizontal_overflow():
    styles = STYLES.read_text(encoding="utf-8")

    assert "/* Main conversation width and overflow correction" in styles
    assert ".chat-main,\n.messages,\n.chat-area {\n    overflow-x: hidden !important;" in styles
    assert "width: min(100%, 1040px) !important;" in styles
    assert "width: min(100%, 920px) !important;" in styles
    assert "max-width: calc(100vw - 272px - 48px);" in styles
    assert ".chat-main--conversation .chat-locator" in styles
    assert "max-width: none !important;" in styles


def test_restored_sessions_focus_current_interaction_and_keep_composer_compact():
    styles = STYLES.read_text(encoding="utf-8")
    ui = UI_JS.read_text(encoding="utf-8")
    history = HISTORY_JS.read_text(encoding="utf-8")

    assert "app.focusRestoredSessionPosition" in ui
    assert "restoredInteractionSelector" in ui
    assert "awaiting_post_lesson_choice: 'post_lesson_choice'" in ui
    assert "container.scrollTop + targetRect.top - containerRect.top - 16" in ui
    assert "window.setTimeout(scrollToTarget, 150)" in ui
    assert "window.setTimeout(scrollToTarget, 500)" in ui
    assert "window.setTimeout(scrollToTarget, 1200)" in ui
    assert "window.setTimeout(scrollToTarget, 1800)" in ui
    assert "app.focusRestoredSessionPosition?.(data.state || {})" in history

    assert ".chat-main--conversation .input-sticky" in styles
    assert ".chat-main--conversation .composer-shell" in styles
    assert ".chat-main--conversation .chat-textarea" in styles
    assert "min-height: 36px;" in styles
    assert "max-height: 128px;" in styles
