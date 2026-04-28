# AI Tutor Agent 下一步迭代计划

更新时间：2026-04-28
项目路径：`/home/haizi/ai-tutor-agent`

## 1. 计划目标

本计划接在“LangGraph 节点制掌握学习主流程主体闭合”之后。目标不是继续横向堆功能，而是把当前可测试原型收敛成更稳定、可演示、可继续产品化的版本。

当前优先级判断：

1. 先修正主流程状态与恢复口径，避免旧流程字段误导恢复。
2. 再补 Web 前端对新主流程交互的确定性支持。
3. 然后接真实题库与作业题库。
4. 最后补端到端回归、文档收敛与运行资产治理。

## 2. 当前基线

已完成基线：

- 后端 LangGraph 主流程已包含节点选择、节点内容加载、讲解后选择、临时问题、客观题批量测试、错题补救、下一节点规划、作业生成、二次登录恢复。
- `GraphRAGPipeline` 与 `StudentStateStore` 已进入运行时 `RuntimeContext`。
- `QuestionBankProvider` 接口已预留。
- 图谱 B 运行资产当前可用：`data/knowledge_map_outputs/**`、`data/mineru_cache/**`、`data/media_evidence_index/**`。
- 历史 A2 / Graph A 已归档到 `docs/archive/a2-control-theory/`，不作为当前主教学图谱。
- `media_evidence_index` 当前可用。
- 本次复查聚焦测试：43 passed, 5 warnings。
- 前一轮闭合报告聚焦大回归：88 passed, 5 warnings。

当前主要风险：

- 部分 state 字段仍残留旧流程命名。
- 前端对新 `pending_interaction_kind` 的支持不完整。
- 题库尚未真实接入。
- 缺少完整浏览器/API 端到端回归。
- 文档较多，旧计划与新状态有重复和过期口径。

## 3. P0：状态口径与恢复稳定性

### Task 1：修正客观题通过后的 resume target

目标：通过节点客观题后，state 中的恢复目标与实际路由保持一致。

涉及文件：

- `ai_tutor_agent/nodes/objective_test.py`
- `tests/test_objective_learning_flow.py` 或新增专门测试

当前问题：

```text
objective_test_scorer 通过分支返回 learning_resume_target=post_eval_selector
但 workflow.route_after_objective_test_scorer 实际会因 current_node_status=passed 路由到 next_node_planner
```

期望改成：

```text
learning_resume_target = next_node_planner
learning_resume_reason = objective_quiz_passed
```

验收：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_objective_learning_flow.py tests/test_workflow.py
```

### Task 2：统一 pending_interaction_kind 命名表

目标：把新主流程所有等待用户输入的 kind 固化成一张表，前后端共用口径。

建议口径：

```text
topic_confirmation
assessment_dialog
post_lesson_choice
temporary_question_text
objective_test_answers
variant_test_answers
continue_or_homework_choice
homework_review_choice
homework_answers
```

涉及文件：

- `ai_tutor_agent/core/state.py`
- `ai_tutor_agent/nodes/post_lesson_choice.py`
- `ai_tutor_agent/nodes/temporary_question_collector.py`
- `ai_tutor_agent/nodes/objective_test.py`
- `ai_tutor_agent/nodes/continue_or_homework_selector.py`
- `ai_tutor_agent/nodes/homework_review.py`
- `ai_tutor_agent/nodes/homework_answer.py`
- 前端 `frontend/assets/js/ui.js`、`frontend/assets/js/session.js`

验收：

- 每个等待节点都写入明确 `pending_interaction_kind`。
- 恢复时前端能根据 kind 渲染对应输入 UI。
- 没有节点只依赖自然语言 prompt 来判断交互类型。

### Task 3：补会话恢复单元测试

目标：覆盖主要中断点恢复，而不只测试节点函数。

建议新增/扩展测试：

- 从 `awaiting_post_lesson_choice` 恢复。
- 从 `awaiting_temporary_question` 恢复。
- 从 `awaiting_objective_answers` 恢复。
- 从 `awaiting_continue_or_homework_choice` 恢复。
- 从 `homework_assigned` 恢复。

验收：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_session_resume_router.py tests/test_session.py tests/test_workflow.py
```

## 4. P0：Web 前端交互闭合

### Task 4：渲染讲解后选择卡片

目标：后端发出 `post_lesson_choice` 时，前端显示两个按钮：

- 我还有临时问题
- 没有问题，开始测试

涉及文件：

- `frontend/assets/js/ui.js`
- `frontend/assets/js/session.js`
- `frontend/assets/js/state.js` 如需要

后端提交方式：

```http
POST /api/answer
{"thread_id":"...", "answer":"start_test"}
```

或：

```http
POST /api/answer
{"thread_id":"...", "answer":"temporary_question"}
```

验收：

- 点击按钮后不需要用户手打文本。
- 历史恢复后仍能看到正确按钮或状态。

### Task 5：渲染节点客观题批量答题卡

目标：后端 `objective_test_generator` 发出 `data.questions` 后，前端渲染 10 道题的选择卡，并一次性提交答案。

后端当前支持紧凑答案字符串，例如：

```text
A B C D A B C D A B
```

更稳的前端可以把答案组装为 dict 后再编码；如果后端只收文本，可先提交紧凑字符串。

验收：

- 10 道题均可选择。
- 未全部作答时阻止提交。
- 提交后进入 `objective_test_scorer`。
- 通过/未通过结果在页面上可见。

### Task 6：渲染通过后的继续/作业选择卡片

目标：`continue_or_homework_choice` 显示两个按钮：

- 开始下一个节点
- 今天不学了，生成作业

验收：

- 继续下一个节点时进入 `node_content_loader -> tutor`。
- 今日结束时进入 `homework_generator` 并显示作业。

### Task 7：作业恢复与作业作答 UI

目标：二次登录/恢复时，如果 state 有作业，前端能显示作业复习与作答入口。

涉及节点：

- `session_resume_router`
- `homework_review`
- `homework_answer_dialog`
- `homework_scorer`
- `homework_explainer`

验收：

- 重启服务或刷新页面后，历史会话能恢复到作业状态。
- 作业答题可提交。
- 作业讲解后能继续进入下一节点或恢复路由。

## 5. P1：真实题库与作业题库

### Task 8：实现最小本地题库 Provider

目标：用 JSON/JSONL 做一个最小本地题库，不先引入数据库复杂度。

建议文件：

```text
data/question_bank/objective_questions.jsonl
data/question_bank/homework_questions.jsonl
ai_tutor_agent/infrastructure/question_bank.py
tests/test_question_bank_provider.py
```

客观题格式建议：

```json
{
  "question_id": "A2-RL-001",
  "node_id": "node_id_here",
  "stem": "题干",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer_key": "A",
  "explanation": "解析",
  "wrong_option_analysis": {"B": "...", "C": "...", "D": "..."},
  "source": "local_question_bank"
}
```

验收：

- provider 可按 node_id 返回最多 k 道题。
- 题目 schema 校验失败时跳过并记录 warning。
- 没有题库时仍 fallback 到 AI 生成。

### Task 9：把 QuestionBankProvider 接入 ApiRuntime

目标：Web/API 运行时真正注入本地题库 provider。

涉及文件：

- `ai_tutor_agent/interfaces/api/runtime.py`
- `ai_tutor_agent/core/ports.py`
- `ai_tutor_agent/infrastructure/question_bank.py`

验收：

- 有题库时 `objective_test_generator` 使用题库题。
- 无题库时不报错。
- 测试覆盖 provider 注入。

### Task 10：将 fallback 题改为严格四选一

目标：即使 LLM 和题库都不可用，fallback 也要满足四选一格式，避免前端/评分假设破裂。

涉及文件：

- `ai_tutor_agent/nodes/objective_test.py`

验收：

- fallback 每题都有 A/B/C/D。
- `answer_key` 必在 A/B/C/D 中。
- 测试覆盖。

## 6. P1：端到端回归

### Task 11：最小 API E2E 脚本

目标：不依赖浏览器，先用 HTTP/SSE 跑通一条主流程。

建议文件：

```text
scripts/smoke_strict_learning_flow.py
```

覆盖：

1. `/api/start`
2. `/api/stream`
3. `/api/confirm_topic`
4. `/api/assessment_answer` 或 `/api/submit_assessment`
5. `/api/answer` 提交 post lesson choice
6. `/api/answer` 提交客观题答案
7. `/api/answer` 提交 continue/homework choice
8. `/api/sessions/{thread_id}/resume`

验收：

```bash
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000
```

### Task 12：浏览器 smoke

目标：用 Playwright 或最小浏览器脚本确认真实 UI 可操作。

覆盖：

- 新对话输入主题。
- 主题确认按钮。
- 测评题提交。
- 节点讲解显示。
- 知识图谱弹窗可打开。
- 至少一个新主流程选择卡片可点击。

验收：

- 有截图或日志。
- 失败时能定位到具体 UI/后端事件。

## 7. P2：运行资产与文档治理

### Task 13：统一文档权威入口

目标：让 `/docs` 不再让人不知道该看哪份。

建议：

- 保留 `docs/current-status-and-usage.md` 作为当前状态入口。
- 保留 `docs/next-iteration-plan.md` 作为下一步入口。
- 历史报告放 `docs/reports/`。
- 历史计划放 `docs/plans/`。
- 旧 `docs/graph-mainflow-task-plan.md` 标注为 historical。

### Task 14：运行资产状态检查命令固化

目标：把图谱、viewer、media index 的检查做成一个统一命令。

建议文件：

```text
scripts/check_runtime_assets.sh
```

检查：

- 图谱 B nodes/edges CSV 存在。
- GraphRAGPipeline 默认读取图谱 B 运行资产。
- media_evidence_index/batch_summary.json 存在且 ok。
- internal dangling refs 为 0。

### Task 15：清理 git 状态并分批提交

当前仓库有大量 modified/untracked 文件。建议不要一次性大提交，按下面批次提交：

1. 主流程后端代码与测试。
2. knowledge_map/runtime assets 相关源码与脚本。
3. 前端交互改造。
4. docs 更新。
5. 运行资产只提交必要小文件；本地缓存和学生状态继续 ignore。

提交前至少运行：

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

## 8. 推荐执行顺序

严格按以下顺序推进：

1. Task 1：修正 objective 通过后的 resume target。
2. Task 10：fallback 四选一，避免前端/评分不一致。
3. Task 2-3：统一 pending kind + 恢复测试。
4. Task 4-7：前端四类新交互闭合。
5. Task 11：API E2E smoke。
6. Task 8-9：本地题库 provider。
7. Task 12：浏览器 smoke。
8. Task 13-15：文档、运行资产、git 分批收敛。

## 9. 暂不做的事

为避免发散，下一轮不建议做：

- 不引入复杂多用户权限系统。
- 不急着把 StudentStateStore 升级成完整数据库。
- 不重写整个前端。
- 不追求大型题库自动生成流水线。
- 不把所有历史 docs 重写一遍。
- 不继续新增主流程节点，除非是为了修复已定义闭环的断点。

当前最重要的是让已经形成的闭环“稳定、可演示、可恢复、可测试”。
