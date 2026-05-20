# AI Tutor Agent Agent Guide

Last synced: 2026-05-01

This project is a Web-first adaptive tutoring agent for automatic control theory. The active learning loop is graph-node mastery learning, not a generic one-shot chat flow.

## Read First

Use these as the current source of truth:

1. `README.md` for setup, launch, network policy, and user workflow.
2. `docs/current-status-and-usage.md` for current capabilities and known gaps.
3. `docs/next-iteration-plan.md` for the next engineering priorities.
4. `docs/knowledge-map-runtime-assets.md` for graph/runtime asset rules.
5. `docs/plans/2026-04-30-interaction-artifact-validation-contract.md` for interaction card/history restore validation.

Files under `docs/reports/`, `docs/plans/2026-04-27-*`, and `docs/plans/2026-04-28-*` are historical unless a current document points to them.

## Runtime Rules

- Use port `8000` for the local Web UI. If it is occupied by an old project process, stop the old process instead of silently moving the app to another port.
- Primary launch command is `python main.py`, then check `http://127.0.0.1:8000/api/health`.
- The project is path-relative. Keep docs and code examples in `data/...`, `docs/...`, `frontend/...`; do not add machine-specific absolute paths.
- Do not commit `.env`, `.codex`, `.hermes/`, `data/chroma_db/**`, `data/student_states/*.json`, `data/tutor_memory.db`, or local vector/cache state.

## Active Architecture

- `ai_tutor_agent/core/` holds state, events, and ports.
- `ai_tutor_agent/nodes/` holds LangGraph node behavior.
- `ai_tutor_agent/orchestration/` wires the graph.
- `ai_tutor_agent/application/` coordinates sessions and persistence.
- `ai_tutor_agent/infrastructure/` holds LLM, retriever, question bank, and storage adapters.
- `ai_tutor_agent/interfaces/api/` is the Web API surface.
- `frontend/` renders chat, interaction cards, history restore, and settings.
- `tests/` contains the regression contract.

The current main flow is:

```text
topic confirmation
-> assessment
-> initial graph node selection
-> node content loading
-> tutor lesson
-> post-lesson pause
-> free-form temporary question or objective test
-> remediation or next node planning
-> continue next node or generate homework
-> homework restore/answer/review on later sessions
```

## Knowledge Graph And Assets

- Active course graph is the 2026-04-27 Graph B runtime asset set in `data/knowledge_map_outputs/`, `data/mineru_cache/`, and `data/media_evidence_index/`.
- Historical Graph A / A2 material lives under `docs/archive/a2-control-theory/` and must not be treated as the active course graph.
- `data/question_bank/a2-control-theory/assessment_questions.jsonl` is the only minimal local question-bank asset currently present. Objective, variant, and homework question-bank content still needs expansion.

## Learner Profile And Student State

- Initial learner profiling is generated in `ai_tutor_agent/nodes/assessment.py`: assessment answers become `assessment_concept_gaps`, `assessment_radar`, `difficulty_level`, `teaching_strategy`, and the initial `user_knowledge_graph`.
- Long-running learning state is stored by `StudentStateStore` in `data/student_states/*.json`: current node, `mastery_scores`, visited/wrong nodes, question attempts, homework assignments, homework history, daily records, last learning time, and `knowledge_graph` (per-node scores, wrong questions, evidence).
- User knowledge graph (`StudentState.knowledge_graph`): starts empty, nodes added only when the user starts learning them. Each node tracks `score` (0-100), `status` (in_progress/mastered), `wrong_questions` (capped 100), `evidence` (capped 50, quiz_pass/fail/homework_pass/fail), and `attempts`. Evidence is the single source of truth for mastery decisions — no separate global `evidence_events` log. API: `GET /api/students/{student_id}/knowledge-graph`.
- Treat the current learner model as a lightweight JSON prototype, not a production-grade learner profile. Do not overstate it as a fully calibrated long-term model.
- Current gaps to preserve in plans: paired self-evaluation/objective calibration must be strengthened, mastery score scale must be normalized, and initial node selection should use profile signals while still respecting graph prerequisites.

## Network Policy

- `GRAPH_RAG_ENABLE_LLM` defaults to true. Startup commands may override `.env` values.
- Shell/process environment takes precedence over persisted `.env` proxy values.
- Smart proxy behavior: foreign APIs go through the configured proxy; localhost, domestic model providers, MinerU/OpenXLab, `hf-mirror.com`, ModelScope, and common PyPI/npm mirrors are merged into `NO_PROXY` for direct access.
- HuggingFace embedding download falls back to `HF_MIRROR_ENDPOINT`, defaulting to `https://hf-mirror.com`, when the default endpoint is unavailable.
- Use `bash scripts/setup_cn_mirrors.sh` or the README pip/npm mirror commands for China mainland dependency setup.

## Frontend And HTML Safety

- Learning/homework/GraphRAG HTML must pass through the allowlist sanitizer in `frontend/assets/js/ui.js`.
- Do not restore the old pattern where `rawText.includes(...)` decides that arbitrary text is trusted HTML.
- Dynamic question text, IDs, and prompts must be inserted with DOM APIs such as `textContent` and `dataset`, not direct string interpolation into `innerHTML`.
- Formula/table/figure content belongs inside `learning-*` viewports so long formulas and wide tables scroll inside their own containers instead of expanding the chat bubble.
- GraphRAG learning answers should be user-facing evidence cards, not debug dumps: keep raw asset ids, long hashes, raw LaTeX, and raw HTML tables hidden or folded by default; show figure thumbnails when `image_paths_abs` resolves and a clear unavailable placeholder when it does not.
- GraphRAG learning answers must keep media tied to the prose that cites it. Referenced formulas, figures, and tables belong in the same `learning-reference-block` as the explanation; unreferenced related media is only a compact supplement and is limited to 3 cards. Frontend restore also normalizes old saved HTML with the same de-noising rule.

## Session And Homework Invariants

- New, refresh, and history restore must not lose assigned/deferred/in-progress homework.
- Frontend “新对话” first calls `POST /api/sessions` to create an empty checkpoint before the first user message; keep that route idempotent because history restore depends on it.
- Restoring a session without a new topic must reuse the existing topic and pending homework state; it must not force topic re-confirmation.
- Restoring a session must sync the header title/current node from the checkpoint and scroll the current pending card into view after media layout stabilizes. The composer must not occlude the pending card.
- Historical interaction cards must render as locked once answered/submitted/skipped/reviewed, except the one current pending interaction.
- Current active `pending_interaction_kind` values include `post_lesson_choice`, `temporary_question`, `objective_test_answers`, `variant_test_answers`, `continue_or_homework_choice`, `homework_review_choice`, `homework_answers`, and `consolidation_choice`.
- `post_lesson_choice` is a natural pause: users may type a free-form stuck point directly, choose `temporary_question` via "继续追问", or choose `start_test` via "我懂了，进入小测". Do not revert it to a rigid "temporary question / start test" copy.

## History Display Title

- Sidebar history titles use `_checkpoint_summary` in `interfaces/api/history.py`. Fallback chain: `custom_title` → `proposed_topic` → `current_topic` → first user message (truncated 30 chars) → `"新对话"`. Never display raw `thread_id` UUID.
- `stateLabel` and `historyState` in `frontend/assets/js/history.js` are based on `flow_status` field, not title text matching.

## Session Resume

- `_has_homework` in `session_resume_router.py` uses blacklist mode: terminal statuses (completed/submitted/deferred) are excluded; missing/unknown status defaults to active homework when items exist.
- `infer_learning_phase` in `learning_flow.py` merges all homework-related flow statuses into a single set to avoid dead-code branches.

## Testing

Use plugin autoload disabling for local pytest runs:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

For API smoke tests, prefer the local `tests/asgi_test_client.py` helper. It avoids the Starlette `TestClient` blocking-portal hang observed in the Python 3.9 environment while still exercising the ASGI request path through `httpx.ASGITransport`.

Before claiming a UI/history restore task is complete, run the relevant backend tests, frontend contract tests, and at least one browser or app health check. Passing a local string-contract test alone is not enough for interaction-card completion.

2026-05-01 UI restore and GraphRAG display validation passed with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
# 450 passed, 5 warnings
```

Browser checks confirmed restored `awaiting_post_lesson_choice` sessions show the correct title/node/status, focus the post-lesson card, avoid composer overlap, keep page-level horizontal overflow at 0, and limit restored related media to 3 cards with no duplicate media keys.
