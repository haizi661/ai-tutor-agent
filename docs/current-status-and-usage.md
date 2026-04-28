# AI Tutor Agent 当前完成情况与使用说明

更新时间：2026-04-28
项目路径：`/home/haizi/ai-tutor-agent`

## 1. 当前一句话结论

当前项目已经从普通 RAG 问答/单题陪练，推进到“知识图谱 2.1 节点路径 + 图谱 2.2 临时问答/证据增强 + LangGraph 显式状态机 + 学生长期状态”的节点制掌握学习原型。

可运行主线已经具备：

```text
新主题输入
→ 主题确认
→ 学前诊断
→ 初始图谱节点选择
→ 节点内容加载
→ Tutor 按当前节点讲解
→ 讲解后选择：临时问题 / 开始测试
→ 节点后客观题批量测试
→ 未通过：错题讲解 + 变式题
→ 通过：下一节点规划
→ 继续下一节点 / 今日结束生成作业
→ 二次登录恢复作业或继续学习
```

但仍要严谨区分：这是“主流程主体闭合、可测试、可演示”的版本，还不是最终产品化版本。题库、前端对所有新交互卡片的完整渲染、真实端到端浏览器回归、图谱本体 4/27 时间口径等仍需后续收敛。

## 2. 已完成范围

### 2.1 LangGraph 主流程节点

当前 `ai_tutor_agent/orchestration/workflow.py` 已注册 26 个节点，其中与严格节点制学习主线直接相关的是：

- `intake_router`
- `greeter`
- `topic_confirmer`
- `assessment_generator`
- `assessment_dialog`
- `user_profiler`
- `initial_node_selector`
- `node_content_loader`
- `tutor`
- `post_lesson_choice`
- `temporary_question_collector`
- `interruption_tutor`
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

旧流程节点 `tester/evaluator/coach/next_step_selector/post_eval_selector` 仍作为兼容路径或旧路径存在，不应再当作目标主线的核心。

### 2.2 图谱 2.1：学习路径与节点内容

已完成：

- 当前主教学图谱是 2026-04-27 图谱 B 运行资产：`data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv` 与 `data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv`。
- `GraphRAGPipeline` 默认读取图谱 B，并结合 `data/mineru_cache` 与 `data/media_evidence_index` 提供节点内容、临时问答与证据增强。
- 历史 Graph A / A2 资料已归档到 `docs/archive/a2-control-theory/`，只保留作溯源与对照，不再作为当前主教学图谱，也不再由前端默认挂载为主 viewer。

### 2.3 图谱 2.2：临时问答与证据增强

已完成：

- `ai_tutor_agent/knowledge_map/graph_rag_pipeline.py` 等知识图谱搜索链路已接入。
- Tutor 讲解时优先覆盖 `node_content_context` 中的图谱 2.1 当前节点材料。
- 临时问题通过 `interruption_tutor` 走图谱/RAG 检索后返回，再回到讲解后选择。
- `data/media_evidence_index` 当前最小可用：11 个章节，2928 条标注资产。

可用检查命令：

```bash
cd /home/haizi/ai-tutor-agent
python -m ai_tutor_agent.knowledge_map.runtime_assets --media-index data/media_evidence_index
```

### 2.4 学生长期状态与作业恢复

已完成原型：

- `StudentStateStore` 已接入节点开始、节点评分、作业生成/作业处理等关键环节。
- 节点通过后可以规划下一节点。
- 今日结束可以生成作业并写入学生记录。
- 二次登录可以通过 `session_resume_router` 分流到作业复习/作答或继续学习。

当前口径：学生长期状态已经参与主流程，但仍属于轻量 JSON/本地存储原型；后续如果产品化，应升级为更明确的数据库 schema、迁移策略和用户隔离策略。

### 2.5 测试状态

本次复查已运行聚焦回归：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_workflow.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_temporary_question_flow.py \
  tests/test_objective_learning_flow.py \
  tests/test_homework_answer_flow.py \
  tests/test_session_resume_router.py \
  tests/test_graph_integrity.py
```

结果：

```text
43 passed, 5 warnings
```

此前大回归报告记录的聚焦集合结果是：

```text
88 passed, 5 warnings
```

warnings 为既有 SWIG DeprecationWarning，不是本轮主流程逻辑失败。

## 3. 当前主要缺口

### P0：先修正一个主流程路由口径问题

在 `objective_test_scorer` 通过分支中，节点返回：

```text
learning_resume_target = post_eval_selector
current_node_status = passed
```

而 `workflow.route_after_objective_test_scorer()` 看到 `current_node_status == passed` 会实际路由到 `next_node_planner`。

也就是说：图运行时能进入下一节点规划，但 state 中的 `learning_resume_target` 命名仍残留旧流程口径。建议下一步改成：

```text
learning_resume_target = next_node_planner
learning_resume_reason = objective_quiz_passed
```

并补一个测试，避免后续恢复时误进旧 `post_eval_selector`。

### P0：前端对新主流程交互事件还没有完整产品化

后端已经发出新主流程事件和 `pending_interaction_kind`，但前端主要仍是通用 chat 输入、测评表单、主题确认、临时问题确认等已有交互。需要专项检查/补齐：

- `post_lesson_choice` 两按钮：临时问题 / 开始测试。
- `objective_test_answers` 批量客观题答题卡。
- `continue_or_homework_choice` 两按钮：开始下一个节点 / 今天不学了生成作业。
- `homework_review`、`homework_answer_dialog` 的展示与提交。
- 对 `pending_interaction_kind` 的统一恢复渲染。

如果不补这一层，系统后端可测，但真实 Web 使用会有部分步骤只能靠文本输入，体验不稳定。

### P1：题库仍是接口预留 + AI 生成 + fallback

当前 `QuestionBankProvider` 接口已经存在：

```python
get_objective_questions(node_id, k=10)
get_variant_question(wrong_item)
get_homework_questions(node_ids, k=5)
```

但真实题库尚未落地。现阶段：

- 节点后客观题优先读 provider；没有 provider 时由 LLM 生成；再失败则 fallback。
- fallback 当前是临时占位，甚至可能不是严格四选一。
- 作业是模板化/AI 化原型，不是正式大题题库。

### P1：端到端浏览器/API 回归不足

已有单元/节点/路由测试较多，但仍缺一条完整真实运行链路：

```text
浏览器或 API
→ 新主题
→ 主题确认
→ 学前测评
→ 节点讲解
→ 临时问题
→ 节点测试
→ 错题或通过
→ 作业生成
→ 二次登录恢复
```

### P2：文档与旧计划需要持续去重

`docs/graph-mainflow-task-plan.md` 中仍有阶段状态写成 `in_progress`，但实际已有不少内容已经完成。新的权威口径建议以本文和 `docs/next-iteration-plan.md` 为准，旧计划保留为历史依据。

## 4. 现在怎么使用

### 4.1 启动 Web UI

```bash
cd /home/haizi/ai-tutor-agent
python -m pip install -r requirements.txt
cp .env.example .env
python main.py
```

浏览器打开：

```text
http://127.0.0.1:8000
```

如果是在 Windows 浏览器访问 WSL 服务，通常也可以打开同一个地址。

### 4.2 配置模型

至少在 `.env` 或 Web 设置页配置一组模型 Key，例如：

- `GOOGLE_API_KEY`
- `QWEN_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `MINIMAX_API_KEY`
- `GLM_API_KEY`

Web 设置入口在左下角用户菜单/设置相关区域。服务端也会读取 `.env`。

### 4.3 推荐的首次使用流程

1. 打开 Web UI。
2. 点击“新对话”。
3. 输入学习主题，例如：

```text
我想学习自动控制原理中的根轨迹法
```

4. 主题确认时，优先选择“先做测评/assessment”，不要跳过测评。
5. 完成学前诊断题。
6. 等待系统选择初始图谱节点并开始讲解。
7. 讲解后如果想追问，输入类似：

```text
我没理解为什么闭环极点会影响稳定性
```

8. 如果没有问题，选择/输入：

```text
开始测试
```

9. 客观题作答可按当前后端支持的紧凑格式输入，例如：

```text
A B C D A B C D A B
```

或按前端渲染情况逐题选择。

10. 通过后选择：

```text
开始下一个节点
```

或：

```text
今天不学了
```

选择今天结束时，系统会生成作业并写入学生状态。

### 4.4 查看知识图谱

启动服务后打开：

```text
当前默认不再挂载历史 A2 viewer；如需查看旧资料，请直接打开 `docs/archive/a2-control-theory/viewer/index.html`。
```

或者在 Web 左侧点击“知识图谱”。

### 4.5 命令行运行方式

项目也保留 CLI 入口：

```bash
cd /home/haizi/ai-tutor-agent
python main.py --cli
```

但当前新主流程、状态恢复、可视化、资料库交互主要面向 Web。CLI 可用于轻量 smoke，不建议作为主要体验入口。

## 5. 常用自检命令

### 5.1 服务健康检查

启动服务后：

```bash
curl http://127.0.0.1:8000/api/health
```

期望：

```json
{"status":"ok"}
```

### 5.2 图谱完整性检查

```bash
cd /home/haizi/ai-tutor-agent
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_graph_integrity.py
```

### 5.3 主流程聚焦回归

```bash
cd /home/haizi/ai-tutor-agent
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_workflow.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_temporary_question_flow.py \
  tests/test_objective_learning_flow.py \
  tests/test_homework_answer_flow.py \
  tests/test_session_resume_router.py \
  tests/test_graph_integrity.py
```

### 5.4 运行资产同步

如果 `data/media_evidence_index`、`data/mineru_cache` 或 `viewer/data.js` 异常：

```bash
cd /home/haizi/ai-tutor-agent
scripts/sync_knowledge_map_runtime_assets.sh
```

脚本会恢复图谱 B 运行资产、构建媒体索引并检查可用性。历史 A2 viewer 已归档，不属于当前主流程恢复步骤。

## 6. 当前文档索引

建议按下面顺序阅读：

1. `docs/current-status-and-usage.md`：当前完成情况与使用方式。也就是本文。
2. `docs/next-iteration-plan.md`：下一步迭代计划，按优先级执行。
3. `docs/reports/2026-04-28-langgraph-final-closure-report.md`：上一轮最终闭合报告，记录 88 项聚焦回归和图谱资产状态。
4. `docs/knowledge-map-runtime-assets.md`：运行资产同步说明。
5. `docs/plans/2026-04-28-strict-kg-mastery-mainflow-plan.md`：严格主流程设计长计划。

## 7. 严谨汇报口径

可以对外说：

> 当前系统已经完成知识图谱驱动节点制掌握学习主流程的主体闭合：从主题确认、学前诊断、图谱节点选择、节点内容加载、讲解、临时问答、节点后客观测试、错题补救、下一节点规划、作业生成，到二次登录恢复和作业处理，均已形成显式节点和可测试路由。知识图谱 B 负责学习路径、节点内容、临时问答和证据增强；媒体证据索引当前包含 11 个章节、2928 条标注资产。历史 A2 / Graph A 已归档，不作为当前主教学图谱。聚焦回归已通过。

必须补一句：

> 当前仍是可演示/可迭代原型，不是最终产品化版本。下一步应优先修正路由状态口径、补齐前端新交互卡片、接入真实题库，并跑完整端到端浏览器/API 回归。
