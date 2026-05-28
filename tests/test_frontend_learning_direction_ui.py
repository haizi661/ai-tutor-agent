from pathlib import Path


AI_PATH_JS = Path("frontend/assets/js/ai_path.js")
STATE_JS = Path("frontend/assets/js/state.js")
UI_JS = Path("frontend/assets/js/ui.js")
HISTORY_JS = Path("frontend/assets/js/history.js")
STYLES = Path("frontend/assets/styles.css")


def test_learning_direction_is_locked_and_persisted_from_course_choice_card():
    content = AI_PATH_JS.read_text(encoding="utf-8")

    assert "/learning-direction" in content
    assert "learningTrackLocked" in content
    assert "lockVisibleCourseChoiceCard" in content
    assert "selectLearningDirection('control_theory')" in content
    assert "selectLearningDirection('artificial_intelligence')" in content
    assert "inferLearningTrackFromText" in content


def test_learning_direction_restores_from_history_snapshot():
    state_content = STATE_JS.read_text(encoding="utf-8")
    ui_content = UI_JS.read_text(encoding="utf-8")
    history_content = HISTORY_JS.read_text(encoding="utf-8")

    assert "learningTrack: ''" in state_content
    assert "learningTrackLabel: ''" in state_content
    assert "learningTrackLocked: false" in state_content
    assert "item.kind === 'course_choice_card'" in ui_content
    assert "item.kind === 'course_choice_selection'" in ui_content
    assert "app.renderCourseChoiceCard" in ui_content
    assert "stateSnapshot.learning_track" in ui_content
    assert "app.applyLearningDirectionFromState?.(data.state || {})" in history_content


def test_learning_direction_locked_card_has_dedicated_styles():
    styles = STYLES.read_text(encoding="utf-8")

    assert ".course-choice-card.is-locked" in styles
    assert ".course-choice-locked" in styles
