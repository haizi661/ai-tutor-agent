# AI Tutor Agent 下一步迭代计划

更新时间：2026-06-01
项目根目录：本文所有命令与路径均以本仓库根目录为基准，统一使用项目内相对路径。

## 1. 计划目标

本计划接在“LangGraph 节点制掌握学习主流程主体闭合”之后。目标不是继续横向堆功能，而是把当前可测试原型收敛成更稳定、可演示、可继续产品化的版本。

当前优先级判断：

1. 先跑真实浏览器/API 端到端回归，证明当前结构在用户界面中确实成立。
2. 收束用户画像和学习情况模型，明确哪些字段是画像、哪些字段是学习过程证据。
3. 再扩充节点客观题、变式题和作业题库内容。
4. 然后继续收敛跨系统启动、历史恢复和运行资产治理。
5. 最后分批整理提交，避免把本地缓存、密钥或 ignored Agent 文件带入仓库。

## 2. 当前基线

已完成基线：

- 后端 LangGraph 主流程已包含节点选择、节点内容加载、讲解后选择、临时问题、客观题批量测试、错题补救、下一节点规划、作业生成、二次登录恢复。
- `GraphRAGPipeline` 与 `StudentStateStore` 已进入运行时 `RuntimeContext`。
- `LocalQuestionBankProvider` 已实现并接入 `ApiRuntime`，但当前题库内容仍只到最小可用层。
- 图谱 B 运行资产当前可用：`data/knowledge_map_outputs/**`、`data/mineru_cache/**`、`data/media_evidence_index/**`。
- 历史 A2 / Graph A 已归档到 `docs/archive/a2-control-theory/`，不作为当前主教学图谱。
- `media_evidence_index` 当前可用。
- 2026-04-28 复查记录中的聚焦测试：43 passed, 5 warnings。
- 2026-04-28 闭合报告中的聚焦大回归：88 passed, 5 warnings。
- 2026-04-30 文档/契约同步时运行历史恢复与前端学习内容契约集：66 passed, 5 warnings。
- 2026-04-30 GraphRAG 证据卡片、图表 fallback、残缺公式过滤与临时追问自然化聚焦回归已通过：临时追问相关 52 passed，GraphRAG/media 相关 25 passed。
- 2026-05-01 历史恢复与显示体验收敛：恢复页标题/当前节点/状态横幅同步，当前待处理卡片自动进入可视区，对话态输入框压缩，GraphRAG 相关媒体去重并限量到 3 张；全量测试 424 passed, 5 warnings，浏览器布局检查无横向溢出和输入框重叠。
- 2026-05-02 用户知识图谱实现、evidence 架构统一、死代码清理：knowledge_graph 空图谱起点、学了才加节点、节点级 evidence 单一来源（移除全局 evidence_events 冗余日志和 record_evidence 死代码）、_persist_homework_result 精简；集成测试重写为走真实函数路径；全量测试 445 passed, 5 warnings。
- 2026-05-02 会话恢复准确性 + 聊天记录命名：history.py fallback 链改为 `custom_title` → `proposed_topic` → `current_topic` → 首条用户消息 → "新对话"（不再显示 UUID）；history.js stateLabel 改为基于 flow_status；`_has_homework` 改为黑名单模式（状态缺失默认有作业）；`infer_learning_phase` 合并重复 homework 判断；+5 测试；450 passed。
- 2026-05-03 post_lesson_choice 残留状态修复（首次运行重置 `post_lesson_choice: ""`）、`_START_TEST_MARKERS` 补全（新增 `"start_test"` 和 `"temporary_question"`）、前端 `stripRedundantTextAfterTables()` 表格冗余文本隐藏；+2 测试；452 passed。
- 2026-05-28 学习路径（Learning Plan）实现：`learning_plan_builder.py` 拓扑排序+画像加权+分步聚合算法；`learning_plan_generator` 节点在 user_profiler 后生成多步路径；`initial_node_selector` 从路径第一步选节点；`next_node_planner` 按 Step 推进；`session_resume_router` 从持久化路径恢复；AgentState+StudentState 新增 learning_plan 字段；19 新测试；606 passed。
- 2026-05-29 学习路径 v2 + 前端路径面板：`compute_relevance()` 目标相关性评分、`_score_node()` 多因子 ZPD 加权、`build_priority_plan()` 目标聚焦、`update_learning_plan()` 动态重算；前端路径面板（聊天右侧独立面板）显示 Step 进度与节点状态；KG key 改为 node_id（不再用中文标题）；全量测试 626 passed, 5 skipped。
- 2026-05-29 错题本基础闭环：`/api/students/{student_id}/wrong-questions` 支持 mastered/node/page/sort 查询，`/review` 和 `/master` 支持复习/掌握状态写回；前端默认待复习筛选，支持全部/待复习/已掌握、按节点分组、展开讲解、标记已掌握/取消掌握。
- 2026-05-29 题目答疑工作区：`/api/students/{student_id}/question-help` 支持文字题、图片题、当前节点上下文和 `quick`/`deep`/`vision` 解答模式；前端有当前解答区、模式选择、图片上传和历史记录。
- 2026-05-29 客观题复盘与公式渲染：客观题选项改为整行布局，复盘解释结构化为判断依据、所选项问题、常见误区、下一步；前端加载本地 `marked`/`katex`，题目答疑和复盘解释复用 Markdown/LaTeX 渲染与 sanitizer。
- 2026-05-29 错题本/题目答疑/客观题复盘相关聚焦回归：128 passed, 5 warnings。
- 2026-06-01 学习路径面板宽度稳定：CSS 固定 `width: 360px` + `max-width: 100%; overflow: hidden` 防护，展开节点时宽度不再变化；浏览器 E2E 验收前端渲染、课程方向、主题确认、摸底触发链路全部正常；全量测试 630 passed, 5 skipped, 5 warnings。

当前主要风险：

- 真实浏览器/API 端到端验收仍不足；2026-05-01 已验证一个恢复历史布局样例，但还需要覆盖从新主题到作业恢复的完整用户路径。
- 题库接入机制已就绪，但节点客观题、变式题、作业题内容仍不完整。
- 用户画像已经由学前诊断、`StudentStateStore` 和 `knowledge_graph`（节点级 evidence）共同支撑；掌握分尺度已统一为 0-100，测验/作业 evidence 已沉淀为节点级事件。仍需升级为完整长期学习者模型：confidence、next_review、教学策略信号。
- 前端已支持新 `pending_interaction_kind` 的结构渲染与恢复，`post_lesson_choice` 已从僵硬二选一改为自由追问/进入小测；但还需要真实浏览器/API 验证 locked/pending 生命周期和真实 LLM 输出体验。
- 学习路径后端已简化为纯拓扑 BFS + 分支优先级（评估只用于入口和同层排序）。v2 过度工程化代码已删除。
- 错题本已有筛选与掌握状态，但还缺“复习本节点”“再做一遍原题”和前端排序控件；不能把它表述为完整复习闭环。
- 题目答疑已有模式选择和公式渲染，但当前是一次请求返回完整解答，不是真 token 流式输出；模型选择、失败提示和图片 OCR 边界还需要真实浏览器验收。
- 变式训练还缺硬边界：连续错误达到阈值后应先完成讲解并询问是否继续训练，避免无限出题。
- 教学优化计划（`docs/plans/2026-05-29-teaching-optimization-plan.md`）部分已实施：错题反馈回流、情绪感知调整、前置节点关联已接入 tutor prompt；讲解字数从 80-150 字升级为 650-1000 字（cherry-pick 8ab6927 素材包融合）。剩余：间隔复习、测试题对齐讲解、教学效果追踪。
- 文档较多，旧计划与新状态有重复和过期口径。

## 3. P0：状态口径与恢复稳定性

### Task 1：已完成 — 客观题通过后的 resume target 与实际路由一致

当前 `objective_test_scorer` 通过分支已经返回：

```text
learning_resume_target = next_node_planner
learning_resume_reason = objective_quiz_passed
```

并由 `workflow.py` 路由到：

```text
objective_test_scorer passed -> next_node_planner -> continue_or_homework_selector
```

回归命令：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_objective_learning_flow.py tests/test_workflow.py
```

### Task 2：已完成基础统一 — 维护 pending_interaction_kind 命名表

目标：把新主流程所有等待用户输入的 kind 固化成一张表，前后端共用口径。

建议口径：

```text
topic_confirmation
assessment_dialog
post_lesson_choice
temporary_question
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

持续验收：

- 每个等待节点都写入明确 `pending_interaction_kind`。
- 恢复时前端能根据 kind 渲染对应输入 UI。
- 没有节点只依赖自然语言 prompt 来判断交互类型。

### Task 3：部分完成 — 会话恢复单元测试已扩展，恢复页布局已做样例验证

目标：覆盖主要中断点恢复，而不只测试节点函数。

当前已有 `tests/test_session.py`、`tests/test_history.py`、`tests/test_session_persistence.py`、`tests/test_session_resume_router_node.py` 覆盖多组恢复状态。2026-05-01 已额外验证 `awaiting_post_lesson_choice` 历史页能恢复标题、节点、状态、当前卡片定位和不遮挡布局。仍需继续扩展 API/browser E2E：

- 从 `awaiting_post_lesson_choice` 恢复后继续提交选择并进入后续节点。
- 从 `awaiting_temporary_question` 恢复。
- 从 `awaiting_objective_answers` 恢复。
- 从 `awaiting_continue_or_homework_choice` 恢复。
- 从 `homework_assigned` 恢复。

验收：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_session_resume_router.py tests/test_session.py tests/test_workflow.py
```

### Learner Profile Track：待收敛 — 画像与学情模型显式化

目标：把当前“测评画像 + StudentState 轻量记录”升级为可解释的伴学学习者模型，而不是只在 UI 上展示测评结果。

当前代码事实：

- `user_profiler` 生成 `assessment_concept_gaps`、`assessment_radar`、`difficulty_level`、`teaching_strategy` 和初始 `user_knowledge_graph`。
- `StudentStateStore` 保存当前节点、掌握分、已访问节点、错题节点、题目尝试、作业批次和作业历史。
- Tutor prompt 会读取难度、策略、概念差距、当前节点和情绪信号来调整讲解。

需要完成：

1. 定义 `LearnerProfile` / `NodeMastery` / `LearningEvidenceEvent` 的 schema，并写入 `ai_tutor_agent/core/state.py` 或独立模型文件。
2. ~~统一 `mastery_scores` 尺度~~ — 已完成，统一为 0-100。
3. ~~把客观题、变式题、临时追问、作业答案、错因、提示使用、情绪信号都沉淀为节点级 evidence event。~~ — 已完成（测验/作业通过 `kg_update_score` 沉淀为节点级 evidence；临时追问/提示使用/情绪信号待扩展）。
4. 让 `initial_node_selector` 和 `next_node_planner` 同时参考画像信号与知识图谱前置关系，并给出"为什么推荐这一步"。
5. 恢复历史时显示稳定的学习状态摘要：当前节点、已记录卡点、未完成作业、下一步推荐。

验收：

- 新增单元测试覆盖画像生成、掌握度更新、evidence event 写入和恢复。
- API/history 序列化中能看到稳定的画像摘要，不依赖从聊天文本反推。
- README 与 `docs/current-status-and-usage.md` 明确标注当前是轻量原型还是完整长期模型。

## 4. P0：Web 前端交互闭合与浏览器验收

### Task 4：已实现结构渲染 — 课后停顿与自然追问卡片

目标：后端发出 `post_lesson_choice` 时，前端不再表现成僵硬二选一，而是显示“课后停顿 / 还有哪里卡住？”；学习者可以直接输入一句卡点，也可以使用两个按钮：

- 继续追问
- 我懂了，进入小测

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

持续验收：

- 点击按钮后不需要用户手打文本。
- 直接输入“还是没太明白这个负反馈判断”这类自由卡点表达时，应进入 `temporary_question`，不能误判为 `start_test`。
- 历史恢复后仍能看到正确按钮或状态。

### Task 5：已实现结构渲染 — 节点客观题批量答题卡

目标：后端 `objective_test_generator` 发出 `data.questions` 后，前端渲染 10 道题的选择卡，并一次性提交答案。

后端当前支持紧凑答案字符串，例如：

```text
A B C D A B C D A B
```

更稳的前端可以把答案组装为 dict 后再编码；如果后端只收文本，可先提交紧凑字符串。

持续验收：

- 10 道题均可选择。
- 未全部作答时阻止提交。
- 提交后进入 `objective_test_scorer`。
- 通过/未通过结果在页面上可见。

### Task 6：已实现结构渲染 — 通过后的继续/作业选择卡片

目标：`continue_or_homework_choice` 显示两个按钮：

- 开始下一个节点
- 结束本轮学习，生成作业

验收：

- 继续下一个节点时进入 `node_content_loader -> tutor`。
- 结束本轮学习时进入 `homework_generator` 并显示作业。

### Task 7：已实现结构渲染 — 作业恢复与作业作答 UI

目标：二次登录/恢复时，如果 state 有作业，前端能显示作业复习与作答入口。

涉及节点：

- `session_resume_router`
- `homework_review`
- `homework_answer_dialog`
- `homework_scorer`
- `homework_explainer`

持续验收：

- 重启服务或刷新页面后，历史会话能恢复到作业状态。
- 作业答题可提交。
- 作业讲解后能继续进入下一节点或恢复路由。

### Task 7.1：已完成基础 — 错题本、题目答疑与客观题复盘

当前已落地：

- 错题本：按节点分组、全部/待复习/已掌握筛选、展开讲解、标记已掌握/取消掌握。
- 题目答疑：文字/图片输入、快速解答/深度解析/图片题专用模式、历史记录、本地 Markdown/KaTeX 渲染。
- 客观题复盘：选项整行布局，提交后按题显示判断依据、所选项问题、常见误区和下一步。

下一步补齐：

1. 错题本增加“复习本节点”，点击后关闭错题本并回到对应知识节点学习流程。
2. 错题本增加“再做一遍”，第一版先前端本地重做原题并即时判分，再决定是否写回后端。
3. 错题本增加排序控件：按做错时间倒序、做错最多、最久未复习。
4. 为连续错误设置边界：同一节点或同一题型连续错到阈值后，先给完整讲解，再询问是否继续变式训练。
5. 题目答疑决定是否做真流式输出；如果做流式，需要保证公式块在未闭合时不触发错误渲染。

验收：

- `tests/test_frontend_wrong_book_ui.py`
- `tests/test_wrong_questions_api.py`
- `tests/test_frontend_question_help_ui.py`
- `tests/test_question_help_api.py`
- `tests/test_frontend_objective_test_ui.py`
- 浏览器检查错题本标记掌握、题目答疑公式、客观题复盘布局无横向溢出。

## 5. P1：真实题库与作业题库

### Task 8：部分完成 — 最小本地题库 Provider 已接入，题库内容待扩充

当前已有：

```text
ai_tutor_agent/infrastructure/question_bank.py
data/question_bank/a2-control-theory/assessment_questions.jsonl
```

Provider 支持：

```text
objective_questions.jsonl
variant_questions.jsonl
homework_questions.jsonl
assessment_questions.jsonl
```

客观题建议格式：

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

剩余工作：补齐节点客观题、变式题和作业题内容；provider 缺题时仍应 fallback 到 AI 生成或内置 fallback。

### Task 9：已完成 — QuestionBankProvider 已接入 ApiRuntime

当前 `ApiRuntime` 启动和配置重载都会尝试构建 `LocalQuestionBankProvider`，并通过 `RuntimeContext.question_bank_provider` 进入 workflow。

相关配置：

- `QUESTION_BANK_DIR`，默认 `data/question_bank`；
- `DEFAULT_COURSE_ID`，默认 `a2-control-theory`。

验收重点：有题库时优先取题，无题库或加载失败时不阻断主流程。

### Task 10：将 fallback 题改为严格四选一

目标：即使 LLM 和题库都不可用，fallback 也要满足四选一格式，避免前端/评分假设破裂。

涉及文件：

- `ai_tutor_agent/nodes/objective_test.py`

验收：

- fallback 每题都有 A/B/C/D。
- `answer_key` 必在 A/B/C/D 中。
- 测试覆盖。

## 6. P1：端到端回归

### Task 11：已完成 — 最小 API E2E 脚本

目标：不依赖浏览器，先用 HTTP/SSE 跑通一条主流程。

已实现文件：

```text
scripts/smoke_strict_learning_flow.py
```

覆盖：

1. `/api/sessions` — 创建会话占位
2. `/api/start` — 启动学习
3. `/api/stream` — 消费 SSE 到 session.end
4. `/api/confirm_topic` — 确认主题
5. `/api/assessment_answer` — 对话式测评逐题作答
6. `/api/answer` — 提交 post_lesson_choice (start_test / temporary_question)
7. `/api/answer` — 提交客观题答案
8. `/api/answer` — 提交 continue/homework choice
9. `/api/sessions/{thread_id}/resume` — 测试会话恢复

额外覆盖临时追问流程：`--flow temporary_question` 模式下在 post lesson 阶段直接提交一句卡点表达，验证后端进入 `temporary_question`；GraphRAG 回答后再回到 `post_lesson_choice`。

验收：

```bash
# 完整主流程
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000

# 临时追问流程
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000 --flow temporary_question

# 两者都跑
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000 --flow both
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
- post lesson 阶段直接输入一句卡点表达能够进入临时追问；回答后能继续追问或进入小测。
- GraphRAG 证据展示不暴露 raw asset id、长 hash、raw LaTeX 或 raw HTML table；公式/图表/表格保持在卡片和局部滚动容器内。
- 恢复旧历史时，正文引用媒体不重复出现；未引用的“更多可参考”媒体最多 3 张。
- 错题本打开后默认显示待复习题，标记已掌握后列表和统计同步更新。
- 题目答疑可提交文字题并渲染 Markdown/LaTeX；有图片时模式落到图片题专用。
- 客观题提交后逐题复盘不挤压选项文本，公式不显示原始转义文本。

验收：

- 有截图或日志。
- 失败时能定位到具体 UI/后端事件。

## 7. P2：运行资产与文档治理

### Task 13：已完成 — 统一文档权威入口

已创建 `docs/INDEX.md` 作为文档索引，明确：
- 权威入口：`current-status-and-usage.md`、`next-iteration-plan.md`、交互验证契约
- 功能说明文档：题库集成、运行资产、已完成改进、能力结构草案
- 历史计划/报告已归档到 `docs/plans/` 和 `docs/reports/`
- `docs/graph-mainflow-task-plan.md` 已标记为历史文档

### Task 14：已完成 — 运行资产状态检查命令固化

已创建 `scripts/check_runtime_assets.sh`，检查：
- 图谱 B nodes/edges CSV 存在
- 图谱 B JSON 存在且格式正确
- media_evidence_index/batch_summary.json 存在
- GraphRAGPipeline 引用图谱 B (v2)
- 内部 dangling refs 检查

运行：

```bash
bash scripts/check_runtime_assets.sh
```

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

1. 执行最小 API E2E smoke，验证主流程 state 与 checkpoint/resume 结构，特别覆盖 post lesson 自由卡点表达进入临时追问。
2. 执行真实浏览器 smoke，重点验证刷新/恢复后历史卡片 locked、当前卡片 pending、批改结果不丢，并检查 GraphRAG 证据卡片不暴露调试原文。
3. 对错题本、题目答疑、客观题复盘做浏览器验收：标记掌握写回、公式渲染、选项/解释布局、历史恢复一致性。
4. 补齐错题本复习闭环：复习本节点、再做一遍、排序控件、连续错误后的变式训练边界。
5. 扩充 `data/question_bank/a2-control-theory/` 下 objective / variant / homework 题库内容。
6. 继续扩展后端结构不变量测试和前端契约测试，覆盖新增的作业/临时追问/错题复习边界。
7. 最后做文档、运行资产、git 分批收敛。

## 9. 暂不做的事

为避免发散，下一轮不建议做：

- 不引入复杂多用户权限系统。
- 不急着把 StudentStateStore 升级成完整数据库。
- 不重写整个前端。
- 不追求大型题库自动生成流水线。
- 不把错题本做成第二套知识图谱；它只服务复习动作和主学习流程回跳。
- 不把所有历史 docs 重写一遍。
- 不继续新增主流程节点，除非是为了修复已定义闭环的断点。

当前最重要的是让已经形成的闭环“稳定、可演示、可恢复、可测试”。
