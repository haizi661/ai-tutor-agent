# 学习路径 V2 实施计划

更新时间：2026-05-29
状态：进行中

## 1. 目标

将学习路径从"课程大纲的分步版本"升级为"个性化、可预测、可调整"的路径。

核心改进点：
- **目标聚焦**：学生说"学根轨迹法"时，路径优先安排通往根轨迹的前置知识
- **动态更新**：学完一步后，后续步骤根据实际掌握状态重算
- **优先级增强**：综合考虑诊断薄弱分、目标相关性、拓扑层级

## 2. 当前进度

### 已完成（learning_plan_builder.py）

| 功能 | 函数 | 状态 |
|------|------|------|
| 目标相关性计算 | `compute_relevance()` | ✅ 已实现 |
| 优先级评分增强 | `_score_node()` | ✅ 已扩展（新增 target_node_id, prereq_chain, topo_layer 参数） |
| 目标聚焦路径生成 | `build_priority_plan()` | ✅ 已扩展（新增 target_node_id 参数） |
| 动态路径更新 | `update_learning_plan()` | ✅ 已实现 |

### 未完成

| 任务 | 涉及文件 | 依赖 |
|------|----------|------|
| 接入 target_node_id 到路径生成节点 | `nodes/learning_plan_generator.py` | 需要从 current_topic 推导 target_node_id |
| 接入动态更新到节点推进器 | `nodes/next_node_planner.py` | 学完一步后调用 update_learning_plan |
| AgentState 新增 target_node_id 字段 | `core/state.py` | 可选，也可从 topic 推导 |
| 单元测试 | `tests/test_learning_plan.py` | 以上代码完成后 |
| 全量回归 | 全项目 | 以上全部完成 |

## 3. 详细任务分解

### Task 1：从 current_topic 推导 target_node_id

**问题**：学生输入的是自然语言主题（如"根轨迹法"），需要匹配到图谱节点 ID。

**方案**：在 `learning_plan_generator` 节点中，用节点名称匹配 current_topic：
1. 遍历 node_map，找 name 包含 current_topic 的节点
2. 如果有多个匹配，选 calibrated 分最低的（最薄弱的）作为 target
3. 如果没有匹配，target_node_id 为空，走全量学习路径

**涉及文件**：`nodes/learning_plan_generator.py`

**改动点**：
```python
# 在 build_priority_plan 调用前，推导 target_node_id
target_node_id = _resolve_target_node(current_topic, node_map, concept_gaps)
plan = build_priority_plan(
    ...,
    target_node_id=target_node_id,
)
```

### Task 2：接入动态更新到 next_node_planner

**问题**：当前 `next_node_planner` 在 Step 完成后只是推进到下一步，不会重算后续路径。

**方案**：在 Step 完成时调用 `update_learning_plan()`：
1. 检测当前 Step 是否完成（所有节点已 visited）
2. 如果完成，调用 `update_learning_plan(completed_step_index, plan, ...)`
3. 用返回的新 plan 替换旧 plan
4. 持久化到 StudentState
5. 发送 `learning_plan.updated` 事件通知前端

**涉及文件**：`nodes/next_node_planner.py`

**改动点**：
```python
# 在 "2. Current step completed" 分支中
from ..core.learning_plan_builder import update_learning_plan

if is_step_completed(current_step, visited):
    updated_plan = update_learning_plan(
        completed_step_index=current_step_idx,
        plan=learning_plan,
        node_map=node_map,
        edges=edges,
        concept_gaps=concept_gaps,
        knowledge_graph=knowledge_graph,
        current_topic=current_topic,
    )
    learning_plan = updated_plan
    # 持久化 + 发事件
```

### Task 3：AgentState 新增字段（可选）

**判断**：如果 target_node_id 只在路径生成时用一次，不需要持久化到 AgentState。
但如果希望前端能显示"目标节点"，可以加。

**方案**：暂不加 AgentState 字段，target_node_id 只在 learning_plan_generator 内部推导和使用。

### Task 4：单元测试

**新增测试用例**：

| 测试 | 验证点 |
|------|--------|
| `test_compute_relevance_prereq_chain` | 节点在目标前置链上 → 返回 100 |
| `test_compute_relevance_same_chapter` | 同章节 → 返回 50 |
| `test_compute_relevance_related_edge` | 有 related_to 边 → 返回 30 |
| `test_compute_relevance_unrelated` | 无关 → 返回 0 |
| `test_build_priority_plan_with_target` | 有 target_node_id 时，前置链节点优先级更高 |
| `test_update_learning_plan_basic` | 学完一步后，后续步骤重算 |
| `test_update_learning_plan_preserves_completed` | 已完成步骤不变 |
| `test_update_learning_plan_empty_remaining` | 所有节点已学完，只返回已完成步骤 |
| `test_score_node_with_target` | 带 target 时评分高于不带 target |

**涉及文件**：`tests/test_learning_plan.py`

### Task 5：全量回归

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

预期：626+ passed（现有测试不破 + 新测试通过）

## 4. 不做的事

- 不改前端面板（当前面板已够用，动态更新通过 SSE 事件通知即可）
- 不改 AgentState 结构（暂不加 target_node_id 字段）
- 不改 session_resume_router（恢复时复用已有 plan，不触发重算）
- 不改 workflow.py 的路由结构

## 5. 验收标准

1. `compute_relevance("KM001", "KM020", edges, node_map)` 返回正确分数
2. `build_priority_plan(target_node_id="KM020", ...)` 生成的路径中，KM020 前置链上的节点排在前面
3. `update_learning_plan(completed_step_index=0, ...)` 返回更新后的 plan，已完成步骤保留，后续步骤重算
4. 全量测试通过
5. learning_plan_generator 节点能正确从 current_topic 推导 target_node_id

## 6. 预计工作量

| 任务 | 预计时间 |
|------|----------|
| Task 1: 接入 target_node_id | 30 分钟 |
| Task 2: 接入动态更新 | 45 分钟 |
| Task 4: 单元测试 | 1 小时 |
| Task 5: 全量回归 | 10 分钟 |
| **总计** | **约 2.5 小时** |

## 7. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| target 推导匹配不准 | 路径不够聚焦 | fallback 到全量学习（当前行为） |
| 动态更新后 plan 大变 | 用户困惑 | 只在 Step 边界重算，当前 Step 内不变 |
| update_learning_plan 性能 | 节点推进变慢 | 预计算 topo_layers，单次调用 < 100ms |
| 现有测试被破坏 | 回归失败 | 新函数是新增，不改现有函数签名 |
