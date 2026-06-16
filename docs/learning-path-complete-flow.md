# AI Tutor Agent 完整学习路径流程

更新时间：2026-06-16

本文档描述从用户进入系统到完成学习的完整链路，以及学习路径生成的核心算法。

---

## 一、总览：14 步主流程

```
用户进入
  → intake_router → greeter                  (意图识别)
  → topic_confirmer                          (主题确认)
  → assessment_generator → assessment_dialog (8 维自评 + 配对实测)
  → user_profiler                            (画像 + 难度等级)
  → learning_plan_generator  ★核心            (生成自适应学习路径)
  → initial_node_selector                    (选第一个节点)
  → node_content_loader                      (加载节点内容)
  → tutor                                    (按 entry_mode 讲解)
  → post_lesson_choice                       (课后停顿：追问 / 小测)
  → objective_test_generator → scorer        (10 道客观题)
  → next_node_planner                        (Step 内推进 / 下一步)
  → continue_or_homework_selector            (继续 / 作业 / 新一轮)
  → homework_generator                       (抽题布置作业)
  → completion_wrapup                        (全部 mastered 后总结)
```

---

## 二、各步骤详解

### 步骤 1：intake_router → greeter

**入口路由**，判断用户意图：

- `flow_status == "greeting"` → 打招呼，进入 `greeter`
- `flow_status == "topic_intake"` → 输入了学习主题，进入 `greeter` 提取主题
- `flow_status == "meta_qa"` → 元问题（"你是谁"），进入 `meta_qa`
- `flow_status == "smalltalk"` → 闲聊，进入 `smalltalk`

### 步骤 2：topic_confirmer

确认学习主题。如果用户输入了模糊主题，LLM 会向用户确认具体范围。确认后设置 `current_topic`。

**路由分支**：
- `awaiting_topic_confirmation` → 暂停等用户确认
- 确认完成 → 进入 `assessment_generator`

### 步骤 3：assessment_generator → assessment_dialog

生成 **8 维自评题**（对应 A-H 能力维度），每道题包含：
- 自评部分（A=非常熟悉 / B=基本了解 / C=不太熟 / D=完全不会）
- 配对的实测题（客观题，用于校准自评准确性）

用户逐题作答，`assessment_dialog` 逐题收集答案直到全部完成。

**8 个能力维度**：

| 代码 | 名称 |
|------|------|
| A | 数学基础 |
| B | 控制系统基本概念 |
| C | 系统建模能力 |
| D | 稳定性分析能力 |
| E | 时域性能分析能力 |
| F | 稳态误差分析能力 |
| G | 根轨迹分析能力 |
| H | 频域分析与校正能力 |

### 步骤 4：user_profiler

根据测评答案计算：

- **`assessment_concept_gaps`**：每个概念的 calibrated 校准分（`0.3×自评 + 0.7×实测`），含 `gap_type`（overconfident / underconfident / aligned_high / aligned_low）
- **`difficulty_level`**（1-5）：按平均校准分映射
  - `avg ≤ 20` → level 1 | `avg ≤ 40` → level 2 | `avg ≤ 60` → level 3 | `avg ≤ 80` → level 4 | `avg ≤ 100` → level 5
- **`teaching_strategy`**：按差距模式选择
  - `overconfident ≥ threshold` → socratic（苏格拉底引导法）
  - `underconfident ≥ threshold` → analogy（类比教学）
  - `aligned_high ≥ 50%` → stepbystep（分步推进）
  - 一般情况 → explain（直接讲解）

输出到 `AgentState`，同时存入 `StudentState`。

### 步骤 5：learning_plan_generator ★

这是学习路径生成的核心节点。详细流程见[第三章](#三learning_plan_generator-内部流程)。

### 步骤 6：initial_node_selector

从 `learning_plan.steps[0]` 选择第一个节点。首个节点**强制 `full_learning`**（确保每个学习轮次的第一个节点从头完整学习）。

设置 `current_node_id`、`current_node_name`。

### 步骤 7：node_content_loader

加载当前节点的教学内容：
- 学习目标（learning_objectives）
- 必会点（key_points）
- 常见误区（common_misconceptions）
- 前置知识（prerequisites）
- 媒体证据（公式、图表、表格 — 来自 `mineru_cache` + `media_evidence_index`）

### 步骤 8：tutor

按 `entry_mode` 进行教学：

| entry_mode | 行为 |
|------------|------|
| `full_learning` | 完整讲解（650-1000 字），含前置关联、错题反馈、情绪调整 |
| `short_learning` | 精简讲解，覆盖核心要点 |
| `quick_check` | 仅出 2 道检测题，通过即跳过 |

教学策略（`teaching_strategy`）影响讲解方式：
- `socratic`：苏格拉底引导法，暴露盲点
- `analogy`：类比教学，建立信心
- `stepbystep`：分步推进，整体掌握良好时用
- `explain`：直接讲解，一般情况

### 步骤 9：post_lesson_choice（课后停顿）

讲解完成后，用户可选择：

- **"继续追问"** → 进入 `temporary_question_collector` → `interruption_tutor`
  - 走图谱 2.2 / RAG 检索，返回证据增强的回答
  - 回答完成后再回到课后停顿
- **"我懂了，进入小测"** → 进入 `objective_test_generator`
- **自由输入卡点**（如"还是没太明白负反馈判断"）→ 直接进入临时追问

### 步骤 10：objective_test_generator → scorer

生成 **10 道四选一客观题**，用户提交答案后自动评分：

- **通过（≥ 60%）**：标记 `current_node_status = "passed"`，进入 `next_node_planner`
- **未通过**：进入 `wrong_question_explainer` → `variant_question_generator`（变式题）→ 重测
  - `remediation_decision` 判断补救路径：
    - `review_node` → `node_content_loader`（重新教学当前节点，立即复习）
    - `do_later` → `next_node_planner`（加入错题本，延后复习，推进到下一节点）
  - 决策依据：分数段 + 复习历史（低分倾向 review_node，部分分倾向 do_later）

### 步骤 11：next_node_planner

按学习路径推进节点：

1. 在**当前 Step** 内找下一个未访问节点
2. 当前 Step 完成 → 推进到**下一步**（`new_step_idx++`）
3. 全部 Step 完成 → `plan_completed`
4. 兜底：`recommend_next_node()`（图谱前置关系推荐）

### 步骤 12：continue_or_homework_selector

询问用户下一步意图：

**正常情况**：
- "开始下一个节点" → 回到步骤 7（`node_content_loader`）
- "今天不学了，生成作业" → `homework_generator`

**plan_completed / all_mastered 额外选项**：
- "开始新一轮完整学习" → 回到步骤 5（`learning_plan_generator`，`include_all=True`）
- "只巩固薄弱点" → 回到步骤 5（`force_review=True`）
- "查看学习报告" → `completion_wrapup`
- "今天就到这里" → `homework_generator`

### 步骤 13：homework_generator

优先从 **runtime question bank**（`data/error_correction_runtime/question_bank/questions.json`）抽取 1-2 道相关题。无题库时 fallback 到 AI 生成或模板题。

作业写入 `StudentState.homework_assignments`，下次登录时由 `session_resume_router` 恢复。

### 步骤 14：completion_wrapup

全部节点 mastered 后，LLM 生成：
- 学习概览（已掌握知识体系）
- 能力评估（各维度掌握度）
- 下一步建议
- 附带复习作业

---

## 三、learning_plan_generator 内部流程

### 3.1 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `self_assessment_scores` | AgentState / StudentState | 8 维自评分数 `{A: 1-5, B: 1-5, ...}` |
| `skip_self_assessment` | AgentState | 是否跳过了自评 |
| `assessment_concept_gaps` | AgentState | 测评校准分（步骤 4 产出） |
| `difficulty_level` | AgentState | 难度等级 1-5（步骤 4 产出） |
| `wrong_question_book` | StudentState | 错题本（用于 context_boost） |
| `question_help_records` | StudentState | 答疑记录（用于 context_boost） |
| `concept_mastery` | StudentState | 持久化的 42 节点掌握度 |
| `learning_plan_v2` | StudentState | 上次的路径（用于 resume） |
| `session_index` | StudentState | 第几次学习会话 |
| 图谱数据 | `data/knowledge_map_outputs/` | 节点 metadata + 前置关系边 |

### 3.2 流程

```
Step 1: Try resume
  └─ 已有 in_progress plan 且无新的自评 → 续上旧 plan，刷新 entry_mode
     └─ 返回 (不重新生成)

Step 2: Build StudentProfile
  ├─ 有自评分 → init_from_self_assessment(8维 → 42节点 mastery)
  └─ 跳过自评 → init_from_default()（静态默认值）

Step 3: 合并测评校准分 ★
  └─ _merge_assessment_gaps()
     将 assessment_concept_gaps 的 calibrated 值按 ability 维度
     写入 profile.concept_mastery，修正 mastery + 提升 confidence

Step 3.5: 计算上下文加成
  ├─ context_boost: 错题本(+0.12/题) + 临时提问(+0.08/条)
  └─ freshness_boost: 从未被规划过的节点获得加成(0.25~0.55)

Step 4: 读取 difficulty_level → 路径粒度 ★
  ├─ level 1 → 5 步, 5-8 节点, 每步 1-2 节点 (弱基础)
  ├─ level 2 → 5 步, 7-10 节点, 每步 1-3 节点
  ├─ level 3 → 4 步, 9-12 节点, 每步 2-4 节点 (默认)
  ├─ level 4 → 4 步, 10-14 节点, 每步 2-4 节点
  └─ level 5 → 3 步, 12-16 节点, 每步 3-5 节点 (强基础)

Step 5: generate_learning_plan_v2() — 7 步算法
  ├─ [1] 候选集 = 全图谱 42 节点 - 已 mastered(≥0.85 & confidence≥0.7)
  ├─ [2] 紧迫度 = 0.35×gap + 0.15×uncertainty + 0.30×failure_hist + 0.20×context_boost
  ├─ [3] 拓扑排序 (按 prerequisite_of 边 BFS)
  ├─ [4] select_nodes ★ 加权复合评分:
  │      composite = 0.60×urgency + 0.15×importance + 0.05×depth
  │                 + 0.05×difficulty + 0.15×id_tiebreaker
  │      选 node_range 内的节点
  ├─ [5] cluster_into_steps (按 primary_ability 聚类, 章序约束)
  ├─ [6] resolve_entry_modes (每节点: full_learning / short_learning / quick_check)
  └─ [7] LLM 生成 step 主题名 (失败时用首节点名兜底)

Step 6: 持久化
  └─ 写入 StudentState (concept_mastery + learning_plan_v2 + session_index)
  └─ 更新 AgentState snapshot
```

### 3.3 输出：LearningPlan 结构

```python
LearningPlan:
  steps: [
    StepEntry(
      step_index=0,
      step_name="建立自动控制基础",     # LLM 生成的主题名
      step_goal="掌握控制系统基本概念",
      step_ability="B",
      chapter="第一章",
      node_ids=["KM001", "KM002", "KM003"],
      entry_modes={                       # 每个节点的教学模式
        "KM001": "full_learning",
        "KM002": "short_learning",
        "KM003": "quick_check",
      },
      reason="主攻控制系统基本概念；章节：第一章",  # 解释为什么这样排
      status="in_progress"               # pending / in_progress / completed
    ),
    StepEntry(
      step_index=1,
      step_name="掌握数学建模",
      ...
      status="pending"
    ),
    ...
  ],
  total_nodes=12,
  total_steps=4,
  generated_at="2026-06-09T...",
  source="cold_start",                   # cold_start / replan / resume
  session_index=0
```

### 3.4 紧迫度（Urgency）公式

```
urgency(node) =
  0.35 × (1 - mastery)          # 掌握度缺口
  + 0.15 × (1 - confidence)     # 不确定度
  + 0.30 × failure_penalty      # 失败惩罚 (失败 1 次=0.3, 2 次=0.6, 3+=1.0)
  + 0.20 × context_boost        # 上下文加成 (错题+提问)
```

### 3.5 entry_mode 决策规则

| 条件 | entry_mode |
|------|-----------|
| `failure_count ≥ 2` | `full_learning` |
| `mastery ≥ 0.8 & confidence ≥ 0.5` | `quick_check` |
| `mastery ≥ 0.7 & confidence ≥ 0.3` | `quick_check` |
| `mastery ≥ 0.5`（高难度+核心除外） | `short_learning` |
| `source == "self_assessment" & mastery < 0.5` | `full_learning`（自评薄弱） |
| `source == "default" & mastery < 0.5` | `full_learning`（冷启动保守） |
| 简单节点 `mastery ≥ 0.35` | `short_learning` |
| 其余 | `full_learning` |

**首节点保护**：每个轮次的第一个节点由 `initial_node_selector` 强制设为 `full_learning`。

---

## 四、会话恢复（Resume）

二次登录时，`session_resume_router` 根据 `StudentState` 状态分流：

```
session_resume_router:
  ├─ homework_assigned → homework_review → 作答 / 讲解
  ├─ in_progress learning_plan_v2
  │   └─ learning_plan_generator (续上 + 刷新 entry_mode)
  ├─ awaiting_post_lesson_choice → post_lesson_choice
  ├─ awaiting_objective_answers → objective_test_scorer
  ├─ awaiting_continue_or_homework_choice → continue_or_homework_selector
  ├─ awaiting_temporary_question → temporary_question_collector
  └─ 其他 → tutor (直接继续教学)
```

恢复时：标题恢复为学习主题 + 当前节点名，当前待处理卡片滚动到可视区，底部输入框不遮挡。

---

## 五、核心数据流

```
                    ┌──────────────┐
                    │  AgentState  │  (单次会话状态, 不持久化)
                    └──────┬───────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
assessment        learning_plan          teaching 相关
concept_gaps      steps[]                tutor_content
difficulty_level  entry_modes            post_lesson_choice
self_assessment   current_step_idx       objective_questions
  _scores         plan_source            current_node_id

                    ┌──────────────┐
                    │ StudentState │  (持久化到 data/student_states/*.json)
                    └──────┬───────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
knowledge_graph       learning_plan_v2       wrong_question_book
(节点掌握状态)         (完整路径+entry_modes)   (错题本)

concept_mastery       visited_nodes          question_help_records
(42节点 mastery+       wrong_nodes            (答疑记录)
 confidence)
                      homework_assignments   session_index
                      (作业)                 (第几次会话)
```

---

## 六、关键配置与文件位置

| 项目 | 路径 |
|------|------|
| 图谱节点 (42 个) | `data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv` |
| 图谱边 (240 条) | `data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv` |
| 节点元数据 (ability_weights 等) | `data/knowledge_map_outputs/auto_control_knowledge_map_v2_node_metadata.json` |
| 学生状态存储 | `data/student_states/*.json` |
| 媒体证据索引 (2928 条) | `data/media_evidence_index/` |
| MinerU 缓存 | `data/mineru_cache/` |
| 题库 (runtime) | `data/error_correction_runtime/question_bank/questions.json` |
| 工作流编排 | `ai_tutor_agent/orchestration/workflow.py` |
| 路径生成器 V2 | `ai_tutor_agent/core/learning_plan_v2.py` |
| 路径生成器节点 | `ai_tutor_agent/nodes/learning_plan_generator.py` |
| 学生画像 | `ai_tutor_agent/core/student_profile.py` |
| 能力映射 | `ai_tutor_agent/core/ability_mapper.py` |
| 学习路径面板（前端） | `frontend/assets/js/ai_path.js` |

---

## 七、完整验证命令

```bash
# 全量测试
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
# 期望: 754 passed, 5 skipped, 5 warnings

# 核心流程聚焦回归
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_workflow.py \
  tests/test_objective_learning_flow.py \
  tests/test_learning_plan.py \
  tests/test_learning_plan_v2.py \
  tests/test_session_resume_router.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_temporary_question_flow.py

# API E2E (需要服务运行)
python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000 --flow both

# 图谱完整性
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_graph_integrity.py
```
