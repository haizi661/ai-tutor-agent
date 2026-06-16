# Interaction Artifact Validation Contract

Last synced: 2026-06-09

This document is the commit-tracked version of the interaction-card validation rules. It replaces references to the ignored `.hermes/` plan path for project handoff and GitHub-visible documentation.

## Goal

Prove that the tutoring UI, backend checkpoint state, and restored history timeline agree about interaction cards.

Passing one focused unit test is not enough. A change can be called complete only when the structure, restore path, and visible browser behavior all satisfy the contract below.

## Artifact Lifecycle

Every interaction artifact must be in one of these states:

```text
pending      current user action is required
submitted    user submitted answers and scoring/review is pending or present
skipped      user skipped the interaction
answered     user chose an option
reviewed     feedback/review has been shown
locked       historical display only; no action can be triggered
```

History restore rule:

```text
Only the current unresolved interaction may be pending.
All earlier resolved cards must be locked or rendered as a non-interactive summary.
The current pending card must be scrolled into view after rich media layout stabilizes.
```

## Timeline Data Requirements

History items representing interaction cards must carry enough data for deterministic rendering:

```python
{
    "role": "agent",
    "kind": "...",
    "content": "...",
    "data": {
        "interaction_kind": "...",
        "status": "pending|submitted|skipped|answered|reviewed|locked",
        "locked": True,
        "selectedValue": "...",
        "selectedLabel": "...",
        "answers": {...},
        "result": {...},
        "statusText": "..."
    }
}
```

The frontend must not infer historical lock state only from `flow_status`.

## Covered Artifact Kinds

These kinds must be kept in the restore contract:

- `topic_confirmation_card`
- `assessment_form`
- `post_lesson_choice_card`
- `objective_test_card`
- `objective_quiz_review`
- `variant_test_card`
- `continue_or_homework_choice_card`
- `homework_review_choice_card`
- `homework_answer_card`
- `homework_feedback_card`
- `consolidation_choice_card`

Legacy `next_step_selector` and `post_eval_selector` may still appear in old histories, but new graph-node learning work should prefer the current `pending_interaction_kind` names documented in `AGENTS.md`.

## Backend Checks

Backend history reconstruction must preserve:

1. Card -> user action -> review/feedback -> next teaching message order.
2. Objective quiz review must remain visible when wrong-question explanations are appended.
3. A resolved choice card must not reappear as a second open pending card.
4. Homework states `assigned`, `deferred`, and `in_progress` must survive new session creation, refresh, and history restore.

Relevant tests:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_history.py \
  tests/test_session.py \
  tests/test_session_persistence.py \
  tests/test_session_resume_router_node.py
```

## Frontend Checks

Frontend renderers must preserve:

1. `locked=true` disables buttons, inputs, and submit controls.
2. Restored selected labels or answers stay visible.
3. Follow-up assistant messages append to the timeline; they must not replace review cards.
4. Long formulas and wide tables remain inside local scroll viewports.
5. Learning/homework HTML is sanitized with tag/attribute allowlists before entering `innerHTML`.
6. Restored GraphRAG learning answers keep prose-cited media bound near the prose and limit unreferenced related media to 3 cards.
7. The composer must not overlap or hide the current pending card after restore.

Relevant tests:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_frontend_objective_test_ui.py \
  tests/test_frontend_chat_layout.py \
  tests/test_frontend_learning_content_layout.py \
  tests/test_frontend_html_safety.py \
  tests/test_homework_learning_ui_contract.py
```

## Browser/API Acceptance

Before reporting UI structure as complete, validate at least these flows through a running app or equivalent API smoke:

1. Start a new topic, reach lesson, use the follow-up question path, then return to post-lesson choice.
2. Submit an objective test with at least one wrong answer; confirm the quiz review remains above wrong-question explanations after refresh/history restore.
3. Choose continue/homework, generate homework, refresh or reopen history, and confirm the previous choice card is locked.
4. Restore a session with existing homework and confirm it does not ask to confirm the topic again.

Health check:

```bash
python main.py
curl http://127.0.0.1:8000/api/health
```

2026-05-01 browser acceptance sample:

- Restored `awaiting_post_lesson_choice` history showed the correct topic title, graph node, status text, and post-lesson choice card.
- After media layout settled, the current pending card was visible and did not overlap the composer.
- Page-level horizontal overflow was absent; wide table overflow stayed inside `learning-table-viewport`.
- Restored legacy GraphRAG related overview had 3 cards and 0 duplicate media keys.
- Full regression at that point: `424 passed, 5 warnings`.
- 2026-06-09 current full suite: `743 passed, 5 skipped, 5 warnings`.
