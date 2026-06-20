# AI Tutor Agent Guide

Last synced: 2026-06-21 (全面项目整理 + 子模块文档补齐)

This is a Web-first adaptive tutor for automatic control theory. The active product loop is graph-node mastery learning, not the older generic `Tutor -> Tester -> Evaluator` chat flow.

## Highest-value sources

- Start with `README.md`, then `docs/learning-path-complete-flow.md`, `docs/current-status-and-usage.md`, `docs/next-iteration-plan.md`, `docs/knowledge-map-runtime-assets.md`, and `docs/plans/2026-04-30-interaction-artifact-validation-contract.md`.
- Treat `docs/reports/`, `docs/plans/2026-04-27-*`, and `docs/plans/2026-04-28-*` as historical unless a current doc points to them.
- `CLAUDE.md` intentionally delegates project guidance back to this file.

## Setup, run, and verify

- Python target is `>=3.9`; install with `python -m pip install -r requirements.txt` or `python -m pip install -e .`.
- Main Web entrypoint: `python main.py`; CLI compatibility entrypoint: `python main.py --cli`.
- Web UI always uses port `8000`; `AI_TUTOR_HOST` only changes bind host. If `8000` is occupied, stop the old process instead of choosing another port.
- Health check after launch: `http://127.0.0.1:8000/api/health`.
- Local pytest should disable unrelated plugin autoloading: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`. A single test can be run as `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_name.py`.
- For API smoke tests, prefer `tests/asgi_test_client.py` over Starlette `TestClient`; the latter has caused blocking-portal hangs in the Python 3.9 environment.
- Frontend has no bundler pipeline; `package.json` pins `marked` and `katex`, with local vendor files under `frontend/assets/vendor/marked/` and `frontend/assets/vendor/katex/`. Browser code is served directly from `frontend/`.
- Retrieval regression command lives in README: `python scripts/evaluate_retrieval.py --eval-file data/retrieval_eval/sample_eval.jsonl --k-values 1,3,5 --recall-k 12 --output data/retrieval_eval/latest_report.json`.
- Demo recording: `python scripts/record_demo_flow.py` (headless Chromium, requires Playwright; verified 9-node complete flow + new plan generation). Phase-by-phase recording: `python scripts/record_phases_v2.py` (single session, timestamp-based 8-phase split). Output: `scripts/phase_recordings/` (7 videos + `PHASE_VIDEOS.md` mapping). API E2E: `python scripts/real_e2e_verify.py`. Question bank generation: `python scripts/gen_objective_bank.py` and `python scripts/gen_variant_bank.py`.

## Architecture that matters

- `main.py` dispatches to `ai_tutor_agent/interfaces/api/app.py`; FastAPI mounts API routers and static `frontend/` at `/`.
- LangGraph wiring is in `ai_tutor_agent/orchestration/workflow.py`; add new teaching steps in `ai_tutor_agent/nodes/` first, then wire them there.
- Core boundaries: `core/` state/events/ports, `application/` session coordination, `infrastructure/` LLM/RAG/storage/adapters, `interfaces/api/` Web API, `frontend/` chat/cards/history/settings.
- **New co-existing modules** (from branch integration 2026-06-16):
  - `backend/` — Flask API + LangChain agents (error_correction, note, solve, teach) + SQLAlchemy DB + PaddleOCR + benchmark. Separate service, not wired into main LangGraph workflow. Entry: `backend/web_app.py`.
  - `ai_tutor_agent/ai_learning_path/` — AI course learning path module (routes, service, course asset builder). Supports dual-course mode: auto_control / artificial_intelligence.
  - `kg_builder_standalone/` — Standalone knowledge graph construction pipeline with demo outputs (v1-v9 evolution).
  - `ai_tutor_agent/interfaces/api/auth.py` — Account registration/login (PBKDF2 password hashing, token auth).
  - `ai_tutor_agent/infrastructure/matlab_experiment.py` — MATLAB simulation engine (natural language → MATLAB code → execution → result analysis).
- Current main flow: topic confirmation → assessment → learning plan generation → initial graph node selection → node content loading → tutor lesson (or quick_check choice) → post-lesson pause → temporary question or objective test → remediation or next node planning → continue next node / consolidate weak / view report / homework → completion wrapup when all nodes mastered → later homework/session restore.
- Legacy nodes such as `tester`, `evaluator`, `coach`, `next_step_selector`, and `post_eval_selector` still exist for compatibility; do not make them the target path for new graph-node learning work.

## Runtime assets and local state

- Active course graph is Graph B from 2026-04-27: `data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv`, `..._edges.csv`, `..._v2.json`, plus `data/mineru_cache/` and `data/media_evidence_index/`.
- Historical Graph A/A2 assets are no longer kept in this repo; never treat any legacy `graph.json` / `notes.jsonl` (including those under `docs/archive/a2-control-theory/`) as the current teaching graph. The only authoritative teaching graph is Graph B under `data/knowledge_map_outputs/auto_control_knowledge_map_v2_*.{csv,json}`.
- If graph/media assets are missing, use `scripts/sync_knowledge_map_runtime_assets.sh`, then check `python -m ai_tutor_agent.knowledge_map.runtime_assets --media-index data/media_evidence_index` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_graph_integrity.py`.
- Keep paths repo-relative (`data/...`, `docs/...`, `frontend/...`); do not add machine-specific absolute paths.
- Do not commit `.env`, `.codex`, `.hermes/`, `data/chroma_db/**`, `data/student_states/*.json`, `data/tutor_memory.db`, vector DBs, local caches, or uploaded/private learner data.
- `data/question_bank/a2-control-theory/` contains 640 total questions: 10 assessment, 420 objective (42×10), 210 variant (42×5), and 3 homework. Objective and variant banks are complete; homework bank is still minimal.

## Learner state and mastery rules

- Initial learner profiling is generated in `ai_tutor_agent/nodes/assessment.py` as `assessment_concept_gaps`, `assessment_radar`, `difficulty_level`, `teaching_strategy`, and initial `user_knowledge_graph`.
- Long-running state is persisted by `StudentStateStore` in `data/student_states/*.json`.
- `StudentState.knowledge_graph` starts empty and adds nodes only when learning begins. Each node tracks `score` (0-100), `status`, capped `wrong_questions`, capped `evidence`, and `attempts`.
- Evidence entries (`quiz_pass/fail`, `homework_pass/fail`) are the source of truth for mastery decisions; do not reintroduce a separate global `evidence_events` log.
- Wrong-question book entries live in `StudentState.wrong_question_book`; question-help history lives in `StudentState.question_help_records`. These are learner-state records, not separate course graph nodes.
- Keep product language honest: this is a lightweight JSON learner-state prototype, not a calibrated long-term learner model.

## Frontend and interaction-card invariants

- Learning/homework/GraphRAG HTML must pass through the allowlist sanitizer in `frontend/assets/js/ui.js` before `innerHTML`.
- Do not restore the old `rawText.includes(...)` trust heuristic. Dynamic question text, IDs, prompts, and labels should be inserted with DOM APIs such as `textContent` and `dataset`.
- Long formulas, wide tables, and figures belong inside `learning-*` local viewports so they scroll within the card/bubble rather than widening the page.
- Markdown/LaTeX answers should render through `app.renderMarkdownContent` / `app.renderMath` in `frontend/assets/js/ui.js`, then pass the existing sanitizer. Do not bypass the allowlist for question-help or review explanations.
- GraphRAG answers should be learner-facing evidence cards: hide/fold raw asset IDs, long hashes, raw LaTeX, and raw HTML tables by default; show thumbnails when image paths resolve and clear unavailable placeholders otherwise.
- Keep prose-cited media in the same `learning-reference-block` as the explanation. Unreferenced related media is a compact supplement capped at 3 cards; history restore applies the same de-noising.
- Wrong-book UI defaults to待复习/未掌握 entries, groups by node, and uses `/api/students/{student_id}/wrong-questions/{question_id}/master` for 标记已掌握/取消掌握. Do not fake local-only mastery state when the API call fails.
- Question-help UI is a side modal for ad hoc text/image problems, supports `quick` / `deep` / `vision` modes, and stores records separately from the wrong-question book. It should not auto-add records to wrong questions unless a dedicated product rule is added.
- Objective-test review cards should keep options as stable full-width rows and explanations structured around 判断依据、所选项问题、常见误区、下一步.
- `post_lesson_choice` is a natural pause: users may type a free-form stuck point directly, choose `temporary_question` via “继续追问”, or choose `start_test` via “我懂了，进入小测”. Do not make it a rigid two-button-only gate.
- Active pending interaction kinds include `learning_mode_choice`, `post_lesson_choice`, `temporary_question`, `objective_test_answers`, `variant_test_answers`, `continue_or_homework_choice`, `homework_review_choice`, `homework_answers`, `consolidation_choice`, `quick_check_choice`, and `remediation_decision`.
- Adding a new pending interaction kind requires: (1) backend node sets both `flow_status` and `pending_interaction_kind`, (2) the `flow_status` is in `PENDING_INTERACTION_FLOW_STATUSES` in `session.py`, (3) `infer_resume_target` in `learning_flow.py` has a mapping, (4) frontend `session.js` has a handler in the `session.end` listener, (5) a render function exists in `ui.js`.
- `graph_app.invoke(None, ...)` in LangGraph 0.6.11 does NOT trigger the conditional entry point. Always use `graph_app.invoke({}, ...)` when the graph has a `conditional_entry_point` that must fire.
- Learning plan v2: `select_nodes()` uses weighted composite scoring (urgency 60% + importance 15% + depth 5% + difficulty 5% + id 15%) — different user profiles produce meaningfully different node selections. `difficulty_level` drives `n_steps` and `per_step_range`. `assessment_concept_gaps` calibrated scores merge into the StudentProfile before plan generation.
- Teaching insights panel (`frontend/assets/js/teaching-insights.js`, `api/teaching_insights.py`) shows teaching strategy transparency per node; the tutor can surface the current strategy, detected student state, and why a particular approach was chosen.
- Historical cards must lock once answered/submitted/skipped/reviewed; only the current unresolved interaction may remain pending.
- Landing chip click auto-confirms topic and goes directly to assessment (`state.autoConfirmTopic` flag in `app.js` → `session.js` `topic.confirmation_needed` handler). No manual topic input needed.
- `session.end` SSE event has a `_time.sleep(0.3)` flush delay before `conn.close()` to prevent race condition where the EventSource drops the final event before rendering the pending interaction card.

## Session/history gotchas

- New session, refresh, and history restore must not drop assigned/deferred/in-progress homework.
- Frontend “新对话” first calls `POST /api/sessions` to create an empty checkpoint before the first user message; keep the route idempotent.
- Restoring without a new topic must reuse existing topic, current node, and pending homework; it must not force topic confirmation again.
- Restored sessions must sync sidebar/header title/current node from checkpoint and scroll the current pending card into view after rich media layout settles; the composer must not cover it.
- Sidebar history titles use `_checkpoint_summary` in `interfaces/api/history.py`: `custom_title` → `proposed_topic` → `current_topic` → first user message (30 chars) → `新对话`; never display raw thread UUIDs.
- `frontend/assets/js/history.js` state labels are based on `flow_status`, not title text matching.
- `_has_homework` in `session_resume_router.py` uses blacklist mode: terminal statuses (`completed`, `submitted`, `deferred`) are excluded; missing/unknown status defaults to active homework when items exist.

## Validation expectations

- For pure backend logic, run focused pytest for touched nodes/services plus any contract tests that cover the flow.
- For GraphRAG HTML, frontend cards, history restore, temporary questions, or homework UI, run the relevant backend tests, frontend contract tests, and at least one app health/API/browser check; a string-only unit test is not enough.
- Useful focused groups:
  - Flow: `tests/test_workflow.py tests/test_objective_learning_flow.py tests/test_temporary_question_flow.py tests/test_session_resume_router.py`
  - History/session: `tests/test_history.py tests/test_session.py tests/test_session_persistence.py tests/test_session_resume_router_node.py`
  - Frontend contracts: `tests/test_frontend_objective_test_ui.py tests/test_frontend_chat_layout.py tests/test_frontend_learning_content_layout.py tests/test_frontend_html_safety.py tests/test_homework_learning_ui_contract.py tests/test_graph_rag_learning_answer_html.py tests/test_frontend_wrong_book_ui.py tests/test_frontend_question_help_ui.py`
  - Student tools/API: `tests/test_wrong_questions_api.py tests/test_question_help_api.py`
