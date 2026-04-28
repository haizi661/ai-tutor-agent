# LangGraph 知识图谱驱动智能导师系统阶段性使用与完成工作报告

报告时间：2026-04-28 01:43:25 CST
项目路径：`/home/haizi/ai-tutor-agent`
报告用途：阶段性汇报、研发进展说明、后续验收与评审参考

---

## 一、项目总体定位

本项目是一个基于 LangGraph / FastAPI / GraphRAG 的知识图谱驱动智能导师系统。系统目标不是简单问答机器人，而是构建一个具备“学习主题确认、学前诊断、知识图谱节点学习、节点后测试、错题补救、作业布置、二次登录恢复”的完整教学状态机。

本阶段工作的核心目标是：

将原有偏“灵活对话式”的教学流程，升级为“显式 LangGraph 状态机 + 知识图谱驱动 + 可 checkpoint/resume 的掌握学习主流程”。

当前系统已经从旧的 tutor / tester / evaluator / next_step 等较宽泛节点，逐步拆分为更明确的业务节点，使每一个关键教学决策都有独立状态、独立路由、独立测试与可恢复入口。

---

## 二、本阶段完成工作的总体概括

截至本报告时间，已经完成以下主干能力：

1. 新主流程显式节点化
   - 已接入主题确认后的学前测评、画像生成、图谱节点选择、图谱内容加载、节点讲解、讲解后选择、节点后测试、错题补救、下一节点规划、继续学习或生成作业等主干流程。

2. 知识图谱 2.1 融入学习路径
   - 已新增 `initial_node_selector` 和 `node_content_loader`，用于从图谱结构中选择初始学习节点、读取当前节点内容、学习目标、必会点、常见误区、推荐下一节点等。

3. 图谱 2.2 融入临时问答
   - 已新增 `temporary_question_collector`，将“临时问题”从讲解后选择中拆出，形成：收集问题 → GraphRAG 检索回答 → 回到讲解后选择 的闭环。

4. 节点后客观测试体系
   - 已新增 `objective_test_generator` 和 `objective_test_scorer`。
   - 真实题库暂不接入时，可由 AI 生成客观选择题，但必须包含 `answer_key`。
   - 判分由程序按 `answer_key` 确定性执行，不由 LLM 判分。

5. 错题补救显式节点化
   - 已新增 `wrong_question_explainer`、`variant_question_generator`、`variant_test_answer_dialog`。
   - 节点后测试失败后，不再把错题讲解和变式题生成堆在 scorer 内部，而是形成可恢复的补救状态机。

6. 下一节点与学习结束分支
   - 已新增 `next_node_planner` 和 `continue_or_homework_selector`。
   - 通过节点测试后，系统可以规划下一图谱节点，并让学习者选择继续学习或今天结束并生成作业。

7. 作业生成与作业作答闭环
   - 已新增 `homework_generator`、`homework_review`、`homework_answer_dialog`、`homework_scorer`、`homework_explainer`。
   - 系统支持生成作业、二次登录查看作业、提交答案、确定性/可审计评分、讲解与归档。

8. 二次登录 / 会话恢复
   - 已新增 `session_resume_router`。
   - 系统恢复时不仅依赖 LangGraph checkpoint，还结合 durable student record / homework 状态进行恢复决策。

9. 图谱完整性审计
   - 已新增 `graph_integrity.py` 与对应测试，用于检查图谱节点、边、引用和教学字段完整性。
   - 当前已明确发现 `a2-control-theory/graph.json` 存在已知 dangling node reference 数据债务，避免误报“图谱已完全闭合”。

10. 测试验证
   - 最新大范围回归结果：`98 passed, 5 warnings in 2.24s`。
   - warnings 为已有 SWIG DeprecationWarning，不是当前主流程逻辑错误。

---

## 三、当前已实现的主流程

当前系统主学习链路已经形成以下状态机：

```text
topic_confirmer
→ assessment_generator / assessment_dialog
→ user_profiler
→ initial_node_selector
→ node_content_loader
→ tutor
→ post_lesson_choice
   ├─ temporary_question
   │  → temporary_question_collector
   │  → interruption_tutor / GraphRAG 2.2
   │  → post_lesson_choice
   └─ start_test
      → objective_test_generator
      → objective_test_scorer
         ├─ failed
         │  → wrong_question_explainer
         │  → variant_question_generator
         │  → variant_test_answer_dialog
         │  → objective_test_scorer
         └─ passed
            → next_node_planner
            → continue_or_homework_selector
               ├─ continue_next_node
               │  → node_content_loader
               │  → tutor
               └─ stop_today
                  → homework_generator
                  → END
```

该流程相比旧版最重要的变化是：

- 不再依赖一个大 tutor 或 next_step 节点隐式决定后续流程。
- 每一个用户选择点都可以 checkpoint / resume。
- 每一个确定性教学判断，如客观题判分、作业客观题判分、通过/失败分支，都由程序规则处理。
- LLM 主要负责生成讲解、题目文本、反馈说明，不负责决定客观分数。

---

## 四、二次登录与作业恢复流程

当前已实现第一版可运行二次登录流程：

```text
第二次登录 / 恢复
→ session_resume_router
   ├─ 有未完成交互
   │  → 回到对应 resume target
   ├─ 有作业
   │  → homework_review
   │     ├─ 先处理作业
   │     │  → homework_answer_dialog
   │     │  → homework_scorer
   │     │  → homework_explainer
   │     │  → session_resume_router
   │     └─ 暂缓作业继续学习
   │        → node_content_loader / next_node_planner / tutor
   └─ 无作业
      → 推荐或恢复下一图谱节点
      → node_content_loader / tutor
```

该部分解决了原系统的一个关键问题：

过去恢复学习容易只依赖 checkpoint，缺少 durable learner record。现在恢复逻辑已显式化，并能结合：

- pending interaction
- homework_status
- homework_items
- student_state_snapshot
- current_node_id / next_node_candidate_id
- learning_resume_target

来决定恢复位置。

---

## 五、关键文件与职责说明

### 1. 状态与运行时接口

#### `ai_tutor_agent/core/state.py`

作用：定义全局 AgentState。

本阶段新增或强化字段包括：

- `learning_phase`
- `learning_resume_target`
- `learning_resume_reason`
- `current_node_id`
- `current_node_name`
- `current_node_status`
- `node_quiz_items`
- `node_quiz_answers`
- `node_quiz_wrong_items`
- `node_quiz_score`
- `variant_questions`
- `wrong_question_explanations`
- `homework_items`
- `homework_answers`
- `homework_results`
- `homework_score`
- `homework_status`
- `student_state_snapshot`
- `pending_interaction_kind`
- `pending_interaction_prompt`
- `pending_interaction_options`
- `pending_interaction_answer`
- `node_content_context`
- `tutor_evidence`
- `tutor_citations`

意义：

这些字段把教学过程从“对话上下文”提升为“可恢复的结构化状态”。这对于 LangGraph 流程控制、二次登录恢复、前端 UI 展示、测试验证都很关键。

#### `ai_tutor_agent/core/ports.py`

作用：定义 RuntimeContext 与外部能力抽象。

本阶段新增/强化：

- `QuestionBankProvider`
- `RuntimeContext.question_bank_provider`
- student state store / graph rag pipeline 等运行时依赖传递

意义：

题库、GraphRAG、学生状态存储等外部能力不直接写死在节点内，而是通过 runtime/ports 注入。这使得未来可以从 AI 临时出题平滑替换到真实题库。

#### `ai_tutor_agent/core/learning_flow.py`

作用：学习流程 scaffold、phase 识别、resume target 规范化。

本阶段完成：

- 新主流程 phase 注册
- 新节点 resume target 注册
- `awaiting_variant_answers`、`awaiting_homework_answers`、`awaiting_homework_review_choice` 等恢复状态识别
- session resume / homework resume 相关状态推断

意义：

保证 checkpoint 恢复时可以准确回到对应 LangGraph 节点，而不是回到旧的 tutor 或 next_step。

---

### 2. LangGraph workflow 编排

#### `ai_tutor_agent/orchestration/workflow.py`

作用：注册所有 LangGraph 节点、条件路由、条件入口。

本阶段已接入节点：

- `initial_node_selector`
- `node_content_loader`
- `post_lesson_choice`
- `temporary_question_collector`
- `objective_test_generator`
- `objective_test_scorer`
- `wrong_question_explainer`
- `variant_question_generator`
- `variant_test_answer_dialog`
- `next_node_planner`
- `continue_or_homework_selector`
- `homework_generator`
- `session_resume_router`
- `homework_review`
- `homework_answer_dialog`
- `homework_scorer`
- `homework_explainer`

意义：

workflow 已经从原有泛化教学循环，升级为更接近“节点制掌握学习”的显式状态机。

---

### 3. 图谱节点选择与内容加载

#### `ai_tutor_agent/nodes/initial_node_selector.py`

作用：根据学前测评结果、用户画像、图谱结构、学生历史状态，选择初始知识图谱节点。

输出：

- `current_node_id`
- `current_node_name`
- `current_node_status`
- `next_node_candidate_reason`
- `learning_phase = node_selected`

#### `ai_tutor_agent/nodes/node_content_loader.py`

作用：读取当前图谱节点的结构化内容与 GraphRAG 解释。

写入：

- `node_content_context`
- `graph_must_know`
- `graph_learning_objectives`
- `graph_common_errors`
- `graph_next_steps`
- `tutor_citations`
- `tutor_evidence`

同时兼容：

- `GraphRAGPipeline.ask(query, traversal_mode="balanced")`
- `GraphRAGPipeline.ask(query)`
- `GraphRAGPipeline.query(...)`

意义：

图谱不再只是检索背景，而是显式参与“选哪个节点学、讲什么内容、后续去哪里”。

---

### 4. 讲解后选择与临时问答

#### `ai_tutor_agent/nodes/post_lesson_choice.py`

作用：节点讲解后，让用户选择：

- 提临时问题
- 开始测试

输出：

- `post_lesson_choice = temporary_question / start_test`
- `learning_resume_target`
- pending interaction 信息

#### `ai_tutor_agent/nodes/temporary_question_collector.py`

作用：收集用户临时问题。

流程：

```text
无问题输入 → flow_status = awaiting_temporary_question → pause
有问题输入 → interrupt_query = 用户问题 → interruption_tutor
```

意义：

临时问答不再直接混在 post_lesson_choice 或 tutor 中，而是成为独立可恢复节点。

#### `ai_tutor_agent/nodes/interruption.py`

作用：处理临时问题问答，并在结束后回到主流程选择点。

当前目标：

```text
临时问题回答完成 → post_lesson_choice
```

而不是回到旧的 next_step_selector。

---

### 5. 节点后客观测试

#### `ai_tutor_agent/nodes/objective_test.py`

包含两个主要节点：

1. `objective_test_generator`
2. `objective_test_scorer`

生成策略：

```text
question_bank_provider 可用
→ 从题库取题
否则
→ AI 生成 JSON 客观题，必须包含 answer_key
否则
→ fallback 占位题
```

评分策略：

- 只按 `answer_key` 确定性评分
- 不使用 LLM 判分
- 分数达到 pass_score → passed
- 分数未达到 pass_score → failed，进入错题补救节点

意义：

解决了“AI 出题但必须能正确评分”的关键要求。

---

### 6. 错题补救与变式验证

#### `ai_tutor_agent/nodes/objective_remediation.py`

本阶段最新新增。

包含：

1. `wrong_question_explainer`
   - 读取错题
   - 生成错题讲解
   - 输出 `wrong_question_explanations`

2. `variant_question_generator`
   - 优先从 provider 生成变式题
   - 无 provider 时 fallback 生成
   - 输出 `variant_questions`
   - 暂停等待答案

3. `variant_test_answer_dialog`
   - 收集变式题答案
   - 回到 `objective_test_scorer` 做确定性评分

当前失败补救链路：

```text
objective_test_scorer failed
→ wrong_question_explainer
→ variant_question_generator
→ awaiting_variant_answers / pause
→ variant_test_answer_dialog
→ objective_test_scorer
```

意义：

错题补救不再是 scorer 内部的隐式逻辑，而是一个完整可恢复的掌握学习子状态机。

---

### 7. 通过后下一节点规划

#### `ai_tutor_agent/nodes/next_node_planner.py`

作用：节点测试通过后，基于图谱推荐和学生状态规划下一学习节点。

输出：

- `next_node_candidate_id`
- `next_node_candidate_name`
- `next_node_candidate_reason`
- `learning_phase = next_node_planned`

#### `ai_tutor_agent/nodes/continue_or_homework_selector.py`

作用：让用户选择：

- 继续学习下一节点
- 今天不学了，生成作业

输出：

- `continue_or_homework_choice`
- 对应下一节点或 homework_generator

意义：

通过测试后不再直接自由对话，而是进入明确的学习路径控制。

---

### 8. 作业生成、作答、评分、讲解

#### `ai_tutor_agent/nodes/homework_generator.py`

作用：当用户选择今天结束时，生成作业并保存状态。

写入：

- `homework_items`
- `homework_status = assigned`
- `flow_status = homework_assigned`
- `learning_resume_target = session_resume_router`

#### `ai_tutor_agent/nodes/homework_review.py`

作用：二次登录时展示已有作业，并让用户选择：

- 先处理作业
- 暂缓作业继续学习

#### `ai_tutor_agent/nodes/homework_answer.py`

包含：

1. `homework_answer_dialog`
   - 收集作业答案
   - 暂停/恢复

2. `homework_scorer`
   - 客观题：按 `answer_key` 确定性评分
   - 主观题：按 rubric / reference_answer 关键词覆盖率做可审计量表评分
   - LLM 不负责判分

3. `homework_explainer`
   - 生成作业反馈
   - 归档或清理当前作业
   - 回到 session_resume_router

意义：

系统已具备第一版完整的“课后作业—二次登录—作答—评分—讲解—继续学习”闭环。

---

### 9. 二次登录恢复

#### `ai_tutor_agent/nodes/session_resume_router.py`

作用：统一处理恢复逻辑。

优先级：

1. 未完成 pending interaction
2. 已布置作业
3. 无作业时推荐/恢复下一学习节点

意义：

二次登录不再只是恢复 LangGraph checkpoint，而是结合学生长期状态、作业状态、图谱节点状态进行恢复。

---

### 10. 图谱完整性审计

#### `ai_tutor_agent/knowledge_map/graph_integrity.py`

作用：检查知识图谱数据质量。

检查内容：

- 节点 ID 是否缺失
- 节点 ID 是否重复
- 边 source/target 是否悬空
- prerequisites / related / recommended next nodes 等引用是否悬空
- 教学字段是否完整
- 孤立节点是否存在

当前发现：

- `a2-control-theory/graph.json` 可以加载，教学字段存在。
- 但存在已知 `dangling_node_reference` 数据债务。
- 因此当前不能宣称“图谱数据本体 100% 完整”。

意义：

区分“代码层面图谱融合主干较完整”和“图谱数据本体仍需清理”，避免汇报中过度承诺。

---

## 六、使用方式说明

### 1. 新学习主题启动

用户输入学习主题后，系统进入主题确认和学前测评流程：

```text
输入学习内容
→ 主题确认
→ 学前诊断题
→ 用户画像 / 雷达图
→ 初始图谱节点选择
```

系统会生成或推进：

- 当前主题
- 学习目标
- 学前测评状态
- 用户知识画像
- 图谱初始节点

### 2. 图谱节点学习

系统根据 `current_node_id` 加载节点内容：

```text
initial_node_selector
→ node_content_loader
→ tutor
```

教学内容来源包括：

- 图谱节点结构化字段
- must know / learning objectives / common errors
- GraphRAG 检索解释
- citations / evidence

### 3. 节点讲解后的选择

讲解完成后，系统进入：

```text
post_lesson_choice
```

用户可以选择：

1. 提临时问题
2. 开始测试

如果提临时问题：

```text
temporary_question_collector
→ interruption_tutor
→ post_lesson_choice
```

如果开始测试：

```text
objective_test_generator
→ objective_test_scorer
```

### 4. 节点后测试

测试题来源：

1. 若题库 provider 存在，则从题库取题。
2. 若题库暂未接入，则由 AI 生成客观题。
3. 所有题必须包含 `answer_key`。
4. 程序按 `answer_key` 判分。

通过：

```text
objective_test_scorer
→ next_node_planner
→ continue_or_homework_selector
```

未通过：

```text
objective_test_scorer
→ wrong_question_explainer
→ variant_question_generator
→ variant_test_answer_dialog
→ objective_test_scorer
```

### 5. 继续学习或生成作业

通过节点测试后，用户选择：

1. 继续下一节点

```text
continue_or_homework_selector
→ node_content_loader
→ tutor
```

2. 今天不学了

```text
continue_or_homework_selector
→ homework_generator
→ END
```

### 6. 第二次登录

用户再次进入系统时：

```text
session_resume_router
```

系统会判断：

- 是否有未完成交互
- 是否有未完成作业
- 是否需要继续某个图谱节点
- 是否进入作业处理流程

---

## 七、测试验证情况

### 1. 最新新功能测试

命令：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_objective_remediation_flow.py -vv
```

结果：

```text
5 passed, 5 warnings
```

覆盖内容：

- 错题讲解节点
- 变式题生成节点
- 变式题答案收集节点
- objective scorer failed 路由
- workflow resume / route 映射

### 2. 聚焦回归测试

命令：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_workflow.py \
  tests/test_state.py
```

结果：

```text
29 passed, 5 warnings
```

### 3. compileall + 主流程聚焦回归

命令：

```bash
python -m compileall ai_tutor_agent tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_homework_answer_flow.py \
  tests/test_session_resume_router_node.py \
  tests/test_session_resume_router.py \
  tests/test_homework_generator.py \
  tests/test_graph_integrity.py \
  tests/test_temporary_question_flow.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_workflow.py \
  tests/test_session.py \
  tests/test_post_eval.py \
  tests/test_state.py
```

结果：

```text
70 passed, 5 warnings
```

### 4. 大范围回归测试

命令：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_debug_graph_rag.py \
  tests/test_graph_rag_pipeline.py \
  tests/test_tutor.py \
  tests/test_post_eval.py \
  tests/test_session.py \
  tests/test_workflow.py \
  tests/test_learning_loop.py \
  tests/test_state.py \
  tests/test_history.py \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_temporary_question_flow.py \
  tests/test_homework_generator.py \
  tests/test_graph_integrity.py \
  tests/test_session_resume_router.py \
  tests/test_session_resume_router_node.py \
  tests/test_homework_answer_flow.py
```

结果：

```text
98 passed, 5 warnings in 2.24s
```

说明：

- 5 个 warnings 均为已有 SWIG DeprecationWarning。
- 当前没有主流程测试失败。

---

## 八、当前 git 工作区状态说明

当前工作区存在大量修改与新增文件，说明本阶段是较大规模的主流程改造。

最新 `git diff --stat` 显示：

```text
21 files changed, 1369 insertions(+), 1284 deletions(-)
```

注意：该统计不包含所有未跟踪新增文件。新增文件包括多个 nodes、tests、docs、knowledge_map 工具等。

当前主要新增文件包括：

- `ai_tutor_agent/core/learning_flow.py`
- `ai_tutor_agent/core/learning_support.py`
- `ai_tutor_agent/nodes/post_lesson_choice.py`
- `ai_tutor_agent/nodes/objective_test.py`
- `ai_tutor_agent/nodes/objective_remediation.py`
- `ai_tutor_agent/nodes/initial_node_selector.py`
- `ai_tutor_agent/nodes/node_content_loader.py`
- `ai_tutor_agent/nodes/temporary_question_collector.py`
- `ai_tutor_agent/nodes/next_node_planner.py`
- `ai_tutor_agent/nodes/continue_or_homework_selector.py`
- `ai_tutor_agent/nodes/homework_generator.py`
- `ai_tutor_agent/nodes/session_resume_router.py`
- `ai_tutor_agent/nodes/homework_review.py`
- `ai_tutor_agent/nodes/homework_answer.py`
- `ai_tutor_agent/knowledge_map/graph_integrity.py`
- 多个 `tests/test_*.py`
- 多个 `docs/plans/*.md`

需要注意：

- 当前存在 `a2-control-theory/viewer/app.js.bak` 和 `style.css.bak` 删除状态。
- 这两个删除状态应在提交前确认是否为预期清理行为。

---

## 九、当前完成度判断

### 已完成度较高的部分

1. LangGraph 主流程显式节点化
   - 已基本完成主干。

2. 图谱 2.1 用于学习路径
   - 已接入初始节点选择、节点内容加载、下一节点规划。

3. 图谱 2.2 用于临时问答
   - 已接入临时问题收集与 interruption_tutor 流程。

4. 节点后测试
   - 已支持 AI 出题 / provider 出题 / fallback。
   - 已支持 answer_key 确定性评分。

5. 错题补救
   - 已显式拆成错题讲解、变式生成、变式作答、重新评分。

6. 作业流程
   - 已支持生成、二次登录查看、作答、评分、讲解、归档。

7. 二次登录恢复
   - 已从 scaffold 升级为可运行第一版。

8. 测试保障
   - 当前大范围回归 98 passed。

### 仍不能过度宣称完整的部分

1. 图谱数据本体尚未 100% 完整
   - `a2-control-theory/graph.json` 已知存在 dangling node reference。

2. tutor 对 node_content_context 的强约束仍可继续加强
   - 当前已接入图谱内容，但后续应进一步保证 tutor 必须优先使用 `node_content_context`、`tutor_evidence`、`tutor_citations`。

3. 真实题库尚未接入
   - 当前保留 `QuestionBankProvider` 抽象。
   - 现阶段节点后客观题可由 AI 生成，但以 `answer_key` 程序评分。

4. 主观题评分仍是第一版可审计策略
   - 当前作业主观题用 rubric/reference_answer 关键词覆盖率进行量表评分。
   - 后续可增强反馈质量，但仍不应让 LLM 决定分数。

5. 前端/产品层完整体验仍需进一步端到端验证
   - 当前主要通过节点测试、workflow 路由测试、session 测试验证。
   - 后续应跑一次真实 API/Web 端到端体验。

---

## 十、阶段性结论

本阶段已经完成了 LangGraph 智能导师系统最关键的结构升级：

从“对话驱动的灵活教学循环”，升级为“知识图谱驱动的节点制掌握学习状态机”。

当前已经具备：

- 学前诊断
- 用户画像
- 图谱节点选择
- 图谱内容加载
- 节点讲解
- 临时问答
- 节点后客观测试
- answer_key 确定性评分
- 错题讲解
- 变式题补救
- 下一节点规划
- 继续/结束学习选择
- 作业生成
- 二次登录恢复
- 作业作答与评分讲解
- 图谱完整性审计
- 大范围自动化测试验证

因此，代码层面的主流程融合已经进入较完整阶段，可以作为阶段性汇报成果。

但为了严谨，仍应表述为：

“主流程代码层面已经基本打通，并通过 98 项回归测试；图谱数据本体、真实题库接入、tutor 强约束使用图谱内容、真实端到端产品体验仍需继续完善。”

---

## 十一、建议的汇报表述

可以在汇报中这样概括：

本阶段我们完成了基于 LangGraph 的知识图谱驱动教学主流程重构。系统已经从原来的通用对话式 tutor/tester/evaluator 循环，升级为显式可恢复的掌握学习状态机。当前流程覆盖主题确认、学前诊断、用户画像、图谱节点选择、节点内容加载、节点讲解、临时问答、节点后客观测试、错题补救、变式题验证、下一节点规划、作业生成、二次登录恢复、作业作答评分与讲解等关键环节。

在技术上，我们新增了多个独立 LangGraph 节点，将原先隐藏在大节点内部的业务逻辑拆成可测试、可恢复、可路由的状态机节点。客观题评分和作业客观题评分均采用 answer_key 确定性判分，避免 LLM 黑箱评分。真实题库尚未接入时，系统允许 AI 临时生成客观题，但必须输出可审计 answer_key。

目前大范围回归测试结果为 98 passed，说明主流程代码层面已经基本打通。后续重点是修补图谱数据本体中的悬空引用、接入正式题库、强化 tutor 对图谱节点内容和证据引用的使用，并进行完整前端端到端体验验证。

---

## 十二、后续工作建议

优先级建议如下：

1. 强化 tutor 图谱内容约束
   - 让 tutor 明确优先使用 `node_content_context`、`graph_must_know`、`graph_learning_objectives`、`tutor_evidence`、`tutor_citations`。

2. 修补 a2-control-theory 图谱数据
   - 处理已知 dangling node reference。
   - 决定是补齐缺失节点、删除错误引用，还是标记为 external_refs。

3. 接入正式题库
   - 实现 `QuestionBankProvider`。
   - 替换当前 AI 临时出题。

4. 做一次真实 Web/API 端到端演示
   - 从新主题输入开始。
   - 完成学前诊断、节点讲解、测试、错题补救、作业、二次登录。

5. 提交前整理 git 工作区
   - 确认 `.bak` 删除是否预期。
   - 将新增文件分组提交。
   - 按功能拆分 commit，便于评审。

---

## 十三、附：本阶段关键验证命令

```bash
# 新增错题补救流程测试
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_objective_remediation_flow.py -vv

# 聚焦回归
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_workflow.py \
  tests/test_state.py

# compileall + 主流程聚焦回归
python -m compileall ai_tutor_agent tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_homework_answer_flow.py \
  tests/test_session_resume_router_node.py \
  tests/test_session_resume_router.py \
  tests/test_homework_generator.py \
  tests/test_graph_integrity.py \
  tests/test_temporary_question_flow.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_workflow.py \
  tests/test_session.py \
  tests/test_post_eval.py \
  tests/test_state.py

# 大范围回归
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_debug_graph_rag.py \
  tests/test_graph_rag_pipeline.py \
  tests/test_tutor.py \
  tests/test_post_eval.py \
  tests/test_session.py \
  tests/test_workflow.py \
  tests/test_learning_loop.py \
  tests/test_state.py \
  tests/test_history.py \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_temporary_question_flow.py \
  tests/test_homework_generator.py \
  tests/test_graph_integrity.py \
  tests/test_session_resume_router.py \
  tests/test_session_resume_router_node.py \
  tests/test_homework_answer_flow.py
```
