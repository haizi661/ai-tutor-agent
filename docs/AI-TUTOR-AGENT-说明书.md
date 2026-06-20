# AI Tutor Agent 完整说明书

> 版本: 2026-06-21 | 模型: deepseek-v4-flash | 图谱: 42 节点, 95 边 | 题库: 630 题

## 一、系统概述

AI Tutor Agent 是一个**知识图谱驱动的节点制掌握学习**自适应伴学系统，专注于自动控制原理教学。

核心闭环：**主题确认 → 学前诊断 → 学习路径规划 → 节点讲解 → 课后追问 → 客观题测试 → 错题补救 → 节点推进 → 作业/结业**。

技术栈：Python 后端 (FastAPI + LangGraph) + vanilla JS 前端 + 知识图谱 (GraphRAG) + Chroma 向量库。

---

## 二、快速启动

```bash
# 安装
python -m pip install -r requirements.txt
cp .env.example .env   # 编辑 .env 填入 API Key

# 启动 (Web UI 固定 8000 端口)
GRAPH_RAG_ENABLE_LLM=true \
GRAPH_RAG_LLM_PROFILE=deepseek \
CHAT_PROFILE=deepseek \
LLM_PROVIDER=openai \
MODEL_NAME=deepseek-v4-flash \
python main.py

# 浏览器打开 http://127.0.0.1:8000

# 健康检查
curl http://127.0.0.1:8000/api/health  # → {"status":"ok"}
```

---

## 三、完整学习流程 (14 步)

```
用户进入
  → [Phase 1] intake_router → greeter → topic_confirmer → assessment_generator
  → [Phase 2] assessment_dialog → user_profiler → learning_plan_generator
  → [Phase 3] initial_node_selector
  → [Phase 4] node_content_loader → tutor
  → [Phase 5] post_lesson_choice → temporary_question → interruption_tutor
  → [Phase 6] objective_test_generator → scorer → remediation_decision
  → [Phase 7] next_node_planner → continue_or_homework_selector
  → [多节点轮转: Phase 4-7 循环...]
  → [Phase 8] homework_generator → completion_wrapup
```

### Phase 1: 入口与主题确认
**节点**: `intake_router → greeter → topic_confirmer → assessment_generator`

1. 用户打开 `http://127.0.0.1:8000`，看到课程方向选择卡片
2. 点击课程方向（如"自动控制原理"）→ 主题自动确认
3. 系统生成 **8 维自评配对题**（对应 A-H 能力维度）

### Phase 2: 学前测评与用户画像
**节点**: `assessment_dialog → user_profiler → learning_plan_generator`

1. 用户逐题作答 8 道配对题（每题含自评 + 实测）
2. `user_profiler` 计算：
   - **difficulty_level** (1-5)：按平均校准分映射
   - **teaching_strategy**：socratic / analogy / stepbystep / explain
   - **assessment_concept_gaps**：每个概念的 calibrated 校准分 (0.3×自评 + 0.7×实测)
3. `learning_plan_generator` 基于画像 + 知识图谱生成多步学习路径

**8 个能力维度**:
| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| 数学基础 | 基本概念 | 系统建模 | 稳定性分析 | 时域分析 | 稳态误差 | 根轨迹 | 频域分析 |

### Phase 3: 初始节点选择
**节点**: `initial_node_selector`

1. 从 `learning_plan.steps[0]` 选择第一个节点
2. 首个节点**强制 `full_learning`**（确保从头完整学习）
3. 设置 `current_node_id`、`current_node_name`

### Phase 4: AI 教学讲解
**节点**: `node_content_loader → tutor`

1. `node_content_loader` 加载节点教学内容：
   - 学习目标、必会点、常见误区、前置知识
   - 媒体证据（公式、图表、表格 — 来自 MinerU + media_evidence_index）
2. `tutor` 按 `teaching_strategy` 生成 650-1000 字讲解：
   - `socratic`：苏格拉底引导法（暴露盲点）
   - `analogy`：类比教学（建立信心）
   - `stepbystep`：分步推进（整体掌握良好时）
   - `explain`：直接讲解（一般情况）

### Phase 5: 课后停顿与临时追问
**节点**: `post_lesson_choice → temporary_question_collector → interruption_tutor`

1. 讲解完成后显示课后停顿卡，三种交互方式：
   - **自由输入卡点**（如"还是没太明白负反馈判断"）→ 直接进入临时追问
   - **点击"继续追问"** → 进入临时追问
   - **点击"我懂了，进入小测"** → 进入客观题测试
2. 临时追问走 **GraphRAG 2.2** 检索证据增强回答
3. 回答完成后回到课后停顿（可多轮追问）

### Phase 6: 客观题测试与错题补救
**节点**: `objective_test_generator → objective_test_scorer → remediation_decision`

1. 生成 10 道四选一客观题（优先从题库 420 题抽取，不足时 LLM 补齐）
2. 用户提交答案 → `objective_test_scorer` 用 answer_key 自动评分
3. 评分结果：
   - **≥60% 通过**：标记 `current_node_status = "passed"` → 进入 Phase 7
   - **<60% 未通过**：显示错题解析 → `remediation_decision` 三个选项：
     - `review_node`：重新教学当前节点
     - `do_later`：加入错题本，延后复习，推进下一节点
     - `still_do_variant`：继续做变式训练（最多 2 轮）

### Phase 7: 节点推进与学习决策
**节点**: `next_node_planner → continue_or_homework_selector`

1. `next_node_planner` 按学习路径 Step 推进：
   - 当前 Step 内找下一个未学节点
   - Step 完成 → 推进下一步
   - 全部 Step 完成 → `plan_completed`
2. `continue_or_homework_selector` 根据状态展示选项：
   - **正常**: "继续下一节点" / "今天就到这里"
   - **plan_completed**: "开始新一轮" / "今天就到这里"
   - **all_mastered**: "开始新一轮" / "巩固薄弱点" / "查看报告" / "今天就到这里"

### Phase 8: 作业生成与结业总结
**节点**: `homework_generator → completion_wrapup`

1. 用户选择"今天就到这里" → `homework_generator` 三级抽题策略：
   - Tier 1: 从题库取题（`homework_questions.jsonl`）
   - Tier 2: 从图谱节点构建作业
   - Tier 3: 模板兜底题
2. 全部节点 mastered 后 → `completion_wrapup` 生成 LLM 学习总结：
   - 学习概览（已掌握知识体系）
   - 能力评估（各维度掌握度）
   - 下一步建议 + 复习作业

---

## 四、学习路径生成算法

### 核心流程
```
build_learning_plan():
  1. 图谱 prerequisite_of 拓扑排序 (BFS)
  2. 评估 calibrated ≥ 60 标记已掌握 → 跳过
  3. 同层节点按评估分低优先（薄弱概念先学）
  4. 每 Step 最多 3 节点
  5. 同 chapter 节点聚合为一步
```

### 概念→节点模糊匹配 (learning_plan_builder._fuzzy_match_node)
评估生成的 concept title（如"基本概念"）映射到知识图谱节点（如 KM001）。5 维加权打分：

| 维度 | 权重 | 说明 |
|------|------|------|
| 精确名称匹配 | +1.0 | name == target |
| 子串包含 | +0.6 × len_ratio | target/name 长度比缩放，防后缀匹配过度加权 |
| 标签精确匹配 | +1.5 | tags 中的 tag == target |
| Bigram Jaccard | +0.7 × Jaccard | 字符二元组重叠度 |
| Containment ratio | +0.5 × containment × len_ratio | 字符集覆盖率 |
| 纯净标签加成 | +0.6 | tag 匹配但无子串重叠（纯语义匹配优于词汇巧合） |

min_score = 0.35，低于此阈值返回 None（概念与所有节点匹配度太低）。

---

## 五、知识图谱

### 图谱数据
- 节点: `data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv` (42 节点, KM001-KM042)
- 边: `data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv` (95 条 prerequisite_of)
- 元数据: `data/knowledge_map_outputs/auto_control_knowledge_map_v2_node_metadata.json`
- 媒体索引: `data/media_evidence_index/` (2928 条标注资产)
- MinerU 缓存: `data/mineru_cache/`

### 题库
| 题库 | 文件 | 数量 | 状态 |
|------|------|------|------|
| 测评题 | `assessment_questions.jsonl` | 10 | 最小可用 |
| 客观题 | `objective_questions.jsonl` | 420 (42×10) | ✅ 完成 |
| 变式题 | `variant_questions.jsonl` | 210 (42×5) | ✅ 完成 |
| 作业题 | `homework_questions.jsonl` | 3 | 待扩充 |

路径: `data/question_bank/a2-control-theory/`

---

## 六、技术架构

### 目录结构
```
ai_tutor_agent/
  core/              — 状态 (AgentState)、事件、学习路径算法
  nodes/             — 29 个 LangGraph 教学节点
  orchestration/     — workflow.py (节点注册 + 路由)
  infrastructure/    — LLM、RAG、向量库、题库 Provider
  interfaces/api/    — FastAPI 路由 + SSE 流式 + 账户认证 (auth.py)
  ai_learning_path/  — AI 课程学习路径模块 (双课程模式)
frontend/
  assets/js/         — 前端逻辑 (session, ui, history, state)
  assets/vendor/     — marked, katex (本地渲染)
backend/             — [独立服务] Flask + LangChain Agents + SQLAlchemy + PaddleOCR
kg_builder_standalone/ — [独立工具] 知识图谱构建管线
data/                — 图谱、题库、学生状态、向量库
tests/               — 754 个测试 (pytest)
scripts/             — 录制、验证、题库生成脚本
```

### 关键路由 (workflow.py)
29 个注册节点，条件边覆盖全部流程分支。入口判断: `get_entry_node()` 根据 `flow_status` / `learning_resume_target` / `is_assessed` 决定起始节点。

### 会话恢复 (session_resume_router)
二次登录时根据 `StudentState` 分流：
- 有作业 → `homework_review`
- 学习中 → 续上 `learning_plan`
- 课后停顿 → `post_lesson_choice`
- 小测中 → `objective_test_scorer`
- 继续/作业 → `continue_or_homework_selector`

### 学生状态持久化
`data/student_states/*.json`（StudentStateStore），包含 knowledge_graph (节点掌握)、wrong_question_book (错题本)、homework_assignments、learning_plan_v2。

---

## 七、子模块说明

主仓库除核心 LangGraph 教学流程外，还包含以下可独立运行/引用的模块：

### 7.1 智能体后端 (`backend/`)
**技术栈**: Flask + LangChain Agents + SQLAlchemy + PaddleOCR  
**功能**: 四个独立 Agent（error_correction、note、solve、teach）  
**状态**: 独立服务，**未接入**主 LangGraph 流程  
**启动**: `cd backend && python app.py`（需额外安装 backend/requirements.txt）

### 7.2 知识图谱构建管线 (`kg_builder_standalone/`)
**功能**: 独立的知识图谱构建工具，从原始教材/讲义自动构建知识图谱  
**产出**: 9 版 demo graph 演进记录（v1-v9）  
**状态**: 独立工具，主教学图谱 B 已预置在 `data/knowledge_map_outputs/`

### 7.3 AI 学习路径模块 (`ai_tutor_agent/ai_learning_path/`)
**功能**: 双课程模式支持（auto_control / artificial_intelligence）  
**包含**: 路由、服务层、课程资产构建器  
**状态**: 已集成到主 LangGraph 流程，欢迎页根据课程方向分流

### 7.4 其他集成
- **账户认证**: `ai_tutor_agent/interfaces/api/auth.py` — PBKDF2 密码哈希 + token 认证
- **MATLAB 仿真**: `ai_tutor_agent/infrastructure/matlab_experiment.py` — 自然语言 → MATLAB 代码 → 执行 → 结果分析

---

## 八、前端交互卡片

支持的 `pending_interaction_kind`:

| Kind | 触发时机 | 卡片行为 |
|------|---------|---------|
| `topic_confirmation` | 主题模糊需确认 | 确认/修改主题 |
| `assessment_dialog` | 测评逐题 | stepper 逐题作答 |
| `post_lesson_choice` | 讲解完成 | 自由追问 / 进入小测 |
| `objective_test_answers` | 客观题生成 | 10 题选择卡 |
| `remediation_decision` | 小测未通过 | 复习/稍后/变式 |
| `continue_or_homework_choice` | 节点通过 | 继续/作业/新一轮 |
| `homework_review_choice` | 作业已布置 | 复习/作答 |
| `homework_answers` | 作业作答 | 提交作业答案 |

---

## 九、演示视频

完整流程分阶段录制在 `scripts/phase_recordings/`：

| 阶段 | 视频 | 时长 | 内容 |
|------|------|------|------|
| Phase 1 | `phase01_entry_topic.webm` | 11s | 入口→主题确认→测评生成 |
| Phase 2 | `phase02_assessment_profiling.webm` | 17s | 测评作答→画像→学习路径 |
| Phase 3 | `phase03_learning_plan.webm` | 1s | 学习路径面板+初始节点 |
| Phase 4 | `phase04_tutor_teaching.webm` | 4m | AI教学讲解(含LLM等待) |
| Phase 5 | `phase05_post_lesson_temporary.webm` | 24s | 课后停顿→自由追问→RAG回答 |
| Phase 6 | `phase06_objective_test_remediation.webm` | 2m42s | 客观题→评分→错题补救 |
| Phase 7 | `phase07_node_progression.webm` | 16s | 节点推进→学习决策 |
| Phase 8 | `phase08_homework_completion.webm` | 15MB | 作业生成→结业总结 |
| 完整 | `00_full_flow.webm` | 21MB | 全部阶段完整视频 |

详细映射文档: `scripts/phase_recordings/PHASE_VIDEOS.md`

---

## 十、验证命令

```bash
# 全量测试
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
# 期望: 754 passed, 5 skipped, 5 warnings

# API E2E 验证 (需要服务运行)
python scripts/real_e2e_verify.py

# 图谱完整性
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_graph_integrity.py

# 核心流程聚焦回归
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_workflow.py \
  tests/test_objective_learning_flow.py \
  tests/test_learning_plan.py \
  tests/test_session_resume_router.py

# 前端契约测试
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_frontend_objective_test_ui.py \
  tests/test_frontend_learning_content_layout.py \
  tests/test_frontend_html_safety.py \
  tests/test_homework_learning_ui_contract.py

# 运行资产检查
bash scripts/check_runtime_assets.sh

# 全流程录制
python scripts/record_demo_flow.py          # 原始录制 (9 节点轮转)
python scripts/record_phases_v2.py          # 分阶段录制 (8 阶段)

# 服务健康检查
curl http://127.0.0.1:8000/api/health
```

---

## 十一、当前状态与下一步

### 已完成
- 14 步主流程完整闭合 (29 个 LangGraph 节点)
- 42 节点知识图谱 + GraphRAG 2.2 证据增强
- 客观题库 420 题 + 变式题库 210 题 (覆盖全部节点)
- 学习路径 v2 简化 (纯拓扑 BFS + 分支优先级)
- 概念模糊匹配 (5 维加权打分)
- 错题本 + 题目答疑 + 客观题复盘
- 结业总结 (completion_wrapup)
- 前端交互卡片完整支持 8 种 pending_interaction_kind
- 全量测试 754 passed

### 待完成 (详见 docs/next-iteration-plan.md)
- 作业题库扩充 (当前仅 3 题)
- 真实浏览器/API 端到端回归扩展
- 错题本"复习本节点"/"再做一遍"/排序控件
- 题目答疑流式输出
- 变式训练硬边界 (连续错误阈值)
- 用户画像升级为长期学习者模型

详细计划见: `docs/next-iteration-plan.md`
