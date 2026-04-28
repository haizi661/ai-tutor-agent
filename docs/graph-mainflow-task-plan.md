# 图谱 2.2 与主流程重构任务计划

> 历史计划说明：本文记录图谱 2.2 与主流程重构的原始分阶段计划，部分阶段状态已被后续实现推进。当前完成情况与下一步执行口径请优先看 `docs/current-status-and-usage.md` 和 `docs/next-iteration-plan.md`。

## 目标

本计划用于统一推进以下四类工作，并作为后续逐步实施的唯一基线：

1. 合并 `2026-04-26` 的图谱搜索 2.2 源码能力。
2. 接入 `2026-04-27` 的运行资产包，但按运行资产管理，不把本地缓存和用户状态错误地并入源码层。
3. 参考 `rag+知识图谱+学生状态交接.docx` 完整接入 `knowledge_map`、`student_state`、图谱搜索与媒体索引链路。
4. 将现有智能体主流程重构为“节点驱动学习编排器”。

## 当前结论

## 实施进展

截至当前分支，已经完成或部分完成的内容如下：

- `GraphRAGPipeline` 已接入主讲解与临时问题链路：
  - `ai_tutor_agent/nodes/tutor.py`
  - `ai_tutor_agent/nodes/interruption.py`
- `StudentStateStore` 已接入节点生命周期关键节点：
  - 进入节点时记录 `mark_node_started`
  - 评估后同步 `mastery_scores / visited_nodes / wrong_nodes`
  - 收尾时同步 `homework`
- 过关后不再默认“自动继续讲”，而是进入显式选择：
  - 推荐下一个图谱节点
  - 允许继续同类型练习
  - 允许结束当日学习并生成作业
- 第二次登录的恢复层已具备基础分流：
  - 有作业时优先展示作业
  - 可直接跳到下一节点
  - 无作业且处于收尾态时，可触发“先巩固”生成新作业

当前仍未完成的核心缺口：

- 节点内“10 道客观题批量测试”仍未替换当前单题 tester/evaluator 主链。
- 错题变式题与作业自动判分尚未形成独立节点闭环。
- 第二次登录后的“作业答题 -> 讲解 -> 清空作业”还只是恢复入口层，不是完整作业执行器。

### 4/26 源码层

必须接入：

- `ai_tutor_agent/knowledge_map/graph_rag_pipeline.py`
- `ai_tutor_agent/knowledge_map/builders/graph_context_builder.py`
- `ai_tutor_agent/knowledge_map/builders/graph_media_enricher.py`
- `ai_tutor_agent/knowledge_map/builders/node_selector.py`
- `ai_tutor_agent/knowledge_map/config/media_index_config.py`
- `ai_tutor_agent/knowledge_map/schema/media_asset_schema.py`
- `ai_tutor_agent/knowledge_map/media_index/*`
- `ai_tutor_agent/knowledge_map/build_media_index_batch.py`
- `ai_tutor_agent/knowledge_map/debug_media_index.py`
- 对应测试：
  - `tests/test_graph_rag_pipeline.py`
  - `tests/test_media_asset_scanner.py`
  - `tests/test_media_candidate_filter.py`
  - `tests/test_media_node_linker.py`
  - `tests/test_media_asset_annotator.py`

### 4/27 运行资产层

要纳入整体部署方案：

- `data/mineru_cache/**`
- `data/knowledge_map_outputs/**`
- `data/knowledge_splits/**`
- `data/bm25_cache*.json`

不要直接并入源码主分支：

- `data/chroma_db/**`
- `data/knowledge_map_vector_db/**`
- `data/student_states/*.json`
- `data/tutor_memory.db`

注意：

- `4/27` 包中没有 `data/media_evidence_index/**`。
- 因此接入 `4/27` 资产后，必须重新执行 `build_media_index_batch.py`，用 `mineru_cache + nodes.csv` 生成图谱搜索 2.2 所需的媒体证据索引。

## 现有主流程问题摘要

当前主流程位于 `ai_tutor_agent/orchestration/workflow.py`，核心路径仍是：

`topic -> assessment -> user_profiler -> tutor -> next_step -> tester -> evaluator -> coach`

它已经具备：

- 主题确认
- 学前测评
- 雷达图
- 初始锚点
- 图谱辅助讲解
- 临时问题打断
- 单题练习
- 错题补救

但它还不是目标中的“节点驱动学习编排器”，主要缺口如下：

1. 主讲解仍以普通检索为主，不是图谱搜索 2.2 驱动。
2. 临时问题仍走普通 interruption 检索，不是图谱搜索 2.2。
3. 节点测试仍是单题模式，不是“10 道客观题批量闭环”。
4. 错题后没有“逐错题变式再评估”。
5. 下一节点选择器还不是正式课程推进器。
6. `student_state.py` 没有真正接入主流程生命周期。
7. 第二次登录后的作业恢复、巩固分流还不存在。

## 目标主流程

### 首次学习

1. 用户输入新主题。
2. 主题确认。
3. 生成 10 道主观/自评测评题。
4. 生成用户雷达图。
5. 选择图谱 2.1 初始节点。
6. 抽取知识图谱内容并开始节点讲解。
7. 节点讲解完成后进入选择：
   - 临时问题：转图谱搜索 2.2 检索并回答，再回到选择步骤。
   - 无临时问题：开始节点测试。
8. 从题库生成 10 道客观选择题。
9. 用户答题并评分：
   - 未通过：讲解错题，为每个错题再生成一道变式题，回到评分流程。
   - 通过：进入下一节点决策。
10. 根据策略选择下一个图谱节点：
   - 相关节点优先
   - 过滤未学过/已学过
   - 前置约束
   - 最小节点序号或章节顺序
11. 用户决定是否开始下一节点：
   - 开始：重复节点学习流程。
   - 今天结束：根据学习记录生成复习/作业题。

### 第二次登录

1. 读取用户记录。
2. 如果存在已布置作业：
   - 加载题目与答案
   - 进入作业答题/讲解流程
3. 如果没有作业：
   - 询问是否需要巩固
   - 需要：按策略生成大题复习
   - 不需要：直接进入下一节点学习

## 分阶段实施

### 阶段 0：计划与边界固化

状态：`completed`

任务：

- 在仓库内创建本计划文件。
- 固化 `4/26` 源码层与 `4/27` 运行资产层边界。
- 固化目标主流程与现有流程差异。

验收：

- 存在计划文件。
- 计划文件足够支持后续逐步施工与状态更新。

### 阶段 1：接入图谱搜索 2.2 源码与运行资产边界

状态：`completed`

任务：

- 完整接入 `4/26` 图谱搜索 2.2 源码。
- 保留已并入的 `knowledge_map` 主干，不回退现有兼容修正。
- 把依赖 `data/...` 的测试改成最小夹具模式。
- 明确 `4/27` 资产如何落地到 `data/`，以及哪些内容只作本地恢复，不纳入版本库。
- 新增或补齐生成 `data/media_evidence_index` 的构建方式。

验收：

- `knowledge_map` 2.2 所需代码全部存在。
- 媒体索引链路可独立执行。
- 相关测试可在最小夹具下运行。

### 阶段 2：重构主流程状态机骨架

状态：`completed`

任务：

- 重构 `ai_tutor_agent/orchestration/workflow.py`。
- 在 `ai_tutor_agent/core/state.py` 中新增节点学习状态字段。
- 在 `ai_tutor_agent/application/session.py` 中补入口分流。
- 从现有“教学闭环”切换为“节点学习编排骨架”。

建议新增状态：

- `topic_init`
- `pre_assessment`
- `profile_complete`
- `node_selected`
- `node_teaching`
- `node_temp_qna`
- `node_quiz_batch`
- `node_quiz_remediation`
- `node_passed`
- `next_node_decision`
- `daily_wrapup`
- `homework_resume`

验收：

- 工作流状态命名清晰。
- 现有 `assessment/tutor/tester/evaluator` 不再直接构成全部主流程。

### 阶段 3：接入图谱 2.2 讲解与临时问答

状态：`completed`

任务：

- 改造 `ai_tutor_agent/nodes/tutor.py`，让节点讲解以图谱搜索 2.2 为主。
- 改造 `ai_tutor_agent/nodes/interruption.py`，让临时问题走图谱搜索 2.2。
- 把“临时问题处理完成后”回流到节点选择步骤，而不是旧的 interruption 收尾路径。

验收：

- 节点讲解使用图谱节点、关系证据、媒体证据。
- 临时问题可返回图表/公式证据。

### 阶段 4：接入学生长期状态与节点推进器

状态：`in_progress`

任务：

- 把 `ai_tutor_agent/knowledge_map/student_state.py` 接入主流程。
- 在节点进入、通过、失败、结束时读写学生状态。
- 新增“下一个节点选择器”服务。
- 把当前 `next_step.py` 从讲法选择器，拆分为：
  - 节点内选择器
  - 节点推进器

验收：

- `student_state` 真正参与主流程。
- 系统能基于学习记录选下一节点。

### 阶段 5：接入节点批量测评与作业闭环

状态：`in_progress`

任务：

- 新增 10 道客观题批量测试链路。
- 新增错题讲解与变式题再评估链路。
- 为题库预留接口：
  - 节点客观题题库
  - 作业/复习大题题库
- 新增第二次登录、作业恢复、巩固分流。

验收：

- 存在完整的“讲解 -> 批量测试 -> 错题补救 -> 下一节点 / 今日结束”闭环。
- 第二次登录可恢复作业或直接进入下一节点。

### 阶段 6：前端与 API 配套

状态：`pending`

任务：

- 扩展 `interfaces/api/session.py` 的会话恢复与新接口。
- 扩展前端状态管理与新交互面板。
- 增加：
  - 节点学习进度
  - 批量测试提交
  - 作业恢复
  - 下一节点确认

验收：

- 前端能够承载新的学习状态机，不只是聊天流。

### 阶段 7：端到端验收

状态：`pending`

必须覆盖：

1. 新主题首次进入。
2. 学前测评与雷达图。
3. 初始节点选择。
4. 图谱 2.2 节点讲解。
5. 临时问题检索。
6. 节点批量测试。
7. 错题变式再评估。
8. 下一节点推进。
9. 今日结束与作业生成。
10. 第二次登录与作业恢复。

## 本轮实施顺序

当前开始顺序：

1. 创建计划文件。
2. 进入阶段 1，优先完成图谱搜索 2.2 代码与运行资产边界。
3. 阶段 1 完成后，再进入主流程骨架重构。
4. 阶段 2 优先改造 `workflow.py`、`core/state.py`、`application/session.py` 的骨架与入口分流。

## 进度记录

- `2026-04-27`：创建计划文件，开始阶段 1。
- `2026-04-27`：完成阶段 1。补齐了 `GraphRAGPipeline` / `build_media_index_batch.py` 的 `mineru_cache` 可配置入口，新增 `docs/knowledge-map-runtime-assets.md` 和 `scripts/sync_knowledge_map_runtime_assets.sh`，媒体链路测试切换到 `tests/fixtures` 并通过 `21` 个相关测试。
- `2026-04-27`：已从 `8c15fdf` 同步 `data/mineru_cache`、`data/knowledge_splits`、`data/knowledge_map_outputs`、`data/bm25_cache*.json`，并生成 `data/media_evidence_index/batch_summary.json`。
- `2026-04-27`：开始阶段 2，进入主流程状态机骨架重构。
- `2026-04-27`：阶段 2 已完成第一轮骨架接线。新增 `ai_tutor_agent/core/learning_flow.py`，在 `AgentState` 中补入 `learning_phase`、`learning_resume_target`、节点测评/作业占位字段，并把 `workflow.py`、`application/session.py`、`interfaces/api/session.py`、`assessment.py`、`next_step.py`、`interruption.py`、`post_eval.py` 的关键返回点接到这套骨架上；相关 `state/workflow/session/learning_loop` 测试通过 `19` 个。
