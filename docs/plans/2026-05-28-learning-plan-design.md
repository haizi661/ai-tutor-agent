# 学习路径（Learning Plan）与节点学习分离设计

更新时间：2026-05-28

## 1. 问题诊断

### 1.1 当前架构缺陷

当前系统中"选下一个节点"和"学习路径"是混在一起的：

```
initial_node_selector  →  全局搜索，只选 1 个起点节点
next_node_planner      →  当前节点的 recommended_next_nodes，只选 1 个
LearningPathBuilder    →  给每个节点标注 recommended_next_nodes（局部跳转，不是全局规划）
ai_path_service        →  有 current_path / path_versions，但只服务于 AI 学习路径子系统，
                          未接入自动控制原理主流程
```

**核心问题**：没有一个"根据用户画像生成的、多步的、每步可含多个节点的学习计划"。

- `next_node_planner` 每次只看当前节点的 `recommended_next_nodes`，是一个贪心的局部跳转
- 没有全局视野：不知道"今天应该学完哪些节点"，不知道"当前处于学习计划的第几步"
- 用户画像（`assessment_radar`, `concept_gaps`, `difficulty_level`）只影响了初始节点选择，没有影响后续路径

### 1.2 正确的架构

```
用户画像 (assessment_radar, concept_gaps, difficulty_level, teaching_strategy)
    ↓
学习路径生成器 (learning_plan_generator)
    ↓
learning_plan = [
  Step 0: { name: "基础概念", node_ids: ["KM001", "KM002"], reason: "..." }
  Step 1: { name: "数学建模", node_ids: ["KM007", "KM008", "KM009"], reason: "..." }
  Step 2: { name: "时域分析", node_ids: ["KM012", "KM013", "KM014", "KM015"], reason: "..." }
  ...
]
    ↓
当前节点 current_node_id ← 属于某个 Step 里的某个节点
    ↓
学完当前节点 → 在当前 Step 内找下一个 → Step 完了 → 进入下一个 Step
```

**核心区分**：
- **学习路径 (learning_plan)**：宏观规划，生成一次、逐步推进，是多步的，每步可含多个节点
- **节点学习 (current_node_id)**：微观执行，是路径里的一个具体节点
- 当前的 `next_node_planner` 应该从路径的当前 Step 里选，而不是每次重新全局搜索

## 2. 数据结构设计

### 2.1 AgentState 新增字段

```python
# state.py 新增
learning_plan: list[dict]              # 多步学习计划
learning_plan_current_step: int        # 当前在第几步
learning_plan_generated_at: str        # 路径生成时间 ISO
learning_plan_source: str              # 生成来源: "profile_based" | "resume_reuse" | "manual"
```

### 2.2 learning_plan 每步结构

```python
{
    "step_index": 0,                          # 步骤序号
    "step_name": "控制系统基础概念",           # 步骤名称（可由 LLM 生成或规则生成）
    "node_ids": ["KM001", "KM002"],           # 该步骤包含的节点 ID 列表
    "node_names": ["一般概念", "基本原理"],    # 对应节点名称（展示用）
    "status": "pending",                      # pending | in_progress | completed
    "reason": "这些是无前置依赖的入门节点",    # 为什么放在这一行
    "estimated_difficulty": 2,                # 该步骤预估难度 1-5
    "prerequisite_steps": []                  # 依赖的前置步骤索引
}
```

### 2.3 StudentState 持久化

在 `StudentStateStore` 的 JSON 中新增：

```python
{
    "learning_plan": [...],                   # 同 AgentState 结构
    "learning_plan_current_step": 0,
    "learning_plan_generated_at": "2026-05-28T...",
    "learning_plan_source": "profile_based"
}
```

这样会话恢复时可以复用已有的学习路径，不需要重新生成。

## 3. 学习路径生成算法

### 3.1 输入

| 输入 | 来源 | 用途 |
|------|------|------|
| 知识图谱节点 | `graph_pipeline.node_map` | 所有可用节点 |
| 知识图谱边 | `graph_pipeline.edges` | prerequisite_of 关系 |
| 用户画像 | `assessment_radar` | 6 维能力雷达图 |
| 概念差距 | `assessment_concept_gaps` | 薄弱概念及其校准分 |
| 学生状态 | `student_state_snapshot` | 已学节点、错题节点、掌握分 |
| 难度等级 | `difficulty_level` | 1-5，影响路径深度 |

### 3.2 算法步骤

```
Phase 1: 拓扑排序
  - 从 prerequisite_of 边构建 DAG
  - 计算每个节点的拓扑层级（layer）
  - 同一层级的节点可以并行学习

Phase 2: 画像加权
  - 已掌握节点（score >= 60 in knowledge_graph）标记为 completed
  - 概念差距中 calibrated 分低的节点提升优先级
  - difficulty_level 影响每步包含的节点数：
    - level 1-2: 每步 1-2 个节点（慢节奏）
    - level 3:   每步 2-3 个节点（标准）
    - level 4-5: 每步 3-5 个节点（快节奏）

Phase 3: 分步聚合
  - 将同一拓扑层级的节点聚合为一个 Step
  - 如果某层节点太多，按 chapter 分组拆分为多个 Step
  - 如果某层节点已全部掌握，跳过该 Step
  - 为每个 Step 生成 step_name 和 reason

Phase 4: 路径剪枝
  - 如果用户目标明确（如"学习根轨迹法"），从目标节点反向 BFS
    找出所有前置节点作为路径，不包含无关分支
  - 如果用户目标模糊（如"学习自动控制原理"），保留完整路径
```

### 3.3 示例输出

用户在诊断中"数学建模"得分最低（calibrated 35），"基础概念"得分中等（calibrated 60）：

```json
{
  "learning_plan": [
    {
      "step_index": 0,
      "step_name": "控制系统基础概念",
      "node_ids": ["KM001"],
      "node_names": ["控制系统的一般概念"],
      "status": "in_progress",
      "reason": "课程起点，无前置依赖",
      "estimated_difficulty": 1,
      "prerequisite_steps": []
    },
    {
      "step_index": 1,
      "step_name": "控制系统的数学模型",
      "node_ids": ["KM007", "KM008", "KM009", "KM010", "KM011"],
      "node_names": ["数学模型总论", "时域模型", "复数域模型", "结构图与信号流图", "建模实例"],
      "status": "pending",
      "reason": "诊断中数学建模维度得分最低(35/100)，需优先补齐",
      "estimated_difficulty": 3,
      "prerequisite_steps": [0]
    },
    {
      "step_index": 2,
      "step_name": "时域分析基础",
      "node_ids": ["KM012", "KM013", "KM014", "KM015"],
      "node_names": ["时域分析法", "性能指标", "一阶系统分析", "二阶系统分析"],
      "status": "pending",
      "reason": "依赖数学模型，是后续稳定性/根轨迹/频域的基础",
      "estimated_difficulty": 3,
      "prerequisite_steps": [1]
    },
    {
      "step_index": 3,
      "step_name": "时域分析进阶",
      "node_ids": ["KM016", "KM017", "KM018", "KM019"],
      "node_names": ["高阶系统分析", "稳定性分析", "稳态误差", "时域设计"],
      "status": "pending",
      "reason": "时域分析的高阶内容",
      "estimated_difficulty": 4,
      "prerequisite_steps": [2]
    },
    {
      "step_index": 4,
      "step_name": "根轨迹法",
      "node_ids": ["KM020", "KM021", "KM022", "KM023", "KM024", "KM025"],
      "node_names": ["根轨迹法", "基本概念", "绘制法则", "广义根轨迹", "性能分析", "复域设计"],
      "status": "pending",
      "reason": "依赖时域分析和复数域模型",
      "estimated_difficulty": 4,
      "prerequisite_steps": [2]
    }
  ],
  "learning_plan_current_step": 0,
  "learning_plan_generated_at": "2026-05-28T10:30:00",
  "learning_plan_source": "profile_based"
}
```

## 4. 节点改造

### 4.1 新增节点：`learning_plan_generator`

**位置**：在 `user_profiler` 之后、`initial_node_selector` 之前

```
user_profiler → learning_plan_generator → initial_node_selector → ...
```

**职责**：
1. 读取用户画像和知识图谱
2. 调用路径生成算法
3. 将结果写入 `learning_plan` 和 `learning_plan_current_step`
4. 发送事件通知前端

**输入 AgentState 字段**：
- `assessment_radar`
- `assessment_concept_gaps`
- `difficulty_level`
- `student_state_snapshot`
- `current_topic`

**输出 AgentState 字段**：
- `learning_plan`
- `learning_plan_current_step`
- `learning_plan_generated_at`
- `learning_plan_source`

**跳过条件**：
- 如果 `student_state_snapshot` 中已有有效的 `learning_plan` 且 `learning_plan_source == "profile_based"`，直接复用，不重新生成
- 如果用户明确指定了学习目标（如"只学根轨迹法"），从目标反向生成精简路径

### 4.2 改造节点：`initial_node_selector`

**当前行为**：全局搜索无前置依赖的最小节点
**改为**：从 `learning_plan[0]` 的 `node_ids` 中选第一个未学节点

```python
# 伪代码
plan = state.get("learning_plan", [])
if plan:
    first_step = plan[0]
    for node_id in first_step["node_ids"]:
        if node_id not in visited:
            selected_id = node_id
            break
else:
    # fallback: 保持当前行为
    selected_id, reason = _select_initial_root_node(node_map, visited)
```

### 4.3 改造节点：`next_node_planner`

**当前行为**：从当前节点的 `recommended_next_nodes` 中找第一个未学节点
**改为**：先在当前 Step 内找 → Step 完了推进到下一个 Step → 所有 Step 完成则进入作业

```python
# 伪代码
plan = state.get("learning_plan", [])
current_step_idx = state.get("learning_plan_current_step", 0)
visited = set(student_state_snapshot.get("visited_nodes", []))

# 1. 在当前 Step 内找未学节点
if current_step_idx < len(plan):
    current_step = plan[current_step_idx]
    for node_id in current_step["node_ids"]:
        if node_id not in visited and node_id != current_node_id:
            return {"next_node": node_id, "source": "same_step"}

    # 2. 当前 Step 全部学完，推进到下一个 Step
    current_step["status"] = "completed"
    next_step_idx = current_step_idx + 1
    if next_step_idx < len(plan):
        plan[next_step_idx]["status"] = "in_progress"
        for node_id in plan[next_step_idx]["node_ids"]:
            if node_id not in visited:
                return {"next_node": node_id, "source": "next_step", "step": next_step_idx}

# 3. 所有 Step 完成
return {"next_node": "", "source": "plan_completed"}
```

### 4.4 改造节点：`session_resume_router`

**当前行为**：恢复时用 `recommend_next_node` 全局搜索
**改为**：从持久化的 `learning_plan` 中恢复当前 Step 和当前节点

```python
# 伪代码
plan = snapshot.get("learning_plan", [])
current_step_idx = snapshot.get("learning_plan_current_step", 0)

if plan and current_step_idx < len(plan):
    current_step = plan[current_step_idx]
    # 找当前 Step 中第一个未学完的节点
    for node_id in current_step["node_ids"]:
        node_status = knowledge_graph.get(node_id, {}).get("status", "")
        if node_status != "mastered":
            return node_id  # 恢复到这个节点
```

### 4.5 改造节点：`continue_or_homework_selector`

**当前行为**：问用户"继续下一节点"或"结束生成作业"
**改为**：显示当前路径进度，让用户决定

```
事件消息示例：
"当前学习路径进度：Step 2/5（时域分析基础），
 已完成 3/4 个节点。
 继续学习下一个节点？还是结束本轮生成作业？"
```

## 5. Workflow 改造

### 5.1 新增条件边

```python
# workflow.py
workflow.add_node("learning_plan_generator", build_learning_plan_generator_node(runtime))

# user_profiler → learning_plan_generator → initial_node_selector
workflow.add_edge("user_profiler", "learning_plan_generator")
workflow.add_edge("learning_plan_generator", "initial_node_selector")
```

### 5.2 路由不变

`initial_node_selector` → `node_content_loader` → `tutor` 的路由不变。

`next_node_planner` → `continue_or_homework_selector` 的路由不变，只是 `next_node_planner` 内部逻辑改变。

## 6. 前端适配

### 6.1 学习路径面板

在聊天右侧或底部新增"学习路径"面板，显示：

```
📋 学习路径：自动控制原理
━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Step 1: 基础概念 (1/1)
   ✅ KM001 控制系统的一般概念

🔄 Step 2: 数学模型 (2/5)     ← 当前
   ✅ KM007 数学模型总论
   🔵 KM008 时域模型          ← 正在学
   ⬜ KM009 复数域模型
   ⬜ KM010 结构图与信号流图
   ⬜ KM011 建模实例

⬜ Step 3: 时域分析 (0/4)
⬜ Step 4: 根轨迹法 (0/6)
⬜ Step 5: 频域分析 (0/6)
```

### 6.2 事件协议

`learning_plan_generator` 发送的事件：

```json
{
  "type": "learning_plan.generated",
  "source": "learning_plan_generator",
  "data": {
    "total_steps": 5,
    "total_nodes": 22,
    "plan": [...]
  }
}
```

`next_node_planner` 发送的事件扩展：

```json
{
  "type": "learning_plan.progress",
  "source": "next_node_planner",
  "data": {
    "current_step": 2,
    "total_steps": 5,
    "step_progress": "2/5",
    "next_node_in_step": "KM009",
    "step_completed": false
  }
}
```

## 7. 会话恢复设计

### 7.1 路径持久化

学习路径写入 `StudentStateStore`，不依赖 LangGraph checkpoint：

```python
# StudentState 新增
learning_plan: list[dict] = field(default_factory=list)
learning_plan_current_step: int = 0
learning_plan_generated_at: str = ""
learning_plan_source: str = ""
```

### 7.2 恢复流程

```
session_resume_router
  ↓
读取 StudentState.learning_plan
  ↓
有效？ → 复用，不重新生成
  ↓
从 learning_plan_current_step 找到当前 Step
  ↓
从当前 Step 找到第一个未 mastered 的节点
  ↓
恢复到该节点继续学习
```

### 7.3 路径失效条件

以下情况需要重新生成路径：
- 学生更换了学习主题（`current_topic` 变化）
- 学生重新做了诊断测评
- 路径中所有节点都已完成

## 8. 与现有 ai_path_service 的关系

当前 `ai_path_service` 是独立的 AI 学习路径子系统，有自己的：
- 图谱（`ai_nodes.csv`, `ai_edges.csv`）
- 学生状态（`ai_student_state.json`）
- 路径生成逻辑

本设计不修改 `ai_path_service`，而是为自动控制原理主流程新增路径能力。

两个系统的路径是独立的：
- `ai_path_service`：AI 学习方向的路径
- `learning_plan_generator`：自动控制原理学习方向的路径

共享的基础设施：
- `StudentStateStore`（新增字段）
- `AgentState`（新增字段）
- 前端路径面板（可切换显示不同方向的路径）

## 9. 实施计划

### Phase 1: 数据结构（预计 1 小时）
- [ ] AgentState 新增 `learning_plan`、`learning_plan_current_step`、`learning_plan_generated_at`、`learning_plan_source` 字段
- [ ] StudentState 新增对应持久化字段
- [ ] `build_initial_state` 新增默认值

### Phase 2: 路径生成算法（预计 2 小时）
- [ ] 新建 `ai_tutor_agent/core/learning_plan_builder.py`
- [ ] 实现 `build_learning_plan(graph_pipeline, assessment_concept_gaps, difficulty_level, student_state_snapshot, current_topic)` 函数
- [ ] 实现拓扑排序、画像加权、分步聚合、路径剪枝
- [ ] 单元测试

### Phase 3: learning_plan_generator 节点（预计 1 小时）
- [ ] 新建 `ai_tutor_agent/nodes/learning_plan_generator.py`
- [ ] 实现 `build_learning_plan_generator_node(runtime)` 函数
- [ ] 读取画像和图谱，调用路径生成算法
- [ ] 写入 AgentState 和 StudentState
- [ ] 发送事件

### Phase 4: 改造 initial_node_selector（预计 0.5 小时）
- [ ] 优先从 `learning_plan[0]` 选节点
- [ ] fallback 保持当前行为

### Phase 5: 改造 next_node_planner（预计 1 小时）
- [ ] 从当前 Step 内选下一个节点
- [ ] Step 完成后推进到下一个 Step
- [ ] 所有 Step 完成后返回 plan_completed
- [ ] 更新 StudentState 中的 Step 状态

### Phase 6: 改造 session_resume_router（预计 0.5 小时）
- [ ] 从持久化的 learning_plan 恢复
- [ ] 找到当前 Step 中未 mastered 的节点

### Phase 7: Workflow 接线（预计 0.5 小时）
- [ ] 注册 `learning_plan_generator` 节点
- [ ] 添加 `user_profiler` → `learning_plan_generator` → `initial_node_selector` 边
- [ ] 更新路由函数

### Phase 8: 前端路径面板（预计 2 小时）
- [ ] 新增 `frontend/assets/js/learning-plan.js`
- [ ] 监听 `learning_plan.generated` 和 `learning_plan.progress` 事件
- [ ] 渲染路径面板
- [ ] 样式

### Phase 9: 测试（预计 1.5 小时）
- [ ] 单元测试：路径生成算法
- [ ] 集成测试：learning_plan_generator 节点
- [ ] 集成测试：改造后的 initial_node_selector
- [ ] 集成测试：改造后的 next_node_planner（Step 内选择、Step 推进、全部完成）
- [ ] 集成测试：会话恢复时路径复用
- [ ] 前端契约测试

**总预计：10 小时**

## 10. 验收标准

### 10.1 路径生成
- 根据用户画像生成多步学习计划
- 每步包含 1-N 个节点，节点按拓扑层级聚合
- 薄弱概念对应的节点优先级更高
- 已掌握节点自动跳过

### 10.2 节点选择
- `initial_node_selector` 从路径第一步选节点
- `next_node_planner` 先在当前 Step 内选，Step 完了推进到下一步
- 所有 Step 完成后进入作业/结束

### 10.3 会话恢复
- 路径持久化到 StudentState
- 恢复时复用已有路径，不重新生成
- 恢复到当前 Step 中未 mastered 的节点

### 10.4 前端
- 显示完整学习路径
- 高亮当前 Step 和当前节点
- 实时更新进度

### 10.5 测试
- 路径生成算法：拓扑排序正确、画像加权正确、分步聚合正确
- 节点选择：Step 内选择、Step 推进、全部完成
- 恢复：路径复用、节点恢复
- 全量测试通过
