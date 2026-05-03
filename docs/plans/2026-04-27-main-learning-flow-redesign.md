# Main Learning Flow Redesign Implementation Plan

> 术语同步说明：2026-04-30 已按当前主线统一历史计划/报告中的用户可见文案：课后停顿为“继续追问 / 我懂了，进入小测”，学习结束为“结束本轮学习，生成作业”。内部结束学习路由值仅表示代码兼容标识，不代表用户界面文案。

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Redesign the LangGraph main tutoring workflow from a flexible tutor/practice loop into a node-centered learning pipeline: topic intake → diagnostic assessment → radar/profile → initial graph node → node lesson → follow-up question loop → objective-question test → wrong-question remediation/variant loop → next-node planning → continue-or-homework decision → second-login continuation/homework handling.

**Architecture:** Keep LangGraph as the durable workflow state machine, but replace the current loose `tutor -> next_step_selector -> tester/evaluator -> post_eval_selector` loop with explicit stage nodes and explicit `flow_status` values. Preserve existing ports (`event_sink`, `answer_provider`, `knowledge_provider`) and checkpoint semantics, while adding a thin student-record service and question-bank abstraction for objective questions and homework. Existing subjective assessment, tutor RAG, interruption tutor, and graph services should be reused where possible instead of rewritten.

**Tech Stack:** Python, LangGraph `StateGraph`, FastAPI/SSE runtime adapters, TypedDict/Pydantic-style state contracts, SQLite LangGraph checkpoint, existing course graph/RAG retriever, future question-bank adapters.

---

## 1. Existing Flow vs Target Flow

### 1.1 Current main flow in code

Current graph is centered in:
- `ai_tutor_agent/orchestration/workflow.py`
- `ai_tutor_agent/orchestration/routing.py`
- `ai_tutor_agent/core/state.py`

Current high-level flow:

1. `intake_router`
2. `greeter`
3. `topic_confirmer`
4. `assessment_generator`
5. `assessment_dialog`
6. `user_profiler`
7. `tutor`
8. `next_step_selector`
9. either:
   - `tutor` again
   - `tester`
   - `interruption_tutor`
10. `evaluator`
11. route to:
   - `post_eval_selector` if passed
   - `coach` if remediable
   - `tutor` if failed badly
12. `coach -> next_step_selector`
13. `post_eval_selector -> tester/tutor/post_eval_wrapup`
14. `post_eval_wrapup -> END`

Current behavior characteristics:
- After teaching, `next_step_selector` may auto choose continue/practice/summary/branch.
- Practice is mostly one generated subjective/open question via `tester.py`.
- Evaluation is LLM rubric-based via `evaluator.py`.
- Passing leads to `post_eval_selector`, which currently means continue advance / same-type practice / wrapup.
- Failure may route to `coach`, then back to `next_step_selector`.
- Follow-up questions are supported through `interrupt_query` and `interruption_tutor`.
- Student long-term record exists partly in `knowledge_map/student_state.py`, but it is not yet the central workflow persistence mechanism.

### 1.2 Target flow described by user

New-user / new-topic flow:

1. User starts new learning topic.
2. User inputs learning content, e.g. `自动控制原理`.
3. Topic is confirmed.
4. Generate 10 subjective multiple-choice diagnostic questions.
5. Generate user radar chart.
6. Select the initial node from graph section 2.1.
7. Extract content from knowledge graph for that node.
8. Teach the node.
9. After teaching, user chooses:
   - follow-up question: send question to graph search 2.2, retrieve/process/answer, then return to same choice step;
   - student is ready: start the quiz.
10. Generate 10 objective multiple-choice questions from question bank. `[question bank not yet developed]`
11. User answers and system scores.
12. If score fails:
   - explain wrong questions;
   - generate one corresponding variant for each wrong question;
   - return to scoring process.
13. If score passes:
   - find next graph node using strategy: related node, user not learned, smallest node order, etc.
14. Ask whether to start next node.
15. User chooses:
   - confirm start: repeat node learning flow;
   - generate homework and end the current learning round: select major/homework questions using user record, nodes learned in the current round, prior learned nodes hit by major questions, etc. `[major question bank not yet developed]`; output homework; end session.

Second-login flow:

1. Load user record.
2. If homework was assigned:
   - load corresponding homework questions and answers for solving/explanation.
3. If no homework was assigned:
   - ask whether user wants knowledge consolidation.
   - if yes: generate/select major homework-style questions using same strategy.
   - if no: directly start next node learning.

### 1.3 Main difference

The target flow is stricter and more curriculum-like.

Current project:
- A flexible adaptive dialogue loop.
- Practice and post-evaluation are optional/auto-selected.
- Node progression can happen through tutor markers or next-step choices.
- Failure remediation is a short coach hint, not a full wrong-question loop.

Target project:
- A node-centered mastery pipeline.
- Each graph node has a fixed sequence: teach → temporary Q loop → 10 objective questions → score → wrong-question remediation/variants until pass → next-node decision.
- Session ending produces homework.
- Second login is record/homework-aware.

Therefore the redesign should not be a small prompt tweak. It should introduce explicit workflow stages.

---

## 2. Proposed New LangGraph Workflow

### 2.1 New graph nodes

Keep these existing nodes:
- `intake_router`
- `greeter`
- `topic_confirmer`
- `assessment_generator`
- `assessment_dialog`
- `user_profiler`
- `tutor`
- `interruption_tutor`

Add or replace with these new nodes:

1. `session_resume_router`
   - First entry point for returning users.
   - Loads durable student record.
   - Decides whether to resume homework, offer consolidation, or continue next node.

2. `initial_node_selector`
   - Selects initial graph node after diagnostic profiling.
   - Uses graph section 2.1 strategy and assessment gaps.
   - Writes `graph_anchor_*`, `learning_stage`, and node attempt state.

3. `node_content_loader`
   - Extracts normalized graph/RAG content for current node.
   - Reuses `knowledge_provider.resolve_graph_context` / `query_with_sources`.
   - Writes graph context fields into state.

4. `post_lesson_choice`
   - Explicitly asks whether student has follow-up questions or wants to start the quiz.
   - Replaces current automatic `next_step_selector` after teaching.

5. `objective_test_generator`
   - Generates or retrieves 10 objective multiple-choice questions for current node.
   - Initially use a fallback LLM generator until question bank exists.
   - Later switch to question bank adapter.

6. `objective_test_dialog`
   - Presents 10 objective questions and collects answers.
   - May be batch-submit or one-by-one depending current frontend behavior.

7. `objective_test_scorer`
   - Deterministically scores answers against objective answer keys.
   - Writes wrong question list and pass/fail state.

8. `wrong_question_explainer`
   - Explains wrong questions using graph node content and answer keys.

9. `variant_question_generator`
   - Generates one variant question per wrong question.
   - Writes a variant round into state.

10. `next_node_planner`
   - Selects the next graph node using strategy: related nodes first, user not learned, smallest node order, prerequisites satisfied.
   - Writes proposed next node.

11. `continue_or_homework_selector`
   - Asks whether to start next node now or generate homework and end the current learning round.

12. `homework_generator`
   - Selects/generates homework from major question bank strategy.
   - Initially create adapter with placeholder/fallback behavior because major question bank is not developed.
   - Writes homework assignment to state and durable student record.

13. `homework_review`
   - Second-login path when existing homework is found.
   - Loads assigned questions and answer/explanation material.

14. `consolidation_selector`
   - Second-login path when no homework exists; asks whether user wants consolidation or next-node learning.

### 2.2 New target graph skeleton

New-user flow:

```text
session_resume_router
  -> intake_router/greeter/topic_confirmer
  -> assessment_generator
  -> assessment_dialog
  -> user_profiler
  -> initial_node_selector
  -> node_content_loader
  -> tutor
  -> post_lesson_choice
       temporary_question -> interruption_tutor -> post_lesson_choice
       start_test         -> objective_test_generator
  -> objective_test_dialog
  -> objective_test_scorer
       fail -> wrong_question_explainer -> variant_question_generator -> objective_test_dialog
       pass -> next_node_planner
  -> continue_or_homework_selector
       continue -> node_content_loader -> tutor
       stop     -> homework_generator -> END
```

Second-login flow:

```text
session_resume_router
  has_homework -> homework_review -> END or next_node_planner
  no_homework  -> consolidation_selector
       consolidate -> homework_generator -> END or homework_review
       continue    -> node_content_loader -> tutor
```

---

## 3. State Contract Changes

### Task 1: Add explicit stage/state fields

**Objective:** Make the new workflow routable and recoverable after every pause.

**Files:**
- Modify: `ai_tutor_agent/core/state.py`
- Test: `tests/test_state_contract.py`

Add fields to `AgentState`:

```python
learning_stage: str
current_node_id: str
current_node_title: str
initial_node_selected: bool
node_lesson_completed: bool
post_lesson_choice: str
objective_questions: list
objective_answers: dict
objective_answer_key: dict
objective_score: int
objective_wrong_items: list
objective_attempt_count: int
variant_questions: list
variant_answers: dict
node_passed: bool
proposed_next_node_id: str
proposed_next_node_title: str
continue_learning_choice: str
homework_assignments: list
homework_pending: bool
session_record_loaded: bool
consolidation_choice: str
```

Recommended `learning_stage` values:

```python
"session_start"
"topic_intake"
"topic_confirm"
"diagnostic_assessment"
"profiling"
"initial_node_selection"
"node_content_loading"
"node_teaching"
"post_lesson_choice"
"temporary_question"
"objective_test_generation"
"objective_test_answering"
"objective_test_scoring"
"wrong_question_review"
"variant_practice"
"next_node_planning"
"continue_or_homework"
"homework_generation"
"homework_review"
"consolidation_choice"
"ended"
```

**Implementation notes:**
- Keep `flow_status` for compatibility, but begin routing primarily through `learning_stage`.
- Do not remove old fields yet; migrate gradually.
- Initialize all new fields in `build_initial_state`.

**Tests:**
- `build_initial_state()` includes all new keys.
- Initial values are empty/false and JSON-serializable.

---

## 4. Student Record Service

### Task 2: Introduce a workflow-facing student record port

**Objective:** Make second-login and homework decisions independent from LangGraph checkpoint only.

**Files:**
- Create: `ai_tutor_agent/core/student_records.py`
- Modify: `ai_tutor_agent/core/ports.py`
- Reuse/possibly adapt: `ai_tutor_agent/knowledge_map/student_state.py`
- Test: `tests/test_student_records.py`

Define a minimal protocol/adapter:

```python
class StudentRecordProvider(Protocol):
    def load_record(self, student_id: str) -> dict: ...
    def save_record(self, student_id: str, record: dict) -> None: ...
    def mark_node_started(self, student_id: str, node_id: str, title: str = "") -> dict: ...
    def mark_node_passed(self, student_id: str, node_id: str, score: float) -> dict: ...
    def assign_homework(self, student_id: str, homework_items: list[dict]) -> dict: ...
    def clear_homework(self, student_id: str, homework_ids: list[str] | None = None) -> dict: ...
```

Add to `RuntimeContext`:

```python
student_record_provider: StudentRecordProvider | None = None
```

Use a no-op/in-memory default for tests.

**Important design rule:**
- LangGraph checkpoint stores current conversation/workflow state.
- Student record provider stores durable learning history across sessions.

Do not conflate these two.

---

## 5. Question Bank Abstraction

### Task 3: Add question bank port with fallback implementation

**Objective:** Support objective tests and homework now, while allowing future real question banks.

**Files:**
- Create: `ai_tutor_agent/core/question_bank.py`
- Modify: `ai_tutor_agent/core/ports.py`
- Test: `tests/test_question_bank_contract.py`

Define:

```python
class ObjectiveQuestion(TypedDict):
    id: str
    node_id: str
    stem: str
    options: list[str]
    answer: str
    explanation: str
    difficulty: str
    source: str

class MajorQuestion(TypedDict):
    id: str
    node_ids: list[str]
    stem: str
    answer: str
    explanation: str
    difficulty: str
    source: str

class QuestionBankProvider(Protocol):
    def get_objective_questions(self, node_id: str, *, k: int = 10, exclude_ids: list[str] | None = None) -> list[ObjectiveQuestion]: ...
    def get_variant_questions(self, wrong_items: list[dict], *, k_per_wrong: int = 1) -> list[ObjectiveQuestion]: ...
    def get_major_questions(self, node_ids: list[str], *, k: int = 3) -> list[MajorQuestion]: ...
```

Fallback behavior before real bank exists:
- For objective questions: LLM generator may be used inside `objective_test_generator` if provider returns empty.
- For major homework: generate placeholder homework from learned nodes or emit “question bank not configured” event, depending product choice.

**Critical:** Objective scoring must be deterministic once questions exist. LLM may generate questions, but answer keys must be stored and scoring should not call LLM.

---

## 6. Initial Node Selection

### Task 4: Implement `initial_node_selector`

**Objective:** Replace implicit start-anchor selection with an explicit graph-node selection node.

**Files:**
- Create: `ai_tutor_agent/nodes/initial_node.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_initial_node_selector.py`

Inputs:
- `assessment_concept_gaps`
- `assessment_radar`
- `current_topic`
- `user_knowledge_graph`
- `knowledge_provider.course_graph_nodes`

Selection strategy v1:
1. Prefer graph section `2.1` if available by ID/prefix/title lookup.
2. Within candidate nodes, prefer largest concept gap / lowest calibrated score.
3. If no gap match, choose smallest node order in section 2.1.
4. If 2.1 not found, fallback to existing `graph_anchor_title` from `user_profiler`.
5. Last fallback: current topic.

Outputs:
```python
{
  "initial_node_selected": True,
  "current_node_id": node_id,
  "current_node_title": node_title,
  "graph_anchor_id": node_id,
  "graph_anchor_title": node_title,
  "turn_goal": node_title,
  "topic_focus": node_title,
  "learning_stage": "node_content_loading",
}
```

**Tests:**
- Chooses 2.1 node when present.
- Falls back safely when no graph nodes exist.
- Does not overwrite completed user record incorrectly.

---

## 7. Node Content Loading

### Task 5: Implement `node_content_loader`

**Objective:** Create an explicit stage for extracting graph/RAG content before teaching.

**Files:**
- Create: `ai_tutor_agent/nodes/node_content.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_node_content_loader.py`

Behavior:
- Resolve graph context for `current_node_title` / `current_node_id`.
- Write all graph context fields into state.
- Mark current node as started in `user_knowledge_graph` and student record provider.
- Emit event `graph.node_loaded`.

Outputs include:
```python
{
  "learning_stage": "node_teaching",
  "graph_anchor_id": ...,
  "graph_anchor_title": ...,
  "graph_prerequisites": [...],
  "graph_neighbors": [...],
  "graph_learning_objectives": [...],
  "graph_must_know": [...],
  "graph_common_errors": [...],
  "graph_next_steps": [...],
}
```

**Design note:**
`tutor.py` currently resolves graph context internally. Keep that fallback, but with this node present, tutor should mostly consume already-resolved state.

---

## 8. Post-Lesson Follow-up Question Loop

### Task 6: Replace automatic `next_step_selector` after tutor with `post_lesson_choice`

**Objective:** Match the target flow: after teaching, only two choices are allowed: ask a follow-up question or start the quiz.

**Files:**
- Create: `ai_tutor_agent/nodes/post_lesson.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Modify: `ai_tutor_agent/orchestration/routing.py`
- Test: `tests/test_post_lesson_choice.py`

Options:
```python
POST_LESSON_OPTIONS = [
  {"value": "temporary_question", "label": "继续追问"},
  {"value": "start_test", "label": "我懂了，进入小测"},
]
```

Behavior:
- If user chooses follow-up question, set:
```python
{
  "interrupt_query": user_question,
  "resume_tester": False,
  "learning_stage": "temporary_question",
}
```
- Route to `interruption_tutor`.
- After `interruption_tutor`, route back to `post_lesson_choice` rather than pause.
- If user chooses start the quiz, set:
```python
{
  "learning_stage": "objective_test_generation",
  "post_lesson_choice": "start_test",
}
```

**Important:** This is different from current `next_step_selector`, which may go back to tutor or branch. The new flow should not branch to another node before passing the test.

---

## 9. Objective Test Loop

### Task 7: Implement `objective_test_generator`

**Objective:** Produce exactly 10 objective multiple-choice questions for current node.

**Files:**
- Create: `ai_tutor_agent/nodes/objective_test.py`
- Test: `tests/test_objective_test_generator.py`

Behavior:
1. Try `runtime.question_bank_provider.get_objective_questions(current_node_id, k=10)`.
2. If fewer than 10 and fallback enabled, use LLM to generate missing questions from:
   - graph node content
   - `graph_learning_objectives`
   - `graph_must_know`
   - `graph_common_errors`
3. Store questions and answer key in state.

State outputs:
```python
{
  "objective_questions": questions,
  "objective_answer_key": {question_id: answer},
  "objective_answers": {},
  "objective_wrong_items": [],
  "objective_score": 0,
  "learning_stage": "objective_test_answering",
}
```

Test requirements:
- Always caps/stabilizes to 10 questions.
- Each question has id, stem, options, answer, explanation.
- Answer keys are stored separately for scoring.

### Task 8: Implement `objective_test_dialog`

**Objective:** Collect user answers for the 10 objective questions.

**Files:**
- Add to: `ai_tutor_agent/nodes/objective_test.py`
- Test: `tests/test_objective_test_dialog.py`

Behavior:
- If frontend submits batch answers via `pending_interaction_answer`, parse it.
- Otherwise call `answer_provider.get_answer` with interaction kind `objective_test`.
- Validate answer format.
- Write `objective_answers` and set `learning_stage = "objective_test_scoring"`.

Suggested answer format:
```json
{"q1": "A", "q2": "C", ...}
```

### Task 9: Implement `objective_test_scorer`

**Objective:** Score objective questions deterministically and route pass/fail.

**Files:**
- Add to: `ai_tutor_agent/nodes/objective_test.py`
- Modify: `ai_tutor_agent/orchestration/routing.py`
- Test: `tests/test_objective_test_scorer.py`

Behavior:
- Compare `objective_answers` to `objective_answer_key`.
- Score = correct_count / total * 100.
- Build `objective_wrong_items` with question, selected answer, correct answer, explanation, concept tags.
- Pass threshold should reuse `settings.pass_score` unless separate objective threshold is added.

Outputs on pass:
```python
{
  "objective_score": score,
  "objective_wrong_items": [],
  "node_passed": True,
  "learning_stage": "next_node_planning",
}
```

Outputs on fail:
```python
{
  "objective_score": score,
  "objective_wrong_items": wrong_items,
  "node_passed": False,
  "objective_attempt_count": old + 1,
  "learning_stage": "wrong_question_review",
}
```

---

## 10. Wrong Question Remediation and Variant Loop

### Task 10: Implement `wrong_question_explainer`

**Objective:** Explain every wrong objective question before variant practice.

**Files:**
- Create: `ai_tutor_agent/nodes/wrong_question.py`
- Test: `tests/test_wrong_question_explainer.py`

Behavior:
- Input: `objective_wrong_items`.
- Output a concise explanation per wrong question.
- Use graph node `common_errors` and `must_know`.
- Emit event `objective_test.wrong_explanation`.
- Set `learning_stage = "variant_practice"`.

### Task 11: Implement `variant_question_generator`

**Objective:** For each wrong question, generate one corresponding variant question.

**Files:**
- Add to: `ai_tutor_agent/nodes/wrong_question.py`
- Test: `tests/test_variant_question_generator.py`

Behavior:
- Try question bank provider `get_variant_questions(wrong_items, k_per_wrong=1)`.
- If unavailable, use LLM fallback.
- Store generated variants in `objective_questions` and reset `objective_answers`.
- Store previous round in a history field if needed.
- Set `learning_stage = "objective_test_answering"`.

**Important:** Variant loop returns to scoring process, not to the original full 10-question generation unless product explicitly wants a new full set.

---

## 11. Next Node Planning

### Task 12: Implement `next_node_planner`

**Objective:** Choose next graph node after current node passes.

**Files:**
- Create: `ai_tutor_agent/nodes/next_node.py`
- Test: `tests/test_next_node_planner.py`

Strategy v1:
1. Mark current node passed in `user_knowledge_graph` and student record.
2. Candidate nodes from current node:
   - `graph_neighbors`
   - graph next steps with relation `neighbor` / successor
   - course graph recommended next nodes if available
3. Filter out nodes already mastered/passed/skipped in user record.
4. Filter out nodes whose prerequisites are not passed, unless they are explicitly next in sequence.
5. Sort by:
   - related/successor relation first;
   - unlearned first;
   - smallest node order/id;
   - fallback graph order.
6. Write proposed next node.

Outputs:
```python
{
  "proposed_next_node_id": next_id,
  "proposed_next_node_title": next_title,
  "learning_stage": "continue_or_homework",
}
```

If no next node:
- Set `learning_stage = "homework_generation"` or `ended`, depending product decision.

---

## 12. Continue or Homework Decision

### Task 13: Implement `continue_or_homework_selector`

**Objective:** Ask whether to start next node or generate homework and end the current learning round.

**Files:**
- Create: `ai_tutor_agent/nodes/continue_or_homework.py`
- Test: `tests/test_continue_or_homework_selector.py`

Options:
```python
[
  {"value": "continue", "label": "开始下一个节点"},
  {"value": "end_current_round", "label": "结束本轮学习，生成作业"},
]
```

Outputs:
- If continue:
```python
{
  "continue_learning_choice": "continue",
  "current_node_id": proposed_next_node_id,
  "current_node_title": proposed_next_node_title,
  "graph_anchor_id": proposed_next_node_id,
  "graph_anchor_title": proposed_next_node_title,
  "node_lesson_completed": False,
  "node_passed": False,
  "learning_stage": "node_content_loading",
}
```
- If generate homework and end the current learning round:
```python
{
  "continue_learning_choice": "end_current_round",
  "learning_stage": "homework_generation",
}
```

---

## 13. Homework and Second Login

### Task 14: Implement `homework_generator`

**Objective:** Generate or select homework from learned record and future major question bank.

**Files:**
- Create: `ai_tutor_agent/nodes/homework.py`
- Test: `tests/test_homework_generator.py`

Strategy v1:
- Candidate nodes:
  - nodes learned in the current round;
  - previous mastered nodes related to nodes in the current learning round;
  - nodes with current or historical wrong items;
  - major questions whose `node_ids` overlap these nodes.
- If major question bank unavailable, fallback to generated homework summary/questions and mark source as `fallback_llm`.
- Save homework to student record.

Outputs:
```python
{
  "homework_assignments": [...],
  "homework_pending": True,
  "learning_stage": "ended",
  "flow_status": "normal",
}
```

### Task 15: Implement `session_resume_router`

**Objective:** Route returning users based on durable student record.

**Files:**
- Create: `ai_tutor_agent/nodes/session_resume.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_session_resume_router.py`

Behavior:
- Load record by `student_id`.
- If pending homework exists:
```python
{"learning_stage": "homework_review", "homework_pending": True, ...}
```
- If no homework but existing progress exists:
```python
{"learning_stage": "consolidation_choice", ...}
```
- If no record/progress:
```python
{"learning_stage": "topic_intake"}
```

### Task 16: Implement `homework_review`

**Objective:** On second login, show assigned homework questions and answers/explanations.

**Files:**
- Add to: `ai_tutor_agent/nodes/homework.py`
- Test: `tests/test_homework_review.py`

Behavior:
- Load homework IDs/items from student record.
- If question bank exists, hydrate full question/answer/explanation.
- Otherwise use saved homework assignment payload.
- Emit event `homework.review`.
- Depending product choice, either END or ask to continue learning after review.

### Task 17: Implement `consolidation_selector`

**Objective:** If second-login user has no homework, ask whether to consolidate or continue next node.

**Files:**
- Create: `ai_tutor_agent/nodes/consolidation.py`
- Test: `tests/test_consolidation_selector.py`

Options:
```python
[
  {"value": "consolidate", "label": "先巩固一下"},
  {"value": "continue_next_node", "label": "直接继续下一个节点"},
]
```

Routes:
- `consolidate -> homework_generator`
- `continue_next_node -> node_content_loader -> tutor`

---

## 14. Workflow Wiring

### Task 18: Update `workflow.py` routes

**Objective:** Wire the new explicit pipeline into LangGraph.

**Files:**
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Modify: `ai_tutor_agent/orchestration/routing.py`
- Test: `tests/test_workflow_new_main_flow.py`

Key changes:

1. Add nodes:
```python
session_resume_router
initial_node_selector
node_content_loader
post_lesson_choice
objective_test_generator
objective_test_dialog
objective_test_scorer
wrong_question_explainer
variant_question_generator
next_node_planner
continue_or_homework_selector
homework_generator
homework_review
consolidation_selector
```

2. Change after `user_profiler`:
```python
user_profiler -> initial_node_selector -> node_content_loader -> tutor
```

3. Change after `tutor`:
```python
tutor -> post_lesson_choice
```

4. Change interruption return:
```python
interruption_tutor -> post_lesson_choice
```
for follow-up questions asked after lesson.

5. Objective testing:
```python
post_lesson_choice -> objective_test_generator -> objective_test_dialog -> objective_test_scorer
```

6. Score routing:
```python
objective_test_scorer pass -> next_node_planner
objective_test_scorer fail -> wrong_question_explainer -> variant_question_generator -> objective_test_dialog
```

7. Node continuation:
```python
next_node_planner -> continue_or_homework_selector
continue -> node_content_loader
action stop -> homework_generator -> END
```

8. Keep old `tester/evaluator/post_eval_selector/coach` temporarily for backward compatibility tests, but do not use them in the new main node pipeline unless a compatibility flag is set.

---

## 15. API/SSE Integration

### Task 19: Update API session handling for new interaction kinds

**Objective:** Ensure frontend can pause/resume at each new user choice.

**Files:**
- Modify: `ai_tutor_agent/interfaces/api/session.py`
- Possibly modify: `ai_tutor_agent/interfaces/api/runtime.py`
- Test: `tests/test_api_new_interactions.py`

New `pending_interaction_kind` values:

```python
"post_lesson_choice"
"temporary_question"
"objective_test"
"continue_or_homework"
"homework_review"
"consolidation_choice"
```

Expected frontend payloads:
- post lesson: `temporary_question` with question text OR `start_test`
- objective test: answer dict `{question_id: option}`
- continue/homework: `continue` OR `end_current_round`
- consolidation: `consolidate` OR `continue_next_node`

**Important:** Existing resume/pending interaction patch logic must update `pending_interaction_answer` and preserve checkpoint thread_id.

---

## 16. Testing Strategy

### Task 20: Add end-to-end graph smoke tests with fake providers

**Objective:** Verify the new main flow without real LLM/question bank.

**Files:**
- Create: `tests/test_main_learning_flow_e2e.py`

Fake providers:
- Fake knowledge provider with graph nodes: `2.1`, `2.2`, `2.3`.
- Fake question bank provider returning 10 objective questions.
- Fake answer provider returning:
  - no follow-up question/start_test;
  - 10 answers;
  - continue or stop.
- Fake student record provider in memory.

Scenarios:
1. New topic → diagnostic → initial node → teach → start the quiz → pass → next node → continue.
2. Teach → follow-up question → return to post lesson → start the quiz.
3. Objective test fail → wrong explanation → variant → pass.
4. Pass → generate homework and end the current learning round → homework generated → END.
5. Second login with homework → homework_review.
6. Second login without homework → consolidation choice → continue next node.

Run:
```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_main_learning_flow_e2e.py -v
```

---

## 17. Migration Order

Recommended implementation order:

1. State fields and tests.
2. Student record provider.
3. Question bank provider contract.
4. Initial node selector.
5. Node content loader.
6. Post lesson choice and interruption return.
7. Objective test generator/dialog/scorer.
8. Wrong question explanation and variants.
9. Next node planner.
10. Continue/homework selector.
11. Homework generator/review.
12. Session resume/consolidation.
13. Workflow wiring.
14. API pending interaction integration.
15. E2E smoke tests.
16. Remove or isolate old `next_step_selector/post_eval_selector/tester/evaluator` from the new main flow after tests pass.

---

## 18. Risks and Guardrails

1. Do not delete current nodes immediately.
   - Keep backward compatibility until new E2E tests pass.

2. Do not let LLM scoring control objective tests.
   - Objective tests must use stored answer keys.

3. Do not rely only on LangGraph checkpoint for long-term student record.
   - Use durable student record provider for second-login behavior.

4. Avoid making `tutor.py` even larger.
   - Put new control logic in new nodes.

5. Keep graph node identity stable.
   - Prefer node_id for records; title only for display.

6. Treat question banks as ports, not hardcoded files.
   - Objective bank and major homework bank are explicitly “待开发”; the workflow should already support them through interfaces.

7. Make every pause resumable.
   - Every user-choice node must set `learning_stage`, `flow_status`, `pending_interaction_kind`, `pending_interaction_options`, and `pending_interaction_answer` consistently.

---

## 19. Acceptance Criteria

The redesign is complete when:

1. A new user can enter `自动控制原理` and reach an initial graph node after diagnostic assessment.
2. The system teaches one graph node using graph/RAG content.
3. After teaching, the only main choices are follow-up question or start the quiz.
4. Follow-up questions use graph/RAG search and return to the post-lesson choice.
5. Objective test generation produces 10 questions with answer keys.
6. Objective scoring is deterministic.
7. Failed scoring triggers wrong-question explanation and variant questions.
8. Passing triggers next-node planning.
9. User can choose to continue next node or generate homework and end the current learning round.
10. Ending the current learning round generates homework and saves it to durable student record.
11. Second login detects pending homework.
12. Second login without homework asks consolidation vs continue.
13. Existing tests still pass or are intentionally updated to the new main-flow contract.
