# AI Tutor Agent 当前完成情况与使用说明

更新时间：2026-05-03
项目根目录：本文所有命令默认都在本仓库根目录执行，路径统一使用项目内相对路径。

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
→ 课后停顿：自由追问/表达卡点，或进入节点小测
→ 节点后客观题批量测试
→ 未通过：错题讲解 + 变式题
→ 通过：下一节点规划
→ 继续下一节点 / 结束本轮学习生成作业
→ 二次登录恢复作业或继续学习
```

但仍要严谨区分：这是“主流程主体闭合、可测试、可演示”的版本，还不是最终产品化版本。题库内容、真实端到端浏览器/API 回归、跨系统启动脚本与图谱运行资产治理仍需后续收敛。

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
- 迁移到新机器时，至少需要随代码提交或同步 `data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv`、`data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv`、`data/knowledge_map_outputs/auto_control_knowledge_map_v2.json` 与 `data/media_evidence_index/`。`.env`、`data/chroma_db/`、上传 PDF 和 `data/mineru_cache/` 仍按本地资产处理，不应直接提交密钥或大体积缓存。
- 如果新机器首次运行需要下载本地 embedding 模型，默认 HuggingFace 源不可达时会自动改用 `HF_MIRROR_ENDPOINT`，默认镜像为 `https://hf-mirror.com`；也可以在 `.env` 中改成自己的镜像或关闭 `HF_ENDPOINT_FALLBACK_ENABLED`。

### 2.3 图谱 2.2：临时问答与证据增强

已完成：

- `ai_tutor_agent/knowledge_map/graph_rag_pipeline.py` 等知识图谱搜索链路已接入。
- Tutor 讲解时优先覆盖 `node_content_context` 中的图谱 2.1 当前节点材料。
- 临时追问通过 `interruption_tutor` 走图谱/RAG 检索后返回，再回到“继续追问 / 我懂了，进入小测”的课后停顿。
- 临时追问入口已支持自由卡点表达，例如“还是没太明白这个负反馈判断”，不要求学习者先点击固定按钮。
- GraphRAG 学习回答会把公式、图表、表格渲染为证据卡片：默认隐藏 raw asset id、长 hash、raw LaTeX 与 raw HTML table；图表有真实图片时显示缩略图，无图时显示明确缺图占位。
- GraphRAG 学习回答会把正文引用的公式、图表、表格绑定在对应解释段落附近；未被正文引用的补充媒体只保留为最多 3 张参考卡，恢复旧历史时前端也会做同样的去重和限量。
- `GraphMediaEnricher` 在节点 scope 没有可用图时，会从同章 MinerU `full.md` 的 Markdown 图片中 fallback，并通过 manifest/images 目录恢复真实图片路径。
- `MediaCandidateFilter` 会过滤截断或结构不闭合的 LaTeX 公式候选，避免残缺公式进入证据卡片。
- `data/media_evidence_index` 当前最小可用：11 个章节，2928 条标注资产。

可用检查命令：

```bash
python -m ai_tutor_agent.knowledge_map.runtime_assets --media-index data/media_evidence_index
```

### 2.4 学生长期状态与作业恢复

已完成原型：

- `StudentStateStore` 已接入节点开始、节点评分、作业生成/作业处理等关键环节。
- 用户知识图谱（`StudentState.knowledge_graph`）已实现：空图谱起点，学了才加节点，每个节点跟踪 `score`(0-100)、`status`(in_progress/mastered)、`wrong_questions`(上限100)、`evidence`(上限50，记录 quiz_pass/fail 和 homework_pass/fail)、`attempts`。API: `GET /api/students/{student_id}/knowledge-graph`。
- Evidence 是掌握度决策的唯一数据源，不再有全局 `evidence_events` 冗余日志。
- 节点通过后可以规划下一节点。
- 结束本轮学习可以生成作业并写入学生记录。
- 二次登录可以通过 `session_resume_router` 分流到作业复习/作答或继续学习。

当前口径：学生长期状态已经参与主流程，但仍属于轻量 JSON/本地存储原型；后续如果产品化，应升级为更明确的数据库 schema、迁移策略和用户隔离策略。

### 2.5 用户画像和学习情况生成口径

当前画像不是一个单独的 `user_profile` 文件，而是由“学前诊断画像 + 学习过程状态”共同形成。

学前诊断画像：

- 生成位置：`ai_tutor_agent/nodes/assessment.py` 的 `build_user_profiler_node`。
- 输入：`assessment_questions` 与 `assessment_answers`。
- 计算结果：`assessment_concept_gaps`、`assessment_radar`、`difficulty_level`、`teaching_strategy`、初始 `user_knowledge_graph`。
- 当前规则：概念差距按 `self_score`、`actual_score`、`gap_type`、`calibrated` 表示；起始难度按校准分映射到 Lv.1-Lv.5；教学策略按 overconfident / underconfident / aligned_high / aligned_low 的分布选择。

学习过程状态：

- 存储位置：`data/student_states/*.json`，由 `StudentStateStore` 读写。
- 核心字段：`current_node_id`、`mastery_scores`、`visited_nodes`、`wrong_nodes`、`node_learning_records`、`question_attempts`、`homework_assignments`、`homework_history`、`daily_learning_records`、`last_learning_at`、`knowledge_graph`。
- 更新触发：Tutor 进入节点时标记 started；节点测验或旧评估路径结束后更新 mastery / visited / wrong；作业生成、作答、评分后写入作业记录。

必须保持的严谨口径：

- 当前系统能记录"学到哪里、哪些节点错过、作业是否未完成"，并通过 knowledge_graph 的节点级 evidence 支撑可解释的掌握度决策。
- 当前学前测评要继续强化自评题与客观校准题的配对，否则只能得到主观起点，难以稳定识别"高估自己"的情况。
- 初始节点选择后续应真正使用画像信号，但必须受知识图谱前置关系约束，不能只按最低分跳到任意节点。

### 2.6 测试状态

2026-04-28 复查记录中已运行聚焦回归：

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

2026-04-28 大回归报告记录的聚焦集合结果是：

```text
88 passed, 5 warnings
```

warnings 为既有 SWIG DeprecationWarning，不是本轮主流程逻辑失败。

2026-04-30 文档/契约同步时额外验证：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_history.py \
  tests/test_session.py \
  tests/test_session_persistence.py \
  tests/test_session_resume_router_node.py \
  tests/test_frontend_objective_test_ui.py \
  tests/test_frontend_chat_layout.py \
  tests/test_frontend_learning_content_layout.py \
  tests/test_frontend_html_safety.py \
  tests/test_homework_learning_ui_contract.py \
  tests/test_graph_rag_learning_answer_html.py
```

结果：

```text
66 passed, 5 warnings
```

2026-04-30 临时追问与 GraphRAG 证据展示收敛后运行的聚焦回归：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_objective_learning_flow.py \
  tests/test_interruption_graph_rag_llm.py \
  tests/test_frontend_learning_content_layout.py \
  tests/test_frontend_objective_test_ui.py \
  tests/test_learning_flow_contract.py \
  tests/test_workflow.py -q

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_graph_rag_learning_answer_html.py \
  tests/test_graph_media_enricher.py \
  tests/test_media_candidate_filter.py -q
```

结果：

```text
52 passed
25 passed
```

这些测试证明后端路由、LLM prompt 契约、前端卡片文案、证据卡片 HTML、图表 fallback 与残缺公式过滤的结构契约成立；仍不能替代真实浏览器/API E2E。

2026-05-01 历史恢复、交流框高度、临时问答公式/图表插入顺序与去重限量完成后运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

结果：

```text
452 passed, 5 warnings
```

2026-05-02 用户知识图谱（KG）实现、evidence 架构统一、死代码清理后运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

结果：

```text
452 passed, 5 warnings
```

同日浏览器实测恢复 `awaiting_post_lesson_choice` 历史页：

- 顶部标题恢复为学习主题，当前节点恢复为图谱节点名；
- 状态恢复为“等你决定课后步骤”，并自动定位到课后停顿卡片；
- 底部交流框不遮挡当前卡片，页面无横向溢出；
- 旧历史中的 GraphRAG 补充媒体被限制为 3 张，重复媒体为 0；
- 宽表格和公式仍在局部 viewport 内滚动。

2026-05-03 post_lesson_choice 残留状态修复、_START_TEST_MARKERS 补全、表格冗余文本隐藏后运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
# 452 passed, 5 warnings
```

修复内容：

- `post_lesson_choice` 节点首次运行时重置 `post_lesson_choice: ""`，防止从临时问答返回后残留旧值导致路由错误进入临时问答。
- `_START_TEST_MARKERS` 新增 `"start_test"` 和 `"temporary_question"`，修复系统内部命令被误判为自由提问。
- 前端新增 `stripRedundantTextAfterTables()`：当答案含 `<table>` 时隐藏后续纯文本段落，遇到下一个结构化元素恢复显示。

## 3. 当前主要缺口

### P0：真实端到端浏览器/API 回归仍需继续扩展

后端状态机、前端交互卡片与历史恢复契约已经有较多结构测试覆盖，并在 2026-05-01 对一个真实恢复页做过浏览器布局验证。但仍不能只凭局部 pytest 或单个恢复样例宣称产品结构完成。下一步验收必须按 `docs/plans/2026-04-30-interaction-artifact-validation-contract.md` 的三层标准继续扩展：

1. 后端 timeline / pending interaction 结构不变量；
2. 前端恢复渲染契约，确保历史卡片 locked、当前待交互卡片 pending；
3. 真实浏览器或等价 API E2E，从开始学习到节点测试、错题/继续、作业与二次登录恢复。

### P1：题库已有最小本地 Provider，但内容仍不完整

当前已经接入 `LocalQuestionBankProvider`，并由 `ApiRuntime` 注入主流程：

- `QUESTION_BANK_DIR` 默认 `data/question_bank`；
- `DEFAULT_COURSE_ID` 默认 `a2-control-theory`；
- 题库文件支持 `assessment_questions.jsonl`、`objective_questions.jsonl`、`variant_questions.jsonl`、`homework_questions.jsonl`；
- provider 不可用或题目不足时，节点仍 fallback 到 AI 生成或内置 fallback，避免流程中断。

当前仓库中只保留最小 `assessment_questions.jsonl` 资产；节点客观题、变式题、作业题仍需继续补内容质量。因此现阶段不能称为“正式题库完成”，只能称为“题库接入机制已就绪，题库内容待扩充”。

### P1：用户画像仍需升级为证据驱动的长期学习者模型

当前 `StudentStateStore` 已经进入主流程，并通过 `knowledge_graph` 实现了节点级 evidence 驱动的掌握度追踪。下一轮要避免只把画像当成"测评报告"，应按伴学产品方式收敛为：

1. 静态学习画像：目标、背景、时间预算、偏好的解释方式。
2. 初始诊断画像：自评、客观校准、概念差距、起始难度和教学策略。
3. 动态节点掌握模型：每个图谱节点的 mastery、confidence、attempts、last_seen、next_review。
4. 错因与证据事件：错题、临时追问、作业答案、提示使用、情绪信号都要能追溯到节点。
5. 教学策略画像：根据 overconfident / underconfident / repeated mistake / formula weak 等信号调整讲解和题目。

优先修复点：

- 统一 `mastery_scores` 的数值尺度（当前 0-100 已统一）。
- 让初始节点选择和后续节点规划能解释"为什么推荐这一步"。

### P1：交互卡片已经结构接入，但需要浏览器级验收

前端已支持以下 `pending_interaction_kind` 的渲染/恢复：

- `post_lesson_choice`：自由追问/表达卡点，或进入节点小测；
- `objective_test_answers` 与 `variant_test_answers`：批量题卡；
- `continue_or_homework_choice`：继续下一节点 / 生成作业结束；
- `homework_review_choice`、`homework_answers`、`consolidation_choice`；
- 历史恢复中的 choice card locked 状态。

剩余风险不再是“完全没有前端入口”，而是需要在真实浏览器中验证：提交/跳过后的历史卡片不会重新可点、刷新后当前 pending 卡片能恢复、批改结果和错题讲解不丢失。

### P1：端到端浏览器/API 回归不足

已有单元/节点/路由测试较多，但仍缺一条完整真实运行链路：

```text
浏览器或 API
→ 新主题
→ 主题确认
→ 学前测评
→ 节点讲解
→ 自由追问或表达卡点
→ 节点测试
→ 错题或通过
→ 作业生成
→ 二次登录恢复
```

### P2：文档与旧计划需要持续去重

`docs/graph-mainflow-task-plan.md` 与历史 `docs/plans/*.md` 仍保留原始计划语境。新的权威口径以本文、`docs/next-iteration-plan.md` 和交互 Artifact 验收计划为准；旧计划只作历史依据。

## 4. 现在怎么使用

### 4.1 启动 Web UI

```bash
python -m pip install -r requirements.txt
cp .env.example .env
python main.py
```

启动约束：

- Web UI 固定使用 `8000` 端口；如果旧服务占着该端口，当前实现会直接报错，要求先关闭旧进程，而不是自动换端口
- `AI_TUTOR_HOST` 只改变绑定地址，不改变端口；例如 `AI_TUTOR_HOST=127.0.0.1 python main.py`

当前作者本地用于图谱主流程与临时问答联调的常用启动命令：

```bash
GRAPH_RAG_ENABLE_LLM=true \
GRAPH_RAG_LLM_PROFILE=deepseek \
CHAT_PROFILE=deepseek \
LLM_PROVIDER=openai \
MODEL_NAME=deepseek-v4-flash \
python main.py
```

如果使用千问链路，可切换为：

```bash
GRAPH_RAG_ENABLE_LLM=true \
GRAPH_RAG_LLM_PROFILE=qwen \
CHAT_PROFILE=qwen \
LLM_PROVIDER=openai \
MODEL_NAME=qwen-plus \
python main.py
```

补充说明：

- 以上命令默认都在项目根目录执行，不依赖任何机器上的绝对路径
- Linux、macOS、Windows、WSL 均应保持 `data/...`、`docs/...`、`frontend/...` 这类项目内相对路径口径
- 不同系统只需要调整 shell 的环境变量写法，不需要修改项目路径
- 当前临时问答路径与 Windows 的兼容性还未完全收敛，其他开发者接手时应优先同步调整本机启动脚本与环境注入方式

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
结束本轮学习，生成作业
```

选择结束本轮学习时，系统会生成作业并写入学生状态。

### 4.4 查看知识图谱

启动服务后打开：

```text
当前默认不再挂载历史 A2 viewer；如需查看旧资料，请直接打开 `docs/archive/a2-control-theory/viewer/index.html`。
```

或者在 Web 左侧点击“知识图谱”。

### 4.5 命令行运行方式

项目也保留 CLI 入口：

```bash
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

### 5.1.1 会话占位 / 恢复 API

前端点击“新对话”时，会先调用一个空会话占位接口，让历史栏在第一条消息发送前就拥有稳定 thread 记录：

```bash
curl -X POST http://127.0.0.1:8000/api/sessions \
  -H 'Content-Type: application/json' \
  -d '{"thread_id":"smoke-thread-001"}'
```

期望返回：

```json
{"status":"created","thread_id":"smoke-thread-001"}
```

再次调用同一个 `thread_id` 时，返回 `status="exists"`，这是预期的幂等行为。恢复继续学习则使用：

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/smoke-thread-001/resume
```

### 5.2 图谱完整性检查

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_graph_integrity.py
```

### 5.3 主流程聚焦回归

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

### 5.4 API E2E Smoke

不依赖浏览器，用 HTTP/SSE 跑通主流程：

```bash
# 完整主流程
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000

# 临时追问流程
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000 --flow temporary_question

# 两者都跑
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000 --flow both
```

覆盖：会话创建 → 主题启动 → SSE 消费 → 主题确认 → 测评作答 → 课后停顿 → 客观题 → 继续/作业选择 → 会话恢复。需要服务已启动且 LLM 已配置。

### 5.5 运行资产检查

```bash
bash scripts/check_runtime_assets.sh
```

检查图谱 B CSV/JSON、media_evidence_index、GraphRAGPipeline 配置和内部 dangling refs。

### 5.6 运行资产同步

如果 `data/media_evidence_index`、`data/mineru_cache` 或归档 viewer 投影 `docs/archive/a2-control-theory/viewer/data.js` 异常：

```bash
scripts/sync_knowledge_map_runtime_assets.sh
```

脚本会恢复图谱 B 运行资产、构建媒体索引并检查可用性；如果归档 A2 图谱包存在，还会顺手刷新 `docs/archive/a2-control-theory/viewer/data.js` 这个兼容性静态工件。历史 A2 viewer 不是当前主教学图谱，只是归档资料。

## 6. 当前文档索引

建议按下面顺序阅读：

1. `docs/current-status-and-usage.md`：当前完成情况与使用方式。也就是本文。
2. `docs/next-iteration-plan.md`：下一步迭代计划，按优先级执行。
3. `docs/reports/2026-04-28-langgraph-final-closure-report.md`：2026-04-28 最终闭合报告，记录 88 项聚焦回归和图谱资产状态。
4. `docs/knowledge-map-runtime-assets.md`：运行资产同步说明。
5. `docs/plans/2026-04-30-interaction-artifact-validation-contract.md`：交互卡片、历史恢复与浏览器验收契约。
6. `docs/plans/2026-04-28-strict-kg-mastery-mainflow-plan.md`：严格主流程设计长计划，作为历史设计依据。

## 7. 严谨汇报口径

可以对外说：

> 当前系统已经完成知识图谱驱动节点制掌握学习主流程的主体闭合：从主题确认、学前诊断、图谱节点选择、节点内容加载、讲解、自然追问、节点后客观测试、错题补救、下一节点规划、作业生成，到二次登录恢复和作业处理，均已形成显式节点和可测试路由。知识图谱 B 负责学习路径、节点内容、临时追问和证据增强；GraphRAG 证据已按公式/图表/表格卡片化展示，媒体证据索引当前包含 11 个章节、2928 条标注资产。历史 A2 / Graph A 已归档，不作为当前主教学图谱。聚焦回归已通过。

必须补一句：

> 当前仍是可演示/可迭代原型，不是最终产品化版本。下一步应优先跑完整端到端浏览器/API 回归，扩充节点客观题、变式题和作业题库内容，并继续收敛跨系统启动、历史恢复和运行资产治理。
