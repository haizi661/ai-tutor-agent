# 学习路径规划算法设计（v2）

更新时间：2026-05-29
状态：设计中，待审核

## 1. 问题定义

### 1.1 当前 `build_learning_plan` 的问题

当前算法是：拓扑排序 → 按层级/章节分块 → 输出。

本质上是"课程大纲的分步版本"，不是"个性化路径"：
- 没有用 `calibrated` 分数做优先级决策
- 没有考虑"哪些节点对当前目标最重要"
- 生成后是静态的，不会随学习进展调整

### 1.2 伴学路径要回答的三个问题

| 问题 | 含义 | 当前是否解决 |
|------|------|-------------|
| 学什么？ | 选哪些节点进入路径 | 部分（跳过 mastered） |
| 什么顺序？ | 节点间的先后关系 | 部分（只用拓扑排序） |
| 怎么分组？ | 几个节点算一步 | 是（按层级/章节） |

### 1.3 目标

生成一个**个性化、可预测、可调整**的学习路径：
- 个性化：根据诊断分数和掌握状态，不同学生看到不同路径
- 可预测：学生能看到"我接下来要学什么"，路径不会突然大变
- 可调整：学完一步后，后续步骤可以根据实际掌握情况微调

## 2. 输入与输出

### 2.1 输入

```python
{
    # 知识图谱
    "node_map": {node_id: {name, chapter, prerequisite_nodes, ...}},
    "edges": [{"source", "target", "relation"}],

    # 用户画像（来自 assessment）
    "concept_gaps": {concept_title: {calibrated, concept_id, ...}},
    "difficulty_level": 1-5,

    # 已掌握状态（来自 StudentState）
    "knowledge_graph": {node_id: {status, score, ...}},

    # 学习目标（可选）
    "current_topic": "根轨迹法",
    "target_node_id": "KM020",  # 从 current_topic 推导
}
```

### 2.2 输出

```python
[
    {
        "step_index": 0,
        "step_name": "基础概念",
        "node_ids": ["KM001"],
        "node_names": ["控制系统的一般概念"],
        "status": "in_progress",  # pending | in_progress | completed
        "reason": "课程起点，无前置依赖",
        "priority_score": 95,  # 越高越优先
    },
    {
        "step_index": 1,
        "step_name": "数学模型基础",
        "node_ids": ["KM007", "KM008"],
        "node_names": ["数学模型总论", "时域模型"],
        "status": "pending",
        "reason": "诊断中数学建模得分最低(35/100)，需优先补齐",
        "priority_score": 80,
    },
    ...
]
```

### 2.3 与当前系统的接口

- `learning_plan_generator` 节点调用 `build_learning_plan()` 生成路径
- `next_node_planner` 从当前 step 中选下一个节点
- `session_resume_router` 从持久化的路径恢复
- 前端面板渲染 step 列表

**这些接口不变**，只改 `build_learning_plan()` 内部的排序逻辑。

## 3. 算法设计

### 3.1 核心思路：ZPD 驱动 + 拓扑约束

不是纯拓扑排序，也不是纯自适应，而是：

```
拓扑约束（硬）：必须前置已掌握才能学
ZPD 优先级（软）：在满足拓扑约束的候选节点中，按优先级排序
```

### 3.2 Phase 1：过滤

```python
# 去掉已 mastered 的节点
active_nodes = [n for n in all_nodes if not is_mastered(n)]

# 去掉 chapter_anchor（结构性节点，不是学习内容）
active_nodes = [n for n in active_nodes if not is_chapter_anchor(n)]
```

### 3.3 Phase 2：计算候选池

"候选" = 所有前置已满足的节点（可以立即开始学的）

```python
def get_candidates(active_nodes, edges, mastered):
    """返回所有前置已满足的节点"""
    candidates = []
    for node in active_nodes:
        prereqs = get_prerequisites(node, edges)
        if all(p in mastered for p in prereqs):
            candidates.append(node)
    return candidates
```

这是 Kahn's algorithm 的思路：入度为 0 的节点就是候选。

### 3.4 Phase 3：优先级排序

对候选池中的每个节点计算优先级分数，分数越高越优先：

```python
def compute_priority(node, concept_gaps, target_node_id, edges, difficulty_level):
    score = 50.0  # 基础分

    # 1. calibrated 分数影响（来自诊断）
    #    calibrated 越低 → 优先级越高
    calibrated = get_calibrated(node, concept_gaps)
    if calibrated is not None:
        score += (100 - calibrated) * 0.3  # 最多 +30

    # 2. 与目标节点的相关性
    #    是目标节点的前置 → 优先级高
    if target_node_id:
        relevance = compute_relevance(node, target_node_id, edges)
        score += relevance * 0.4  # 最多 +40

    # 3. 拓扑层的影响
    #    层级越低（越基础）→ 优先级越高
    layer = get_topo_layer(node)
    score += max(0, 10 - layer) * 1  # 最多 +10

    # 4. difficulty_level 的影响
    #    难度偏好低的学生，更基础的节点优先
    if difficulty_level <= 2:
        score += max(0, 5 - layer) * 2  # 基础节点额外加分

    return score
```

### 3.5 Phase 4：相关性计算

```python
def compute_relevance(node_id, target_node_id, edges):
    """计算 node 与 target 的相关性。

    返回 0-100 的分数：
    - 是 target 本身的前置（在前置链上）→ 100
    - 与 target 同 chapter → 50
    - 与 target 有 related_to 边 → 30
    - 无关 → 0
    """
    # BFS 从 target 反向找前置链
    prereq_chain = find_prerequisite_chain(target_node_id, edges)

    if node_id in prereq_chain:
        return 100  # 在目标的前置链上

    # 同 chapter
    if same_chapter(node_id, target_node_id):
        return 50

    # 有 related_to 边
    if has_related_edge(node_id, target_node_id, edges):
        return 30

    return 0
```

### 3.6 Phase 5：分步聚合

```python
def aggregate_into_steps(sorted_candidates, difficulty_level, node_map):
    """将排序后的候选节点聚合成步骤。

    策略：
    - 每步包含 1-N 个节点（N 由 difficulty_level 决定）
    - 同一拓扑层的节点可以放在同一步
    - 同一 chapter 的节点优先放在一起
    - 前置依赖关系必须跨步满足（A 在 Step 0，B 依赖 A 必须在 Step 1+）
    """
    max_per_step = nodes_per_step_for_difficulty(difficulty_level)

    steps = []
    current_step = []
    assigned = set()

    for node in sorted_candidates:
        if node in assigned:
            continue

        # 检查前置是否都在已分配的步骤中
        prereqs = get_prerequisites(node)
        if not all(p in assigned for p in prereqs):
            continue  # 跳过，等前置先分配

        current_step.append(node)
        assigned.add(node)

        if len(current_step) >= max_per_step:
            steps.append(current_step)
            current_step = []

    if current_step:
        steps.append(current_step)

    return steps
```

### 3.7 Phase 6：生成后续步的"大致方向"

前几步确定后，后续步不需要精确排序，只需要给出大致方向：

```python
def generate_future_directions(remaining_nodes, edges, target_node_id):
    """生成后续步骤的大致方向。

    不做精确排序，只按拓扑层分组，让用户知道"后面大概要学什么"。
    """
    layers = group_by_topo_layer(remaining_nodes, edges)
    directions = []
    for layer_num in sorted(layers.keys()):
        nodes_in_layer = layers[layer_num]
        directions.append({
            "layer": layer_num,
            "node_ids": nodes_in_layer,
            "description": f"拓扑层 {layer_num}：{len(nodes_in_layer)} 个知识点",
        })
    return directions
```

## 4. 动态更新策略

### 4.1 什么时候重算

| 场景 | 是否重算 | 原因 |
|------|---------|------|
| 学完一个节点 | 不重算 | 当前步内的顺序固定 |
| 学完一步 | 重算后续步 | 掌握状态变了，优先级可能变 |
| 诊断分数更新 | 重算全部 | calibrated 变了 |
| 用户更换学习目标 | 重算全部 | 相关性变了 |

### 4.2 "当前步确定 + 后续步可调"

这是折中方案的核心：

```
Step 0: [KM001]                    ← 已完成，不变
Step 1: [KM007, KM008]             ← 当前进行中，不变
Step 2: [KM009, KM010]             ← 待学习，可调整
Step 3+: 按拓扑层的大致方向          ← 模糊，学到了再细化
```

当 Step 1 完成后：
1. 更新 knowledge_graph（KM007 mastered, KM008 mastered）
2. 重新计算候选池（KM009 的前置 KM008 已满足）
3. 重新排序候选池（可能 KM012 的 calibrated 更低，应该优先）
4. 生成新的 Step 2 和后续方向

### 4.3 前端展示

```
📋 学习路径：自动控制原理
━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Step 1: 基础概念 (1/1)          ← 已完成，折叠
🔄 Step 2: 数学模型 (1/2)          ← 当前，展开
   ✅ KM007 数学模型总论
   🔵 KM008 时域模型               ← 正在学
⬜ Step 3: 复数域模型 (0/2)         ← 待学习，折叠
   ⬜ KM009 复数域模型
   ⬜ KM010 结构图与信号流图
⬜ 后续：时域分析 → 根轨迹法 → ...  ← 大致方向，不展开
```

## 5. 与现有系统的关系

### 5.1 与 `next_node_planner` 的关系

**增强，不替代**。

- `next_node_planner` 仍然负责"从当前 step 选下一个节点"
- 路径规划提供 step 结构，`next_node_planner` 在 step 内选
- 如果 step 内没有未学节点，`next_node_planner` 推进到下一个 step

### 5.2 与 `initial_node_selector` 的关系

**替代**。

- `initial_node_selector` 现在从 `learning_plan[0]` 选节点
- 路径规划的第一步就是初始节点，不需要单独的初始选择逻辑

### 5.3 与 `session_resume_router` 的关系

**增强**。

- 恢复时从持久化的路径中找当前 step
- 如果路径是"动态更新"的，恢复后可能需要重算后续步

## 6. 实现计划

### Phase 1：重写 `build_learning_plan()` 核心逻辑

- [ ] 过滤：去掉 mastered 和 chapter_anchor
- [ ] 候选池：前置已满足的节点
- [ ] 优先级排序：calibrated + 相关性 + 拓扑层
- [ ] 分步聚合：按 difficulty_level 分组
- [ ] 生成后续方向

### Phase 2：添加"动态更新"接口

- [ ] `update_learning_plan()` 函数：学完一步后重算后续步
- [ ] 在 `next_node_planner` 中调用更新逻辑

### Phase 3：添加相关性计算

- [ ] `compute_relevance()` 函数：BFS 前置链 + 同 chapter + related_to
- [ ] 处理无目标节点的情况（全量学习）

### Phase 4：测试

- [ ] 单元测试：优先级排序、相关性计算、分步聚合
- [ ] 集成测试：路径生成 → 节点选择 → 步骤推进 → 动态更新

### Phase 5：前端适配

- [ ] 渲染"后续方向"（模糊区域）
- [ ] 处理"路径变化"的情况（后续步调整时的 UI 反馈）

## 7. 待确认的问题

### Q1：动态更新的粒度

选项：
- A. 每学完一个节点就重算（最灵活，但路径不稳定）
- B. 每学完一步重算（折中，当前设计）
- C. 只在诊断分数更新时重算（最稳定，但可能错过优化）

**建议**：B，每学完一步重算。

### Q2：前端展示"后续方向"

选项：
- A. 显示完整的后续路径（即使可能变化）
- B. 只显示下一步，后续用"..."表示
- C. 显示大致方向（"接下来是时域分析 → 根轨迹法"）

**建议**：C，显示大致方向。

### Q3：与 `next_node_planner` 的分工

选项：
- A. 路径规划完全替代 `next_node_planner` 的选择逻辑
- B. 路径规划提供 step 结构，`next_node_planner` 在 step 内选
- C. 两套逻辑并存，`next_node_planner` 可以不按路径走

**建议**：B，保持现有接口不变。

### Q4：无目标节点时怎么处理

当用户说"学习自动控制原理"（没有具体目标），路径应该怎么生成？

选项：
- A. 按拓扑序全量铺开
- B. 按 calibrated 分排序，薄弱的优先
- C. 先问用户"你想重点学哪个部分？"

**建议**：B，薄弱优先。如果用户后续指定了目标，再动态调整。
