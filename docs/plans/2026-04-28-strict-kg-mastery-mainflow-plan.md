# 知识图谱节点制掌握学习主流程改造计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 将当前 ai-tutor-agent 从“已有图谱/RAG/测评/客观题底座 + 部分严格主流程”改造成完整的知识图谱驱动节点制掌握学习闭环。

**Architecture:** 用 LangGraph 显式节点表达所有用户等待点、评分点、节点选择点和二次登录分流点；知识图谱负责节点结构与内容检索，LLM 负责学前/节点后临时出题与讲解，程序负责客观题确定性评分与状态写回，StudentStateStore 负责 durable 学习记录。

**Tech Stack:** Python, LangGraph, FastAPI runtime, SQLite checkpointer, GraphRAGPipeline, StudentStateStore, LLM ports, pytest.

---

## 0. 当前结构结论

当前结构“底座已比较完整，主流程还没有完全按你这次描述的目标流程固化”。

已经具备：

1. 新主题输入、主题确认、学前诊断入口。
2. 学前 10 组自评 + 配对客观校准题。
3. 用户画像、雷达图数据、初始图谱锚点选择雏形。
4. tutor 图谱感知讲解。
5. 讲解后选择节点 `post_lesson_choice`。
6. 临时问题节点 `interruption_tutor`，已经能走图谱/RAG 检索解答。
7. 节点后客观题生成节点 `objective_test_generator`，目前没有题库时可用 AI 出题。
8. 节点后客观题确定性评分节点 `objective_test_scorer`，根据 `answer_key` 判分，不由 LLM 判分。
9. 评分失败后错题解释 + 变式题最小闭环。
10. 通过后进入 `post_eval_selector`，已有下一节点推荐/作业收尾雏形。
11. 第二次登录已有 homework assigned / consolidation / next node 的 session 层处理雏形。

主要缺口：

1. “从图谱 2.1 选择初始节点”和“从图谱 2.2 检索讲解/临时问题”的边界还没有在代码层显式命名和隔离，当前更多是共用 GraphRAGPipeline/KnowledgeProvider。
2. `user_profiler` 直接跳到 `tutor`，缺少显式 `initial_node_selector` 和 `node_content_loader` 节点。
3. `post_eval_selector` 仍混合了“下一节点规划、是否继续学习、作业收尾”三类职责，应拆分为显式节点。
4. 作业目前是 `build_homework_items` 根据已学/错题节点生成 prompt，不是真正“大题题库”或“大题 AI 临时生成 + 答案/评分标准”。
5. 第二次登录有粗分流，但没有显式 LangGraph 节点 `session_resume_router/homework_review/homework_scorer/consolidation_selector`。
6. 作业作答后的判分、错题讲解、清空/归档尚未形成完整闭环。
7. 老流程 `tester/evaluator/coach/next_step_selector` 仍在 workflow 中保留，和新严格流程并存，后续需要降级为兼容路径或逐步移出主线。

---

## 1. 用户目标流程与当前流程差异对照

### 1.1 新学习主题与主题确定

目标：

```text
用户开始新学习主题 → 输入学习内容（自动控制原理） → 主题确定
```

当前：

- `intake_router` / `greeter` / `topic_confirmer` 已存在。
- `workflow.get_entry_node()` 能处理 `greeting/topic_intake/topic_confirmation_pending/awaiting_topic_confirmation`。

差异：

- 当前主题确定后，部分路径可直接 `direct_tutor`，需要强制新主题首次进入学前测评。
- 应明确：只要是新主题且 `is_assessed=False`，必须进入 `assessment_generator`，不能跳过。

需要改：

- 收紧 `route_after_topic_confirmer()`：新主题确认后默认到 `assessment_generator`。
- 保留 `direct_tutor` 只作为调试/已有 assessed 恢复路径。

---

### 1.2 学前 10 道测评题与雷达图

目标：

```text
生成10道主观选择测评题 → 生成用户雷达图
```

当前：

- `assessment_generator` 生成 10 组 pair：10 道自评题 + 10 道配对客观题。
- `assessment_dialog` 逐题收集。
- `user_profiler` 生成：
  - `assessment_radar`
  - `assessment_concept_gaps`
  - `assessment_result`

差异：

- 你这次说“10 道主观选择测评题”，当前实现是 10 组双测，实际更强，但项目文案需要统一。
- 如果产品上只展示“10 道主观选择题”，则客观校准题可作为隐藏/补充校准；但从学习准确性看，建议保留“10 组自评—客观校准式诊断”。

需要改：

- 明确命名为 `pre_assessment_generator` 或保留 `assessment_generator` 但注释/事件文案改成“10组诊断”。
- 增加测试：确认完整学前测评结束后一定产生 `assessment_radar` 并进入节点选择。

---

### 1.3 初始图谱节点选择

目标：

```text
生成用户雷达图 → 选择图谱2.1中的初始节点
```

当前：

- `user_profiler` 内部调用 `_select_initial_teaching_anchor(concept_gaps)`。
- 返回：
  - `graph_anchor_id`
  - `graph_anchor_title`
  - `current_node_id`
  - `current_node_name`

差异：

- 现在“选择初始节点”隐藏在 `user_profiler` 内部，不是显式节点。
- 没有明确表达“图谱 2.1 初始学习路径图”和“图谱 2.2 检索问答图”的区别。
- 选择策略目前主要基于 concept gap，没有完整纳入：图谱 2.1 节点层级、前置依赖、节点序号、已学记录。

需要改：

新增节点：

```text
initial_node_selector
```

职责：

1. 输入：`assessment_radar`, `assessment_concept_gaps`, `student_state_snapshot`, `graph_2_1_node_map`。
2. 策略：
   - 优先选择校准分最低/过度自信的概念；
   - 映射到图谱 2.1 节点 ID；
   - 若多个候选，选前置依赖已满足者；
   - 若仍多个，选最小节点序号；
   - 排除已完成节点。
3. 输出：
   - `current_node_id`
   - `current_node_name`
   - `learning_phase=node_selected`
   - `learning_resume_target=node_content_loader`

---

### 1.4 节点内容抽取与讲解

目标：

```text
抽取知识图谱中的内容 → 对节点开始讲解
```

当前：

- `tutor.py` 会使用 GraphRAGPipeline / knowledge_provider 做图谱感知讲解。
- 但缺少显式 `node_content_loader`。

差异：

- 当前 `tutor` 既承担内容检索、图谱上下文整理、讲解生成、学生状态 started 写回等多职责。
- 不利于测试“是否真的先抽取图谱节点内容，再讲解”。

需要改：

新增节点：

```text
node_content_loader
```

职责：

1. 根据 `current_node_id` 从图谱 2.1/节点表读取结构化字段：
   - node name
   - prerequisites
   - core_concepts
   - key_points
   - common_errors
   - recommended_next_nodes
2. 必要时调用 GraphRAGPipeline 做节点内容检索。
3. 写入：
   - `graph_anchor_id/title`
   - `graph_learning_objectives`
   - `graph_must_know`
   - `graph_common_errors`
   - `node_content_context`
   - `learning_resume_target=tutor`
4. `tutor` 只负责基于已加载内容讲解。

---

### 1.5 讲解完成后的两个选择

目标：

```text
讲解完成后：
1. 输入临时问题 → 图谱搜索2.2 → 检索处理并输出解答 → 回到选择步骤
2. 没有临时问题，开始测试 → 下一步骤
```

当前：

- `post_lesson_choice` 已实现。
- `interruption_tutor` 已存在。
- `route_after_interruption()` 已倾向回到 `post_lesson_choice`。

差异：

- 当前 session 层对任意输入可能直接当成临时问题，和 `post_lesson_choice` 的显式选择可能有冲突。
- 临时问题“图谱搜索 2.2”未在代码命名上显式区分。

需要改：

1. 在 `post_lesson_choice` 的 `temporary_question` 分支中，不仅记录选择，还要进入一个等待用户输入临时问题的状态：

```text
flow_status=awaiting_temporary_question_text
pending_interaction_kind=temporary_question_text
```

2. 新增或改造节点：

```text
temporary_question_collector
→ interruption_tutor
→ post_lesson_choice
```

3. 在 `interruption_tutor` 中显式使用 `graph_search_mode="2.2_temp_question"` 或等价字段，保证项目书可解释。

---

### 1.6 节点后 10 道客观题与评分

目标：

```text
从题库生成10道客观选择题【待开发】 → 用户回答并评分
```

当前：

- `objective_test_generator` 已实现。
- 当前没有题库时，已经可用 AI 生成四选一客观题。
- `objective_test_scorer` 根据 `answer_key` 程序评分。

差异：

- 当前 `QuestionBankProvider` 接口存在，但真实题库未接。
- AI 题目生成失败时 fallback 只有两选项，和“四选一”目标不完全一致。

需要改：

1. 当前阶段保留 AI 出题：

```text
AI 生成题目 + answer_key → 程序确定性评分
```

2. 修改 fallback 为四选一，避免和目标流程不一致。
3. 后续真实题库开发时只替换 provider，不改 scorer。
4. 加测试：题库缺失时 AI 出题必须是 10 道、四选一、answer_key 有效。

---

### 1.7 不通过后的错题讲解与变式

目标：

```text
评分不过 → 讲解错题 → 每个错题再出一道对应的变式 → 回到评分过程
```

当前：

- `objective_test_scorer` 不通过后：
  - 生成 `wrong_question_explanations`
  - 生成 `variant_questions`
  - 把变式题放回 `node_quiz_items`
  - 等待用户再次作答

差异：

- “讲解错题”当前只是从题目 `explanation` 拼结构，不是显式 LLM 错题讲解节点。
- “每个错题再出一道对应变式”当前可由 provider 或 fallback 生成，未由 AI 根据错因生成高质量变式。
- 缺少最多重试次数/连续失败策略，可能无限变式。

需要改：

新增显式节点：

```text
wrong_question_explainer
variant_question_generator
variant_test_scorer 或复用 objective_test_scorer
```

推荐边：

```text
objective_test_scorer failed
→ wrong_question_explainer
→ variant_question_generator
→ END 等待 variant_test_answers
→ objective_test_scorer
```

策略：

- `wrong_question_explainer` 用 LLM 讲错因，但不改分数。
- `variant_question_generator` 用 LLM 每道错题生成一道四选一变式，必须带 `answer_key`。
- `objective_test_scorer` 继续程序评分。
- 增加 `variant_attempt_count`，超过 2 次后回到 `node_content_loader/tutor` 重讲。

---

### 1.8 通过后寻找下一图谱节点

目标：

```text
评分通过 → 根据策略（相关节点、用户未学过、最小节点序号等）寻找并确定下一个图谱节点
```

当前：

- `post_eval_selector` 内部调用 `recommend_next_node()`。
- `recommend_next_node()` 策略已包含：
  - recommended_next_nodes
  - next_nodes
  - related_nodes
  - 排除 visited
  - fallback 到最小未访问节点序号

差异：

- 策略基本接近，但隐藏在 post_eval 中。
- 没有显式 `next_node_planner` 节点。
- `visited_nodes` 写回依赖 `objective_test_scorer` 通过后写 StudentStateStore，需确保 snapshot 总是最新。

需要改：

新增节点：

```text
next_node_planner
```

职责：

1. 读取最新 StudentStateStore，而不是只信 checkpoint 里的 snapshot。
2. 调用 `recommend_next_node()`。
3. 输出：
   - `next_node_candidate_id`
   - `next_node_candidate_name`
   - `next_node_candidate_reason`
   - `learning_resume_target=continue_or_homework_selector`

---

### 1.9 是否开始下一个节点学习 / 生成作业

目标：

```text
是否开始下一个节点的学习：
1. 确认开始 → 重复上述学习步骤
2. 今天不学了 → 根据策略调用大题题库【待开发】输出题目生成作业 → 结束会话
```

当前：

- `post_eval_selector` 当前有三个选项：
  - continue_advance
  - same_type_practice
  - summarize_wrapup
- `post_eval_wrapup` 生成总结和作业。

差异：

- 目标只需要两个选择：继续下一节点 / 今天不学了生成作业。
- `same_type_practice` 属于旧流程，不应在新严格主流程里作为主选项。
- `post_eval_wrapup` 同时做总结 + 作业，不够显式。
- 作业生成不是题库/AI 大题生成，而是 prompt 占位。

需要改：

新增节点：

```text
continue_or_homework_selector
homework_generator
```

新选项：

```python
[
  {"value": "continue_next_node", "label": "开始下一个节点"},
  {"value": "stop_today", "label": "今天不学了，生成作业"},
]
```

边：

```text
next_node_planner
→ continue_or_homework_selector
   ├─ continue_next_node → node_content_loader → tutor
   └─ stop_today → homework_generator → END
```

作业策略：

1. 优先命中当天已学节点。
2. 加入最近错过/低分节点。
3. 加入之前已学但间隔较久的节点用于复习。
4. 题库未开发时：AI 生成大题 + 参考答案 + 评分 rubric。
5. 题库开发后：HomeworkBankProvider 替换 AI 来源。

---

### 1.10 第二次登录

目标：

```text
用户第二次登录 → 调取用户记录
如果布置过作业：调取对应题目和答案用于解答
如果没布置过作业：询问是否需要巩固知识
  - 需要 → 按策略生成大题
  - 不需要 → 直接开始下一节点学习
```

当前：

- `application/session.py` 已有 session 层逻辑：
  - homework assigned 时展示作业；
  - 输入继续学习可跳到下一节点；
  - daily_wrapup 且无作业时询问巩固/继续；
  - 输入巩固可生成作业；
  - 输入继续可恢复下一节点。

差异：

- 当前是 application/session.py 中的 if/else，不是 LangGraph 显式节点。
- 作业“答案用于解答”还不完整：没有 homework_review/homework_scorer。
- StudentStateStore 只存 homework ID 列表和状态，不完整保存题目、答案、rubric、提交记录。

需要改：

新增节点：

```text
session_resume_router
homework_review
homework_answer_dialog
homework_scorer
consolidation_selector
```

边：

```text
session_resume_router
  ├─ has_homework → homework_review → homework_answer_dialog → homework_scorer
  ├─ ask_consolidation → consolidation_selector
  └─ continue_learning → next_node_planner/node_content_loader/tutor

consolidation_selector
  ├─ wants_consolidation → homework_generator
  └─ continue_learning → next_node_planner/node_content_loader/tutor
```

---

## 2. 建议的最终主流程图

### 2.1 首次学习主题流程

```text
intake_router
→ topic_confirmer
→ pre_assessment_generator
→ pre_assessment_dialog
→ user_profiler
→ initial_node_selector
→ node_content_loader
→ tutor
→ post_lesson_choice
   ├─ temporary_question
   │   → temporary_question_collector
   │   → interruption_tutor_graph_2_2
   │   → post_lesson_choice
   └─ start_test
       → objective_test_generator_ai_or_bank
       → objective_test_answer_dialog
       → objective_test_scorer
          ├─ failed
          │   → wrong_question_explainer
          │   → variant_question_generator
          │   → variant_test_answer_dialog
          │   → objective_test_scorer
          └─ passed
              → next_node_planner
              → continue_or_homework_selector
                 ├─ continue_next_node
                 │   → node_content_loader
                 │   → tutor
                 └─ stop_today
                     → homework_generator
                     → END
```

### 2.2 第二次登录流程

```text
session_resume_router
  ├─ has_homework
  │   → homework_review
  │   → homework_answer_dialog
  │   → homework_scorer
  │   → next_node_planner / continue_or_homework_selector
  ├─ no_homework
  │   → consolidation_selector
  │      ├─ wants_consolidation → homework_generator → END
  │      └─ continue_learning → next_node_planner → node_content_loader → tutor
  └─ unfinished_pending_interaction
      → learning_resume_target
```

---

## 3. 需要新增/修改的文件

### 新增 nodes

1. `ai_tutor_agent/nodes/initial_node_selector.py`
2. `ai_tutor_agent/nodes/node_content_loader.py`
3. `ai_tutor_agent/nodes/temporary_question.py`
4. `ai_tutor_agent/nodes/wrong_question_explainer.py`
5. `ai_tutor_agent/nodes/variant_question_generator.py`
6. `ai_tutor_agent/nodes/next_node_planner.py`
7. `ai_tutor_agent/nodes/continue_or_homework_selector.py`
8. `ai_tutor_agent/nodes/homework_generator.py`
9. `ai_tutor_agent/nodes/homework_review.py`
10. `ai_tutor_agent/nodes/homework_scorer.py`
11. `ai_tutor_agent/nodes/session_resume_router.py`
12. `ai_tutor_agent/nodes/consolidation_selector.py`

### 修改 core

1. `ai_tutor_agent/core/state.py`
   - 增加：
     - `node_content_context`
     - `next_node_candidate_reason`
     - `temporary_question_text`
     - `variant_attempt_count`
     - `homework_rubrics`
     - `homework_reference_answers`
     - `homework_submissions`
     - `homework_score`
     - `homework_feedback`
     - `session_resume_decision`
     - `consolidation_choice`

2. `ai_tutor_agent/core/ports.py`
   - 保留 `QuestionBankProvider`。
   - 可新增 `HomeworkBankProvider`，但当前题库待开发时可先不接真实 provider。

3. `ai_tutor_agent/core/learning_support.py`
   - 抽出：
     - `select_initial_node()`
     - `load_node_content_patch()`
     - `plan_next_node()`
     - `select_homework_node_ids()`
     - `build_ai_homework_prompt()`

4. `ai_tutor_agent/core/learning_flow.py`
   - 增加新的 phase/resume target。

### 修改 orchestration

1. `ai_tutor_agent/orchestration/workflow.py`
   - 注册新节点。
   - 主线改成严格流程。
   - 旧 `tester/evaluator/coach/next_step_selector` 只保留兼容入口，不走新主线。

2. `ai_tutor_agent/application/session.py`
   - 将第二次登录 if/else 逐步收敛到 `session_resume_router`。
   - session 层只负责拿 checkpoint 和注入用户输入，不负责业务分支。

### 修改 tests

新增：

1. `tests/test_main_learning_flow_plan.py`
2. `tests/test_initial_node_selector.py`
3. `tests/test_node_content_loader.py`
4. `tests/test_temporary_question_flow.py`
5. `tests/test_wrong_variant_flow.py`
6. `tests/test_next_node_planner.py`
7. `tests/test_continue_or_homework_selector.py`
8. `tests/test_homework_flow.py`
9. `tests/test_session_resume_router.py`

---

## 4. 分阶段实施任务

### Task 1: 用测试锁定严格主流程路由骨架

**Objective:** 先定义完整目标流程，防止继续在旧节点里堆逻辑。

**Files:**
- Create: `tests/test_strict_mastery_workflow.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`

**Steps:**

1. 写测试断言：
   - `user_profiler → initial_node_selector`
   - `initial_node_selector → node_content_loader`
   - `node_content_loader → tutor`
   - `tutor → post_lesson_choice`
   - `post_lesson_choice temporary_question → temporary_question_collector/interruption_tutor → post_lesson_choice`
   - `post_lesson_choice start_test → objective_test_generator`
   - `objective_test_scorer passed → next_node_planner`
   - `next_node_planner → continue_or_homework_selector`
   - `continue_next_node → node_content_loader`
   - `stop_today → homework_generator → END`

2. 先让测试失败。
3. 最小实现路由函数与节点注册占位。
4. 运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_strict_mastery_workflow.py -vv
```

---

### Task 2: 拆出 initial_node_selector

**Objective:** 把初始节点选择从 `user_profiler` 移到显式节点。

**Files:**
- Create: `ai_tutor_agent/nodes/initial_node_selector.py`
- Modify: `ai_tutor_agent/nodes/assessment.py`
- Modify: `ai_tutor_agent/core/learning_support.py`
- Test: `tests/test_initial_node_selector.py`

**Behavior:**

`user_profiler` 只输出画像与雷达图，不直接设置最终当前节点；`initial_node_selector` 读取画像并选择节点。

**Verification:**

- 低校准概念优先。
- 已学节点排除。
- 多候选时按图谱序号最小。

---

### Task 3: 拆出 node_content_loader

**Objective:** 明确“抽取知识图谱中的内容”这个步骤。

**Files:**
- Create: `ai_tutor_agent/nodes/node_content_loader.py`
- Modify: `ai_tutor_agent/nodes/tutor.py`
- Test: `tests/test_node_content_loader.py`

**Behavior:**

输入 `current_node_id`，输出 `node_content_context` 与 graph state patch。

**Verification:**

- 给定 node_map 中的 `KM001`，必须填充 `graph_anchor_id/title/must_know/common_errors/next_steps`。
- tutor 可以在没有重新检索的情况下使用 `node_content_context` 讲解。

---

### Task 4: 修正 post_lesson_choice 的临时问题收集

**Objective:** 避免选择“临时问题”后还没输入问题就直接进入 interruption。

**Files:**
- Create: `ai_tutor_agent/nodes/temporary_question.py`
- Modify: `ai_tutor_agent/nodes/post_lesson_choice.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_temporary_question_flow.py`

**Behavior:**

```text
post_lesson_choice temporary_question
→ temporary_question_collector 等待问题文本
→ interruption_tutor
→ post_lesson_choice
```

---

### Task 5: 保持 AI 出题，但严格四选一与确定性评分

**Objective:** 当前题库不接，节点后测试由 AI 出题，但评分必须正确。

**Files:**
- Modify: `ai_tutor_agent/nodes/objective_test.py`
- Test: `tests/test_objective_learning_flow.py`

**Changes:**

- fallback 也改为四选一。
- AI 题目不足 10 道时，可以补齐四选一 fallback。
- 所有题都必须有 `answer_key`。

**Verification:**

- 无题库情况下生成 10 道。
- 每题 options 有 A/B/C/D。
- scorer 不调用 LLM。

---

### Task 6: 拆出 wrong_question_explainer 与 variant_question_generator

**Objective:** 将失败补救闭环变成显式节点。

**Files:**
- Create: `ai_tutor_agent/nodes/wrong_question_explainer.py`
- Create: `ai_tutor_agent/nodes/variant_question_generator.py`
- Modify: `ai_tutor_agent/nodes/objective_test.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_wrong_variant_flow.py`

**Behavior:**

- scorer 只负责判分和整理 wrong_items。
- explainer 负责错题讲解。
- generator 负责变式题生成。
- 变式题仍由 scorer 确定性评分。

---

### Task 7: 拆出 next_node_planner

**Objective:** 将“找下一个图谱节点”的策略从 post_eval 中拆出。

**Files:**
- Create: `ai_tutor_agent/nodes/next_node_planner.py`
- Modify: `ai_tutor_agent/core/learning_support.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_next_node_planner.py`

**Strategy:**

1. related/recommended next nodes 优先。
2. 排除已完成/已学节点。
3. 前置依赖未满足的候选降权。
4. 多候选时最小节点序号。
5. 没有相关候选时全图最小未学节点。

---

### Task 8: 替换 post_eval_selector 为 continue_or_homework_selector

**Objective:** 按用户目标只保留“开始下一个节点 / 今天不学了生成作业”。

**Files:**
- Create: `ai_tutor_agent/nodes/continue_or_homework_selector.py`
- Modify: `ai_tutor_agent/orchestration/workflow.py`
- Test: `tests/test_continue_or_homework_selector.py`

**Behavior:**

```text
continue_next_node → node_content_loader
stop_today → homework_generator
```

旧 `same_type_practice` 从新主线移除，只作为 legacy tester 兼容路径。

---

### Task 9: 实现 AI 大题作业生成

**Objective:** 大题题库待开发时，先用 AI 根据策略生成作业，但要保存题目、参考答案、rubric。

**Files:**
- Create: `ai_tutor_agent/nodes/homework_generator.py`
- Modify: `ai_tutor_agent/core/learning_support.py`
- Modify: `ai_tutor_agent/knowledge_map/student_state.py`
- Test: `tests/test_homework_flow.py`

**Behavior:**

- 选节点：今天已学 + 错题/低分 + 旧已学复习。
- 生成题目：大题/综合题。
- 保存：
  - `homework_items`
  - `homework_reference_answers`
  - `homework_rubrics`
  - `homework_status=assigned`

---

### Task 10: 实现第二次登录显式分流

**Objective:** 将二次登录从 session if/else 收敛为可测试 LangGraph 节点。

**Files:**
- Create: `ai_tutor_agent/nodes/session_resume_router.py`
- Create: `ai_tutor_agent/nodes/consolidation_selector.py`
- Create: `ai_tutor_agent/nodes/homework_review.py`
- Create: `ai_tutor_agent/nodes/homework_scorer.py`
- Modify: `ai_tutor_agent/application/session.py`
- Test: `tests/test_session_resume_router.py`

**Behavior:**

```text
has_homework → homework_review
no_homework → consolidation_selector
pending_interaction → learning_resume_target
```

---

### Task 11: 作业作答、评分、归档闭环

**Objective:** 第二次登录后如果有作业，不只是展示，还要能解答、评分、讲解、归档。

**Files:**
- Modify: `ai_tutor_agent/nodes/homework_review.py`
- Modify: `ai_tutor_agent/nodes/homework_scorer.py`
- Modify: `ai_tutor_agent/knowledge_map/student_state.py`
- Test: `tests/test_homework_flow.py`

**Scoring:**

- 作业是大题，不能像选择题用 answer_key。
- 当前阶段可用 LLM rubric 评分，但必须输出结构化 JSON：
  - `score`
  - `rubric_hits`
  - `missing_points`
  - `feedback`
  - `recommended_review_nodes`
- 分数与反馈写回 StudentStateStore。

---

### Task 12: 全量回归与旧流程降级

**Objective:** 保证新主线通过，旧 tester/evaluator 不破坏已有测试。

**Commands:**

```bash
python -m compileall ai_tutor_agent tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_objective_learning_flow.py tests/test_workflow.py tests/test_session.py tests/test_post_eval.py tests/test_state.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

**Acceptance:**

- 新严格主流程测试通过。
- 现有 59 个关键回归不倒退。
- 旧 `tester/evaluator/coach/next_step_selector` 不再出现在新主线 happy path。

---

## 5. 推荐实施顺序

优先级从高到低：

1. `initial_node_selector` + `node_content_loader`：补齐图谱节点制主流程最关键缺口。
2. `continue_or_homework_selector` + `next_node_planner`：替换通过后的旧 post_eval 混合逻辑。
3. `temporary_question_collector`：让临时问题分支更严谨。
4. `wrong_question_explainer` + `variant_question_generator`：把失败补救拆成显式节点。
5. `homework_generator`：完成当天结束作业生成。
6. `session_resume_router/homework_review/homework_scorer`：完成第二次登录闭环。
7. 最后收敛旧流程，保留兼容但不走主线。

---

## 6. 当前阶段的判断

当前不是“结构完全完整”，而是：

```text
底座完整度较高；
严格主流程已经有一条可跑的核心链路；
但和你这次定义的最终流程相比，仍缺显式节点拆分、作业闭环、二次登录显式图节点化、图谱2.1/2.2职责边界。
```

下一步最应该先做：

```text
user_profiler → initial_node_selector → node_content_loader → tutor
```

因为这一步能把“图谱节点制学习”的骨架真正立住。后面的测试、作业、二次登录才能稳定接在这个骨架上。
