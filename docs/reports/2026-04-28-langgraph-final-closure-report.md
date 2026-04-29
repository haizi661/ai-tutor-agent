# LangGraph 知识图谱驱动智能导师系统最终闭合补充报告

报告时间：2026-04-28
项目根目录：本报告中的路径说明统一以仓库根目录为基准，使用项目内相对路径。

## 1. 本轮补齐目标

本轮目标是把上一阶段仍未完全闭合的底座继续补齐，重点包括：

1. 27 号风格知识图谱可视化是否正确接入；
2. `viewer/data.js` 是否与当前 `a2-control-theory/graph.json` 可重复同步；
3. `media_evidence_index` 是否存在并达到最小可用状态；
4. `tutor` 是否真正优先使用图谱 2.1 当前节点材料，而不是绕过 `node_content_loader`；
5. 图谱、可视化、GraphRAG、主流程节点能否通过回归测试。

## 2. 当前结论

当前代码层面的主流程、图谱运行资产、27 号风格可视化数据投影、媒体证据索引检查、tutor 图谱材料优先级已经进一步补齐。

准确口径如下：

- LangGraph 主流程已经基本形成完整的节点制掌握学习闭环；
- A2 图谱内部节点/边没有阻塞性 dangling；
- `viewer/data.js` 已由当前 `graph.json` 重新生成，保持 27 号风格 viewer 所需的数据结构；
- `media_evidence_index` 当前存在且最小可用；
- `tutor` 已强化为优先覆盖 `node_content_context` 中的图谱 2.1 节点材料；
- 最新聚焦大回归通过：`88 passed, 5 warnings`；
- 仍需谨慎说明：当前 `graph.json` 的元数据 `generated_at` 是 `2026-04-12T12:38:04.020547+00:00`，因此不能简单宣称图谱本体就是 4/27 新生成本体；但当前 viewer/data.js 已按当前 graph.json 重建，并采用 27 号那种交互式可视化数据契约。

## 3. 本轮关键补丁

### 3.1 27 号风格 viewer/data.js 可重复生成

新增/强化：

- `ai_tutor_agent/knowledge_map/viewer_data.py`
- `scripts/sync_knowledge_map_runtime_assets.sh`
- `tests/test_graph_integrity.py`

现在可以通过以下命令从 `graph.json` 生成 27 号 viewer 所需的 `data.js`：

```bash
python -m ai_tutor_agent.knowledge_map.viewer_data \
  --graph-json a2-control-theory/graph.json \
  --output a2-control-theory/viewer/data.js
```

生成数据保持：

```text
window.A2_GRAPH_VIEWER_DATA = {
  meta: ...,
  graph: { nodes: ..., links: ... },
  notes: ...
}
```

并保留右侧教学详情栏需要的字段：

- `prerequisites`
- `neighbors`
- `learning_objectives`
- `must_know`
- `common_errors`
- `target_mastery_level`
- `difficulty`
- `internal_links`
- `inbound_links`
- `out_of_scope_links`
- `missing_links`
- `viewer_markdown_path`
- `content_excerpt`

### 3.2 图谱完整性审计口径修正

修改：

- `ai_tutor_agent/knowledge_map/graph_integrity.py`

已区分：

- 内部 dangling node reference；
- dangling edge source/target；
- 已声明的 external node reference。

当前 A2 图谱审计摘要：

```json
{
  "graph_nodes": 85,
  "graph_edges": 240,
  "issue_kinds": {
    "external_node_reference": 36
  },
  "internal_dangling_refs": 0,
  "dangling_edges": 0
}
```

说明：

- 36 个问题不是内部坏引用，而是已声明的外部先修概念；
- 当前内部边和内部节点引用没有阻塞性 dangling；
- 这些 external references 后续可以选择保留为跨域先修，或补成基础知识节点。

### 3.3 media_evidence_index 最小可用性检查

新增：

- `ai_tutor_agent/knowledge_map/runtime_assets.py`

可检查媒体证据索引：

```bash
python -m ai_tutor_agent.knowledge_map.runtime_assets \
  --media-index data/media_evidence_index
```

当前检查结果：

```json
{
  "exists": true,
  "summary_exists": true,
  "summary_valid": true,
  "chapter_count": 11,
  "annotated_file_count": 11,
  "linked_file_count": 11,
  "filtered_file_count": 11,
  "annotated_asset_count": 2928,
  "linked_candidate_count": 2928,
  "filtered_candidate_count": 2928,
  "ok": true
}
```

这说明 GraphRAG 2.2 中的媒体/公式/图表证据索引不再是缺失状态，已达到可运行底座要求。

### 3.4 同步脚本闭合

修改：

- `scripts/sync_knowledge_map_runtime_assets.sh`

现在同步脚本除恢复运行资产、构建 media index 外，还会：

1. 重建 27 号风格 viewer/data.js；
2. 检查 media_evidence_index 是否可用。

流程变为：

```text
git archive 恢复 runtime assets
→ build_media_index_batch
→ viewer_data 重建 a2-control-theory/viewer/data.js
→ runtime_assets 检查 media_evidence_index
→ completed
```

### 3.5 tutor 强化为优先使用图谱 2.1 节点材料

修改：

- `ai_tutor_agent/nodes/tutor.py`
- `tests/test_tutor.py`

关键变化：

`tutor` 现在会优先读取 state 中的：

- `node_content_context`
- `tutor_citations`
- `tutor_evidence`

并在 prompt 中明确加入：

```text
【图谱 2.1 当前节点材料】
正式讲解必须优先覆盖这里的学习目标、必会要点、常见误区和节点解释；
只有这里不足时，才补充图谱 2.2 检索或通用资料。
```

同时，如果存在 `graph_rag_pipeline.ask()` 的图谱 2.2 结果，但 state 中已经有 2.1 节点材料，`tutor` 不再直接绕过 LLM 使用 2.2 answer，而是把 2.1 材料作为主讲约束，把 2.2 作为补充上下文。

这使主流程更加符合设计分工：

- 图谱 2.1：学习路径、当前节点、节点材料、教学目标；
- 图谱 2.2：临时问题检索、证据增强、图表公式补充。

## 4. 当前运行资产状态

### 4.1 graph.json

当前：

```text
nodes: 85
edges: 240
internal dangling refs: 0
dangling edges: 0
external_node_reference: 36
```

### 4.2 viewer/data.js

当前：

```text
viewer nodes: 85
viewer links: 240
viewer notes: 85
viewer generated_at: 2026-04-12T12:38:04.020547+00:00
```

说明：

- viewer/data.js 已与当前 graph.json 同步；
- 数据格式是 27 号 viewer/app.js 所需的交互式可视化格式；
- generated_at 来自 graph.json 原始 meta，不代表本轮没有重建。

### 4.3 media_evidence_index

当前：

```text
ok: true
chapter_count: 11
annotated_asset_count: 2928
```

## 5. 测试验证

本轮已运行：

```bash
python -m compileall ai_tutor_agent tests

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_graph_integrity.py \
  tests/test_graph_rag_pipeline.py \
  tests/test_node_selection_and_content_loader.py \
  tests/test_temporary_question_flow.py \
  tests/test_tutor.py \
  tests/test_objective_learning_flow.py \
  tests/test_objective_remediation_flow.py \
  tests/test_homework_answer_flow.py \
  tests/test_session_resume_router_node.py \
  tests/test_session_resume_router.py \
  tests/test_homework_generator.py \
  tests/test_next_node_and_continue_flow.py \
  tests/test_workflow.py \
  tests/test_session.py \
  tests/test_state.py
```

结果：

```text
88 passed, 5 warnings
```

warnings 仍为已有 SWIG DeprecationWarning，不是本轮逻辑问题。

## 6. 现在可以用于汇报的简洁口径

可以这样说：

> 当前项目已经完成 LangGraph 节点制掌握学习主流程的主体闭合：从主题确认、学前诊断、图谱节点选择、节点内容加载、讲解、临时问答、节点后客观测试、错题补救、下一节点规划、作业生成，到二次登录恢复和作业处理，均已形成显式节点和可测试路由。知识图谱 2.1 负责学习路径与节点内容，图谱 2.2 负责临时问答和证据增强。A2 图谱当前包含 85 个节点、240 条边，内部无阻塞性 dangling；27 号风格可视化数据已由当前 graph.json 重建，viewer 节点、边、详情字段与 graph.json 对齐；媒体证据索引当前包含 11 个章节、2928 条标注资产，GraphRAG 可用。最新聚焦回归 88 项通过。

严谨补充：

> 需要注意的是，当前 graph.json 的原始元数据生成时间仍是 2026-04-12，因此不能简单宣称图谱本体是 4/27 新生成版本；但当前系统中的 viewer/data.js 已按 27 号交互式 viewer 契约重新生成，并与当前 graph.json 完全同步。若后续拿到真正 4/27 graph.json 本体，只需重新运行 viewer_data 和 sync 脚本即可更新可视化。

## 7. 后续剩余但非阻塞工作

1. 如果要严格对外宣称“4/27 最终图谱本体”，需要找到或重新生成 graph.json 本体，使其 meta/generated_at 与 4/27 资产一致。
2. 36 个 external_node_reference 可以继续保留为外部先修，也可以后续补成跨域基础节点。
3. 可继续扩展端到端浏览器/API 测试，覆盖真实前端会话从开始学习到作业恢复的完整路径。
4. 可把当前报告与上一份阶段报告合并成最终版汇报文档。
