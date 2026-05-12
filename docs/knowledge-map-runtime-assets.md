# Knowledge Map 运行资产接入说明

## 目标

把 `2026-04-27` 上传的运行结果包按“本地运行资产”方式接入当前项目，同时避免把本地缓存、向量库和用户状态误并入源码层。

## 应接入的资产

- `data/mineru_cache/**`
- `data/knowledge_map_outputs/**`
- `data/knowledge_splits/**`
- `data/bm25_cache.json`
- `data/bm25_cache__course_primary.json`

这些内容用于：

- 图谱 2.1 节点与边的离线产物读取
- 图谱搜索 2.2 的章节媒体索引扫描
- 章节 PDF 拆分后的运行输入
- 传统检索缓存的本地恢复

## 不应并入源码主分支的运行态文件

- `data/chroma_db/**`
- `data/knowledge_map_vector_db/**`
- `data/student_states/*.json`
- `data/tutor_memory.db`
- `data/retrieval_state.json`

这些内容属于：

- 本地向量库
- 本地会话库
- 某个学生的学习记录
- 某次运行的临时状态

它们应该由本地环境生成或恢复，不应作为功能源码的一部分提交。

## 与当前项目的路径约定

- 旧检索子系统仍使用 `data/minerU_cache`
- `knowledge_map` / 图谱搜索 2.2 使用 `data/mineru_cache`

这两个目录目前并存。主流程重构阶段不去强行合并旧路径，而是保持：

- 旧流程继续读 `data/minerU_cache`
- 新图谱链路统一读 `data/mineru_cache`

## 为什么还需要重新构建 `data/media_evidence_index`

`2026-04-27` 的备份提交没有包含 `data/media_evidence_index/**`。

因此即使已经同步了 `data/mineru_cache` 与 `data/knowledge_map_outputs`，图谱搜索 2.2 的媒体证据链路仍然是不完整的。必须再执行一次：

```bash
python -m ai_tutor_agent.knowledge_map.build_media_index_batch \
  --mineru-cache-root data/mineru_cache \
  --nodes-csv data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv \
  --output-dir data/media_evidence_index
```

## 一键同步方式

仓库内提供了本地同步脚本：

```bash
scripts/sync_knowledge_map_runtime_assets.sh
```

它会从本仓库已有的 `8c15fdf` 提交中提取：

- `data/mineru_cache`
- `data/knowledge_map_outputs`
- `data/knowledge_splits`
- `data/bm25_cache*.json`

随后会自动：

1. 构建 `data/media_evidence_index`。
2. 如果归档 A2 图谱包存在，则从 `docs/archive/a2-control-theory/graph.json` 重新生成 `docs/archive/a2-control-theory/viewer/data.js`，作为兼容性静态 viewer 工件。
3. 检查图谱 B nodes/edges CSV 与媒体证据索引是否达到最小可用状态。
4. 历史 A2 / Graph A 资料仍只保留在 `docs/archive/a2-control-theory/`，不会被当作当前主教学图谱；viewer 刷新只是为了让归档静态页面继续可打开。

## 最小验证

同步完成后，至少检查这几项：

```bash
test -f data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv
test -d data/mineru_cache
test -f data/media_evidence_index/batch_summary.json
test -f data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv
test -f docs/archive/a2-control-theory/viewer/data.js
python -m ai_tutor_agent.knowledge_map.runtime_assets --media-index data/media_evidence_index
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_graph_integrity.py
```

当前图谱口径：

```text
graph nodes: 42
graph edges: 95
internal dangling refs: 0
dangling edges: 0
external_node_reference: 0
```

说明：当前主教学图谱是 2026-04-27 图谱 B 运行资产，不再把历史 A2 / Graph A 的 `graph.json` 表述为当前主图谱。
