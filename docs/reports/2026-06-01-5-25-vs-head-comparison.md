# 5/25 e56fb96 vs HEAD:工作差异汇报文档

更新时间:2026-06-01
作者:[汇报人]
对比基准:
- **5/25 基准**:`e56fb96` (2026-05-25,origin/524yang / 0520pan 分支最后一条 commit,代表 ytun-y "人工智能知识图谱 3.0" 完成态)
- **现在 HEAD**:`6e3a317` (haizi661 分支,领先 origin 12 个提交,代表当前主线)

> 重要事实纠正(避免汇报翻车):**5/25 那个版本不是"老的 Tutor→Tester→Evaluator 闲聊循环"**。5/25 时 LangGraph 主流程已经基本搭好,27 个节点已经全部注册,Graph B 数据也已经齐全。真正的工作是**「在已搭好的主流程骨架上加肉」**——加教学契约、错因推断、出题蓝图、变式题补救、多步学习路径、统一学习方向、补题库、补测试、补文档、补工具。

---

## 0. 一句话总览

5/25 时,自动控制原理(Graph B)的 LangGraph 主流程框架已经搭好但**关键算法没落地**;人工智能知识图谱是**独立子服务**,与主流程互不通气。现在 HEAD:
- **自动控制原理**:在主流程上加 1 个新节点 + 5 个节点大改 + 12 个 AgentState 字段 + 1 套题库,完整闭环可跑
- **人工智能**:仍走独立子服务,但通过 `learning_track` 字段与主流程统一入口和会话状态
- **共享层**:学习方向 API、会话持久化、错题本、临时问题侧弹窗、题库、教学契约、HTML 安全、运行态检查全部共用

Working tree 还有 42 处未提交修改,属于"学习路径 v2"和"教学能力优化"两波正在做的下一步工作,不算入已交付范围。

---

## 1. 分支拓扑与基线

```
d422e8c 2026-05-03 (分叉点) "feat: KG architecture, evidence unification, session resume fixes, 452 tests"
│
├── 0520pan / origin/524yang  ──→ e56fb96 2026-05-25 路径学习状态读取更新 (5/25 基准)
│                                  (5/20-5/25 期间做了 AI 知识图谱 1.0/2.0/3.0)
│
└── haizi661 (当前主分支) ──→ 6e3a317 HEAD (领先 origin 12)
                              │
                              ├── 0f2186a 5/26 主流程融合打通:接入知识图谱与临时会话,融合 25 号功能
                              ├── 7521feb 5/28 学习方向 API + session 状态
                              ├── 66d7f2d 5/28 runtime assets check + API E2E smoke
                              ├── 9cbe374 5/28 学习方向 UI + 课程选择卡
                              ├── d58a7c1 5/28 文档全更新
                              ├── ada1f66 5/28 UI contract 测试
                              ├── ae668bb 5/28 un-ignore AI 路径数据
                              ├── 82c277f 5/28 修 merge 冲突 + 集成 learning path builder
                              ├── f24f3f4 5/28 userKnowledgeGraph key 改用 node_id
                              ├── e1a0e75 5/28 chat 内学习路径卡片
                              ├── 737c751 5/28 集成固定学习路径显示
                              ├── e3ca182 5/28 chat 右侧独立学习路径面板
                              └── 6e3a317 5/30 cherry-pick:图谱内容讲解补全 + 修 next_nodes
```

> 5/25 e56fb96 那波 AI 路径分支**没有通过 merge 进入主分支**(merge-base 检查 not in HEAD),但**它的功能通过 0f2186a "主流程融合打通"被吸收进主 LangGraph workflow**——同一个 `ai_tutor_agent/ai_learning_path/` 目录在 HEAD 树里,git 历史不同而已。

---

## 2. 数字汇总

| 维度 | 5/25 e56fb96 | 现在 HEAD | 增量 |
|---|---|---|---|
| LangGraph 节点数 | 27 | 28 | +1 (remediation_decision) |
| workflow.py 行数 | 744 | 774 | +30 |
| objective_test.py | 570 行 | 1409 行 | **+839** |
| next_node_planner.py | 59 行 | 174 行 | +115 |
| tutor.py | 1463 行 | 1648 行 | +185 |
| node_content_loader.py | 278 行 | 339 行 | +61 |
| session.py(API 层) | 737 行 | 917 行 | +180 |
| AgentState 字段 | 94 | 106 | +12 |
| 前端 JS 文件数 | 9 | 11 | +2 (question-help, wrong-book) |
| 测试文件 | 1 (test_ai_learning_path_progress) | 30+ | +29 |
| 题库 | 0 道 | 30 道 | +30 |
| 设计文档 | 几乎无 | 4 份 plans/ + 4 份 docs/ | +8 |
| Runtime 工具 | 无 | 3 个 | +3 |
| `git diff --stat` | — | — | 314 files / +29934 / -41451 |

---

## 3. 自动控制原理 vs 人工智能:分流机制

| 维度 | 自动控制原理 (Graph B) | 人工智能 (AI 知识图谱) |
|---|---|---|
| 数据源 | `data/knowledge_map_outputs/auto_control_knowledge_map_v2_{nodes,edges,graphml,json}` | `data/knowledge_map_outputs/artificial_intelligence/{ai_nodes.csv, ai_edges.csv}` |
| 节点规模 | 42 节点 / 95 边 / 9 章节 | 228 节点 / 1494 边 |
| 学生状态目录 | `data/student_states/{student_id}.json` | `data/student_states/artificial_intelligence/ai_student_state.json` |
| 教学执行位置 | **主 LangGraph workflow**(wf 节点运行) | **独立子服务** `ai_tutor_agent/ai_learning_path/ai_path_service.py` |
| API 入口 | `/api/start`、`/api/answer`、`/api/confirm_topic` 等主流程接口 | `/api/ai-path/{status,chat,teach,next,node/{id},reload}` 6 个独立接口 |
| 前端入口 | `frontend/assets/js/session.js` + `ui.js` 主聊天流 | `frontend/assets/js/ai_path.js` 独立右侧面板 |
| 题库 | `data/question_bank/a2-control-theory/{assessment,objective,variant,homework}_questions.jsonl` | **无题库**(全靠 LLM 生成 + fallback 模板) |
| 教学契约 | `node_teaching_contract` 注入 LLM,5/25 已有 | **无**,直接用节点字段拼 prompt |
| 客观小测 | 主流程 objective_test_scorer,门槛 80+必会 70% | **无**,mastery 直接写 0.85 |
| 错题补救 | wrong_question_explainer → remediation_decision → variant_question(2 轮上限) | **无** |
| 节点推进 | next_node_planner 按 learning_plan step 推进 | 顺序 path,跳过 mastered |
| 选节点切换 | `POST /api/sessions/{thread_id}/learning-direction` 设 `track=control_theory` | 设 `track=artificial_intelligence` |
| 触发时机 | 用户输入主题"自动控制原理"或选 control_theory 方向 | 用户选 artificial_intelligence 方向并确认 |

**关键设计**:两套教学体系**共用同一会话状态**(thread_id 唯一),但走两条独立子路径。前端用 `learningTrack` 字段在 `session.js` 和 `ai_path.js` 之间切换渲染区域。`/api/sessions/{thread_id}/learning-direction` 是切换开关。

---

## 4. LangGraph 节点清单对比

5/25 e56fb96 已注册 27 个节点(workflow.py 744 行)。HEAD 新增 1 个,共 28 个:

| 节点 | 5/25 | HEAD | 备注 |
|---|---|---|---|
| intake_router | ✓ | ✓ | |
| greeter / topic_confirmer | ✓ | ✓ | |
| meta_qa / smalltalk | ✓ | ✓ | |
| assessment_generator / assessment_dialog | ✓ | ✓ | |
| user_profiler | ✓ | ✓ | |
| learning_plan_generator | ✓ | ✓ | 5/25 已有,5/28 后实际跑通 |
| initial_node_selector | ✓ | ✓ | |
| **node_content_loader** | ✓ | ✓ | **5/25 后扩展 +61 行,加教学契约** |
| tutor | ✓ | ✓ | 5/25 后扩展 +185 行,加错因策略 + 契约兜底 |
| interruption_tutor | ✓ | ✓ | |
| post_lesson_choice | ✓ | ✓ | 5/25 已有,5/28 后行级调整 |
| temporary_question_collector | ✓ | ✓ | |
| objective_test_generator | ✓ | ✓ | 5/25 后大改 +839 行 |
| objective_test_scorer | ✓ | ✓ | 5/25 后大改 +839 行 |
| wrong_question_explainer | ✓ | ✓ | |
| **variant_question_generator** | ✓ | ✓ | 5/25 时只有 1 个 variant 函数,5/25 后扩成完整节点 |
| variant_test_answer_dialog | ✓ | ✓ | |
| **remediation_decision** | ❌ | ✓ | **HEAD 新增,340 行,从 wrong_question_explainer 抽离** |
| next_node_planner | ✓ | ✓ | 5/25 后扩展 +115 行,加 learning_plan 多步推进 |
| continue_or_homework_selector | ✓ | ✓ | |
| homework_generator / homework_review | ✓ | ✓ | |
| homework_answer_dialog / homework_scorer / homework_explainer | ✓ | ✓ | |
| session_resume_router | ✓ | ✓ | 5/25 后行级 +66 |
| next_step / post_eval_selector / post_eval_wrapup | ✓ | ✓ | |
| coach | ✓ | ✓ | |
| tester / evaluator | ✓ | ✓ | 旧"闲聊循环"残存,fallback 用 |

**结论**:节点框架是 5/25 之前就搭好的,5/25 → 现在的工作集中在**已有节点内部算法的丰富**,而不是新增节点。

---

## 5. 自动控制原理(Graph B 主线)关键改动

### 5.1 workflow.py

- **5/25**:744 行,27 个节点,条件路由已完整
- **HEAD**:774 行,新增 `remediation_decision` 节点注册和它的 4 条入边,以及一些"学习路径生成"路由函数 `route_after_learning_plan_generator`
- 增量 +30 行,主要是挂载新节点

### 5.2 新增节点:`remediation_decision.py`(340 行,全新)

5/25 时错题后的决策逻辑散在 `wrong_question_explainer` 和 `objective_remediation` 里。HEAD 抽成独立节点,带硬界限护栏:

```python
MAX_VARIANT_ROUNDS_PER_NODE = 2       # 单节点最多 2 轮变式
MAX_SAME_OBJECTIVE_FAILURES = 2       # 同一目标连续错 2 次即停
MAX_EXTRA_REMEDIATION_QUESTIONS = 10  # 额外补救题 ≤ 10 道
```

决策分支:
```
score >= 80         → 通过,跳到 next_node_planner
60 <= score < 80    → 决策卡 ① 继续变式训练 ② 复习本节点 ③ 稍后复习
score < 60          → 决策卡 ① 复习本节点 ② 稍后复习 ③ 仍然做变式训练
触达硬界限          → 决策卡 ① 复习本节点 ② 稍后复习(强制收束,不再加变式)
```

用户选择 → 学习阶段切换:`continue_variant` / `still_do_variant` → `variant_question_generator`;`review_node` → `node_content_loader`;`do_later` → `continue_or_homework_selector`。

### 5.3 节点内容装载:`node_content_loader.py`(278 → 339 行)

- **5/25**:只做 `build_graph_state_patch` + 简单上下文拼装
- **HEAD**:+61 行,新增 `_build_node_teaching_contract()` 生成教学契约:

```python
@dataclass  # 契约结构
{
    "node_id": "KM001",
    "node_name": "自动控制的一般概念",
    "learning_goal": "理解反馈控制系统的核心判断",       # 来自 learning_objectives[0]
    "prerequisites": [...],
    "must_know": [...],                                  # 来自 core_concepts/key_points
    "common_misconceptions": [...],                      # 来自 extra.common_errors
    "worked_example": "...",                             # 来自 examples[0]
    "assessment_targets": [                              # 出题蓝图
        {"target_objective": "...", "assessment_focus": "概念辨析",
         "misconception": "...", "required": True},
        ...
    ],
    "exit_criteria": [                                   # 退出条件
        "节点客观题总分达到 80 分",
        "关键目标正确率达到 70%",
        "常见误区题不能连续错 2 次",
    ],
}
```

契约进 `AgentState.node_teaching_contract`,被 tutor 和 objective_test_generator 共用。

### 5.4 教学:`tutor.py`(1463 → 1648 行)

新增算法:
1. **错因推断 + 策略选择**(`_infer_error_type` + `_select_strategy`):
   ```python
   _ERROR_TYPE_STRATEGY = {
       "concept_confusion": "socratic",   # 概念混淆 → 苏格拉底
       "calculation_error": "stepbystep", # 计算错误 → 逐步拆解
       "understanding_gap": "analogy",    # 理解偏差 → 换类比
       "carelessness": "explain",         # 粗心 → 强调细节
       "formula_error": "stepbystep",
       "method_confusion": "socratic",
   }
   # 优先看错因,其次看 attempt_count 轮转: 0→explain 1→analogy 2→stepbystep 3+→socratic
   ```
2. **教学契约 prompt 注入**(`_build_node_teaching_contract_prompt`):把契约转成 LLM 输入块,要求"必须覆盖学习目标 / 至少 2 必会要点 / 1 例子 / 1 误区 / 1 自检,220-420 字"
3. **教学长度兜底**(`_is_too_brief_node_lesson` + `_build_contract_lesson_fallback`):LLM 输出 < 120 字时用契约驱动的模板兜底
4. **教学标记门控**:`[MASTERY_ACHIEVED: id]` 标记需要 `turn_count >= 最小阈值`(识别層 1 / 理解層 3 / 应用層 5 / 分析層 7)才认

### 5.5 客观小测:`objective_test.py`(570 → 1409 行,**+839 行**)

这是 5/25 → 现在**改动最大的文件**。从单一 LLM 出题升级为"题库优先 → LLM 出题 → 模板兜底"三级流水线,加全套质量门控:

**新增的核心函数**:
```python
def _build_question_blueprints(state, node_id, node_name, count):
    """从契约 assessment_targets 抽出出题蓝图,锁定 target_objective/misconception/focus/difficulty/answer_key"""

def _normalize_ai_question_batch(raw_questions, *, state, ...):
    """校验 AI 出题:stem 非空 / options 必须是 A/B/C/D / answer_key 必须在 options 里"""

def _question_quality_errors(item):
    """质量门控:
        - missing_stem
        - invalid_options (不是 A/B/C/D)
        - invalid_answer_key
        - duplicate_options (4 个选项有重复)
        - option_too_long (> 95 字)
        - placeholder_or_template_text (含"第 1 个核心判断"等占位)
    """

def _is_unsuitable_focus_text(value):
    """过滤占位词:实例/示例/系统示例/自动控制/一般概念/核心概念/本节点/节点要点/... 24 个"""

def _build_actionable_explanation(focus, misconception, correct_text):
    """生成结构化解释:判断依据 + 正确理解 + 易错点"""

def _build_actionable_wrong_option_analysis(focus, misconception, option_text):
    """给每个错误选项生成针对性分析:这个选项把"X"当成结论,没有按 Y 判断"""
```

**scorer 改动**:
- 算分:`score = round(对题数 / 总数 * 100)`
- **通过条件**:`score >= pass_score=80` **且** `_contract_required_targets` 全部 ≥ 70% 正确率
- 必会目标分类汇总:`_build_objective_mastery_summary` 按 target_objective 分桶统计,定位薄弱必会点
- 写 `question_attempts` 记录,留 200 条
- 通过 → `next_node_planner`;未通过 → `wrong_question_explainer`

**10 道模板兜底**(`_fallback_questions`):当 LLM 也不工作时,内置 10 道围绕"被控对象 vs 控制装置 / 输入输出扰动 / 反馈判断 / 比较元件 / 闭环特征 / 测量元件 / 前向通路 / 主反馈通路 / 负反馈方向"的稳定题,确保任何节点都能出卷。

### 5.6 错题补救链路:整套(5/25 已有框架,5/25 后填血肉)

```
objective_test_scorer (score < 80)
    ↓
wrong_question_explainer (340 行)
    ├─ _generate_llm_explanations:对每道错题生成针对性讲解
    ├─ _build_wrong_question_prompt:含题干+答案+错因+正确项
    └─ _fallback_variant:模板兜底
    ↓
remediation_decision (340 行,5/25 后新增独立节点)
    ├─ 分数档判定:pass/partial/low
    ├─ 硬界限检查:变式轮数 / 同目标失败次数 / 额外题数
    └─ 用户选:continue_variant / review_node / do_later / still_do_variant
    ↓
variant_question_generator (5/25 已有,5/25 后扩)
    ├─ _generate_llm_variants:基于错题生成 5 道变式
    ├─ _build_variant_question_prompt:用错题的正确选项做干扰素材
    └─ _has_visible_variant_meta_text:检测"原题变体"等元信息泄露
    ↓
variant_test_answer_dialog
    ↓
objective_test_scorer (复测)
```

### 5.7 节点推进:`next_node_planner.py`(59 → 174 行)

- **5/25**:59 行,只有"找 next_node_candidate" 兜底逻辑
- **HEAD**:+115 行,加 learning_plan 多步推进:

```python
# 优先级: learning_plan step 内 → step 间 → 兜底
if learning_plan and current_step_idx < len(learning_plan):
    candidate = find_next_node_in_step(current_step, visited, current_node_id)
    if candidate:
        # reason = "same_step", source = "learning_plan"
    else:
        current_step["status"] = "completed"
        new_step_idx += 1
        if new_step_idx < len(learning_plan):
            # reason = "next_step", 进入下一步
        else:
            source = "plan_completed"  # 全走完,触发作业收束
```

持久化:`mutate_student_state_snapshot` 把 `learning_plan_current_step` 写进 `StudentState`。

### 5.8 继续/作业选择:`continue_or_homework_selector.py`(5/25 已有,行级微调)

简单节点,5/25 已有,5/25 后只调 18 行:接 learning_plan / next_node_candidate,选项固定为"开始下一个节点 / 今天不学了,生成作业"。

### 5.9 测评:`assessment.py`(5/25 已有,5/25 后扩)

- `assessment_concept_gaps` / `assessment_radar` / `difficulty_level` / `teaching_strategy` 5/25 已有
- 5/25 后加 `initial_user_knowledge_graph` 初始化 + GraphRAG 画像接入

### 5.10 会话恢复:`session_resume_router.py`(5/25 已有,5/25 后 +66 行)

5/25 后核心改动:`_has_homework` 用 blacklist 模式——`completed` / `submitted` / `deferred` 视为非活动,缺失或未知状态默认 active。保证新会话、刷新、历史恢复不丢作业。

### 5.11 临时提问 / 中断:`temporary_question_collector.py` + `interruption_tutor.py`(5/25 已有,5/25 后微调)

- `temporary_question_collector`:5/25 已有,5/25 后只接 answer_provider
- `interruption_tutor`:5/25 已有,5/25 后扩展 87 行(测试代码),`route_after_interruption` 5/25 后加 `awaiting_post_lesson_choice` / `learning_resume_target == post_lesson_choice` 分支

---

## 6. 人工智能(AI 知识图谱子服务)关键改动

### 6.1 独立子服务结构(5/25 时已基本成型,5/25 后未动核心)

```
ai_tutor_agent/ai_learning_path/
├── __init__.py
├── config.py                        # AI_NODES_CSV / AI_EDGES_CSV / AI_STUDENT_STATE_JSON
├── ai_path_service.py               # 1443 行,核心服务
├── ai_path_routes.py                # 46 行,FastAPI 路由
├── build_ai_nodes_from_seed.py      # 从种子构造节点的脚本
├── build_ai_edges_from_nodes.py     # 从节点构造边的脚本
└── normalize_ai_nodes.py            # 节点标准化
```

**6 个 API 端点**(都在 `ai_path_routes.py`):
```python
GET  /api/ai-path/status             # 图谱/学生状态摘要
POST /api/ai-path/reload             # 重新加载 CSV
POST /api/ai-path/chat               # 多轮澄清学习意图(DeepSeek 抽取)
GET  /api/ai-path/node/{id}          # 拿节点详情
POST /api/ai-path/teach              # 教当前节点
POST /api/ai-path/next               # 推进到下一节点
```

### 6.2 与主流程的桥接(0f2186a 5/26 做的关键改动)

5/25 时 AI 路径**完全独立**,与主 LangGraph workflow 互不通气。0f2186a 之后:
1. `AgentState` 加 `learning_track: str` 字段(`control_theory` / `artificial_intelligence`)
2. `POST /api/sessions/{thread_id}/learning-direction` 上线
3. `learning_track == artificial_intelligence` 时,`flow_status` 切到 `ai_path_active`,跳过主 LangGraph 节点调度
4. 前端 `ai_path.js` 接管,`session.js` 在切方向时调用 `selectLearningDirection('artificial_intelligence')`

### 6.3 AI 知识图谱数据(5/25 已落地)

```
data/knowledge_map_outputs/artificial_intelligence/
├── ai_nodes.csv                     # 228 节点,28 列(含图谱全字段)
├── ai_nodes.before_normalize.csv    # 标准化前快照
└── ai_edges.csv                     # 1494 边,字段:source/target/relation
```

边类型:`prerequisite_of` / `related_to` / `parallel_to` / `weak_related_to`,用于 service.py 的拓扑排序和路径生成。

### 6.4 与自动控制原理的核心差异(汇报要点)

| 维度 | 自动控制原理 | 人工智能 |
|---|---|---|
| 走主 LangGraph | ✅ | ❌(独立子服务) |
| 客观小测 | ✅ 10 道 + 评分 + 必会目标 | ❌ |
| 错题补救 | ✅ variant_question(2 轮上限) | ❌ |
| 多步学习路径 | ✅ learning_plan 步进 | ❌(单 path 列表) |
| 教学契约 | ✅ node_teaching_contract | ❌(直接拼 explanation) |
| 错题本 | ✅ 写 wrong_question_book | ❌ |
| 临时提问侧弹窗 | ✅(主流程) | ❌ |
| 学习方向切换 | ✅ | ✅ |
| 教学掌握度评估 | ✅ 客观题评分 | ❌(直接写 0.85) |
| 适合场景 | 已有题库 + 完整图谱 | 实验性 LLM 驱动探索 |

> **汇报要点**:AI 知识图谱分支是"轻量版教学循环",负责快速验证 LLM 驱动的多轮澄清 + 路径生成,适合没有题库、没有教学契约约束的探索性课题;自动控制原理是"完整版教学循环",适合有标准教材和题库的核心课。

---

## 7. 状态字段对比(AgentState)

`ai_tutor_agent/core/state.py` 5/25 已有 94 字段,HEAD 共 106 字段,新增 12 个:

| 字段 | 含义 | 用途 |
|---|---|---|
| `learning_plan: list` | 多步学习计划 `[{step_index, step_name, node_ids, status}]` | next_node_planner 用 |
| `learning_plan_current_step: int` | 当前在第几步 | 同上 |
| `learning_plan_generated_at: str` | 路径生成时间 ISO | 持久化 |
| `learning_plan_source: str` | `profile_based` / `resume_reuse` / `manual` | 路径来源 |
| `learning_track: str` | `control_theory` / `artificial_intelligence` | 主流程 / AI 子服务分流 |
| `learning_track_label: str` | 中文标签"自动控制原理"等 | UI 显示 |
| `learning_track_locked: bool` | 方向是否已锁定 | 防止误改 |
| `node_quiz_coverage_plan: list` | 当前节点出题蓝图 | objective_test_generator 用 |
| `node_remediation_state: dict` | `{original_score, variant_rounds, same_objective_failures, extra_count, status}` | remediation_decision 用 |
| `node_teaching_contract: dict` | 教学契约 | node_content_loader 产出,tutor/objective_test 消费 |
| `remediation_decision: str` | `continue_variant` / `review_node` / `do_later` / `still_do_variant` | 路由用 |
| `thinking_mode: bool` | 教学推理透明模式 | tutor emit thinking.step event |

> 5/25 已有字段保留:`learning_phase` / `flow_status` / `pending_interaction_*` / `graph_anchor_*` / `user_knowledge_graph` / `assessment_concept_gaps` / `node_quiz_*` / `homework_*` 等。

---

## 8. 前端对比(`frontend/assets/js/`)

| 文件 | 5/25 | HEAD | 改动 |
|---|---|---|---|
| `session.js` | 有 | 大改 | 5/25 后重构,加 `selectLearningDirection` / `patchLearningDirection` / 学习方向选择卡 / 主题确认流 |
| `ui.js` | 有 | 大改 | 5/25 后行级调整,加 chat 内学习路径卡 / 错题本入口 |
| `state.js` | 有 | 微调 | 加 `learningTrack` / `aiPathMode` 等字段 |
| `app.js` | 有 | 大改 | 加独立学习路径面板 wiring,右侧滑入滑出 |
| `ai_path.js` | 有 | 微调 | 5/25 时是主体,5/25 后只调 49 行(适配主流程方向) |
| `history.js` | 有 | 微调 | 加 ai_path_active 状态 label |
| `knowledge.js` | 有 | 微调 | 知识图谱 viewer |
| `config.js` | 有 | 未改 | |
| `error_correction.js` | 有 | 未改 | |
| `matlab_experiment.js` | 有 | 未改 | |
| **`question-help.js`** | ❌ | ✅ **新增** | 临时问题侧弹窗,quick/deep/vision 模式 |
| **`wrong-book.js`** | ❌ | ✅ **新增** | 错题本 UI,176 行 |

### 8.1 错题本(`wrong-book.js`,176 行,新增)

- 默认显示"待复习/未掌握"条目
- 按节点分组
- `/api/students/{student_id}/wrong-questions/{question_id}/master` 调用"标记已掌握/取消掌握"
- 不做"fake local-only mastery state"——必须等 API 返回成功

### 8.2 临时问题侧弹窗(`question-help.js`,126 行,新增)

- 侧弹 modal 形式
- 三种模式:`quick` / `deep` / `vision`
- 记录走 `StudentState.question_help_records`,与错题本分开
- 默认**不自动加进错题本**

### 8.3 学习方向选择卡(在 `session.js` 5/25 后加)

```
/api/sessions/{thread_id}/learning-direction
POST { track: "control_theory", label: "自动控制原理" }
POST { track: "artificial_intelligence", label: "人工智能" }
```

`/api/learning-direction/sources` 返回可选项(自动控制原理 / 人工智能 + 关联图谱路径)。

---

## 9. 题库(自动控制原理)

**5/25 时 0 道**。HEAD 新增 4 个 JSONL 文件,共 30 道:

```
data/question_bank/a2-control-theory/
├── assessment_questions.jsonl     # 10 道 学前测评题
├── objective_questions.jsonl      # 12 道 节点客观小测题
├── variant_questions.jsonl        # 5 道  错题变式题
└── homework_questions.jsonl       # 3 道  课后作业题
```

题库 provider 接入:`runtime.question_bank_provider.get_objective_questions(node_id, k)`。出题顺序:题库 → LLM → 模板兜底。

---

## 10. 测试覆盖

**5/25 时 1 个测试**:`test_ai_learning_path_progress.py`(就是 AI 路径分支那个)。
**HEAD 共 30+ 测试文件**,按主题:

### 10.1 主流程图节点教学
- `test_workflow.py` — 16+ 行新增
- `test_objective_learning_flow.py` — +319 行
- `test_temporary_question_flow.py` — +72 行
- `test_session_resume_router.py` — +13 行
- `test_node_selection_and_content_loader.py` — +17 行
- `test_next_node_and_continue_flow.py` — +19 行
- `test_remediation_decision.py` — **+340 行,全新文件**
- `test_objective_remediation_regressions.py` — +70 行

### 10.2 错题本 / 临时问题
- `test_wrong_questions_api.py` — +84 行
- `test_question_help_api.py` — +232 行
- `test_frontend_wrong_book_ui.py` — +108 行
- `test_frontend_question_help_ui.py` — +126 行

### 10.3 前端契约
- `test_frontend_learning_direction_ui.py` — **+41 行,全新**(5/28 ada1f66)
- `test_frontend_objective_test_ui.py` — +69 行
- `test_frontend_learning_content_layout.py` — +64 行
- `test_frontend_html_safety.py` — +6 行
- `test_frontend_chat_layout.py` — 已有
- `test_homework_learning_ui_contract.py` — +2 行
- `test_graph_rag_learning_answer_html.py` — +375 行

### 10.4 数据 / 集成
- `test_graph_integrity.py` — +11 行
- `test_graph_b_data_order.py` — +57 行
- `test_knowledge_graph.py` — +285 行
- `test_session_persistence.py` — +54 行
- `test_history.py` — +107 行
- `test_assessment.py` — +68 行
- `test_interruption_graph_rag_llm.py` — +87 行

### 10.5 删除的测试(43 个文件被删,大多是老闲聊循环的)
- `test_homework_generator.py` 删 -124 行
- `test_graph_rag_pipeline.py` 删 -74 行
- `test_media_asset_annotator.py` 删 -29 行
- `test_post_eval.py` 删 -22 行
- `test_debug_graph_rag_rendering_regressions.py` 删 -61 行
- `test_matlab_post_generation_pipeline.py` 改 6 行
- ...

---

## 11. 文档

### 11.1 5/25 当时
- 几乎无(只有 README 和零散 md)

### 11.2 HEAD 已有/新增
- `README.md` — 37 行新增
- `AGENTS.md` — 12 行新增(明确"active product loop is graph-node mastery learning")
- `docs/INDEX.md` — 13 行新增
- `docs/current-status-and-usage.md` — +199 行
- `docs/next-iteration-plan.md` — +57 行
- `docs/ai-tutor-summary.md` — +32 行
- `docs/plans/2026-05-28-learning-plan-design.md` — **全新**学习路径与节点学习分离设计
- `docs/plans/2026-05-29-learning-path-algorithm-v2.md` — **全新**算法设计 v2
- `docs/plans/2026-05-29-learning-path-v2-implementation-plan.md` — **全新**实施计划
- `docs/plans/2026-05-29-teaching-optimization-plan.md` — **全新**教学能力优化计划

> 后 4 份 plan 文档是 working tree 未提交的新增,不是已 commit 的内容,但属于"正在做的下一步"。

---

## 12. Runtime 工具

**5/25 时无**。HEAD 新增:

### 12.1 `scripts/check_runtime_assets.sh`(171 行)
- 校验 Graph B / AI 知识图谱 / Chroma / BM25 / 媒体证据索引 等运行时资产是否齐全
- 跑命令:`bash scripts/check_runtime_assets.sh`

### 12.2 `scripts/smoke_strict_learning_flow.py`(740 行)
- 端到端冒烟测试,跑完整节点教学闭环
- 验证:测评 → 选节点 → 教学 → 小测 → 错题 → 补救 → 推进 → 作业

### 12.3 `tests/asgi_test_client.py`
- 替代 Starlette `TestClient`(在 Python 3.9 环境会卡 BlockingPortal)
- 用 httpx.ASGITransport 直接执行 ASGI 路径
- 同步调用,所有 pytest 都基于它

---

## 13. Working tree 未提交开发(下一步)

> 42 处未提交修改,分 staged 29 + untracked 13。**不属于已交付**,但属于"正在做的下一步工作"。

### 13.1 Staged 改动(+1690 / -675)

```
state.py                  +13  (新增 6 字段:learning_plan × 4, node_teaching_contract, node_quiz_coverage_plan)
workflow.py               +36  (新增 route_after_learning_plan_generator)
tutor.py                 +180  (_ERROR_TYPE_STRATEGY, _infer_error_type, _select_strategy, 教学契约兜底)
node_content_loader.py    +63  (生成 node_teaching_contract)
objective_test.py        +147  (出题蓝图 _build_question_blueprints, 质量门控)
next_node_planner.py     +147  (learning_plan step 内/间推进)
session_resume_router.py  +66  (active homework 识别增强)
initial_node_selector.py  +18  (适配 learning_plan 入口)
homework_bank.py        -379  (整个文件删除,改走题库 + LLM)
```

### 13.2 Untracked 新增

```
ai_tutor_agent/core/learning_plan_builder.py        20K  # 多步路径生成器
ai_tutor_agent/nodes/learning_plan_generator.py     10K  # LangGraph 节点
tests/test_learning_plan.py                         18K  # 完整测试
data/question_bank/a2-control-theory/homework_questions.jsonl    3 道
data/question_bank/a2-control-theory/objective_questions.jsonl  12 道
data/question_bank/a2-control-theory/variant_questions.jsonl    5 道
docs/plans/2026-05-28-learning-plan-design.md
docs/plans/2026-05-29-learning-path-algorithm-v2.md
docs/plans/2026-05-29-learning-path-v2-implementation-plan.md
docs/plans/2026-05-29-teaching-optimization-plan.md
```

**主题**:"学习路径 v2 + 教学能力优化",属于"图节点主线下一阶段"。

---

## 14. 13 个新 commit 列表(5/25 之后到 HEAD)

| # | commit | 日期 | 一句话 |
|---|---|---|---|
| 1 | `0f2186a` | 5/26 | 主流程融合打通:接入知识图谱与临时会话,融合 25 号功能 |
| 2 | `7521feb` | 5/28 | learning direction API + session state |
| 3 | `66d7f2d` | 5/28 | runtime assets check + API E2E smoke |
| 4 | `9cbe374` | 5/28 | learning direction UI + 课程选择卡 |
| 5 | `d58a7c1` | 5/28 | 文档:update status, iteration plan, add document index |
| 6 | `ada1f66` | 5/28 | test: learning direction UI contract |
| 7 | `ae668bb` | 5/28 | fix: un-ignore AI 路径数据 |
| 8 | `82c277f` | 5/28 | fix: merge 冲突 + 集成 learning path builder |
| 9 | `f24f3f4` | 5/28 | fix: userKnowledgeGraph key 改用 node_id |
| 10 | `e1a0e75` | 5/28 | chat 内学习路径卡片 |
| 11 | `737c751` | 5/28 | 集成固定学习路径显示 |
| 12 | `e3ca182` | 5/28 | chat 右侧独立学习路径面板 |
| 13 | `6e3a317` | 5/30 | cherry-pick: 图谱内容讲解补全 + 修 next_nodes |

---

## 15. 汇报要点(给同事 / 老板 1 分钟版)

> **5/25 时**:自动控制原理 LangGraph 主流程 27 个节点框架已搭好(workflow.py 744 行),Graph B 数据齐全(42 节点 / 95 边),但**关键算法没落地**:出题靠 LLM 单一通道,无教学契约,无错因推断,无变式题上限,无多步学习路径。AI 知识图谱走独立子服务(228 节点 / 1494 边),与主流程不通气。
>
> **现在 HEAD**:
> - 自动控制原理新增 1 个节点 `remediation_decision`(+340 行),5 个节点大改(尤其 `objective_test.py` +839 行),加 12 个 AgentState 字段、1 套题库(30 道)、教学契约机制、错因推断 + 教学策略选择、出题蓝图 + 质量门控、变式题 2 轮上限、同目标失败 2 次上限
> - 人工智能保留独立子服务,通过 `learning_track` 字段统一入口(`POST /api/sessions/{thread_id}/learning-direction`),共享学生状态、错题本、临时问题
> - 新增学习方向 API + UI、错题本 UI、临时问题侧弹窗、runtime assets 检查、端到端冒烟测试、4 份设计文档
> - 共 30+ 测试文件覆盖主流程、错题、UI 契约、数据完整性
> - 数字层面:314 files / +29934 / -41451 行
>
> **下一步**(working tree 未提交):学习路径 v2 + 教学能力优化,主体内容已完成,等 commit。

---

## 附录:文件级变更统计(`git diff --stat e56fb96..HEAD` 节选)

```
ai_tutor_agent/orchestration/workflow.py                                    +30
ai_tutor_agent/nodes/remediation_decision.py                                +340  (新文件)
ai_tutor_agent/nodes/objective_test.py                                      +839
ai_tutor_agent/nodes/next_node_planner.py                                   +115
ai_tutor_agent/nodes/tutor.py                                               +185
ai_tutor_agent/nodes/node_content_loader.py                                +61
ai_tutor_agent/nodes/session_resume_router.py                               +66
ai_tutor_agent/nodes/initial_node_selector.py                               +18
ai_tutor_agent/interfaces/api/session.py                                    +180
ai_tutor_agent/core/state.py                                                +12
ai_tutor_agent/core/learning_flow.py                                        +3
ai_tutor_agent/knowledge_map/student_state.py                               +10
ai_tutor_agent/ai_learning_path/*                                           (5/25 已有,5/25 后未动)
frontend/index.html                                                         +320
frontend/assets/app.js                                                      +206
frontend/assets/js/question-help.js                                         +126  (新文件)
frontend/assets/js/wrong-book.js                                            +176  (新文件)
frontend/assets/js/session.js                                               +81
frontend/assets/js/ui.js                                                   -118 / +118(重构)
frontend/assets/styles.css                                                  +333
frontend/assets/vendor/katex/*                                             +48  (字体文件)
frontend/assets/vendor/marked/*, vis-network/*                             (新增 vendor)
data/knowledge_map_outputs/auto_control_knowledge_map_v2_*                 (5/25 已有,5/25 后微调)
data/knowledge_map_outputs/artificial_intelligence/*                       (5/25 已有,5/25 后未动)
data/question_bank/a2-control-theory/*                                      (5/25 0 → 现在 30 道)
scripts/check_runtime_assets.sh                                            +171  (新文件)
scripts/smoke_strict_learning_flow.py                                       +740  (新文件)
tests/test_*.py                                                             +29 个新测试 / -43 个老测试
docs/INDEX.md / current-status-and-usage.md / next-iteration-plan.md /
docs/ai-tutor-summary.md / AGENTS.md / README.md                            +199(综合)
docs/plans/2026-05-28-learning-plan-design.md 等 4 份                      (working tree,未提交)
```
