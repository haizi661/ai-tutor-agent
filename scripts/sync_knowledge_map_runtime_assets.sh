#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMIT_REF="${1:-8c15fdf}"
ARCHIVED_A2_GRAPH_JSON="docs/archive/a2-control-theory/graph.json"
ARCHIVED_A2_VIEWER_DATA_JS="docs/archive/a2-control-theory/viewer/data.js"

cd "$ROOT_DIR"

echo "[sync] restoring knowledge_map runtime assets from ${COMMIT_REF}"

git archive "$COMMIT_REF" \
  data/bm25_cache.json \
  data/bm25_cache__course_primary.json \
  data/knowledge_map_outputs \
  data/knowledge_splits \
  data/mineru_cache | tar -x

echo "[sync] building media evidence index"

python -m ai_tutor_agent.knowledge_map.build_media_index_batch \
  --mineru-cache-root data/mineru_cache \
  --nodes-csv data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv \
  --output-dir data/media_evidence_index

if [[ -f "$ARCHIVED_A2_GRAPH_JSON" ]]; then
  echo "[sync] refreshing archived A2 viewer data.js (compatibility artifact)"

  python -m ai_tutor_agent.knowledge_map.viewer_data \
    --graph-json "$ARCHIVED_A2_GRAPH_JSON" \
    --output "$ARCHIVED_A2_VIEWER_DATA_JS"
else
  echo "[sync] archived A2 graph package not found; skip viewer data.js refresh"
fi

echo "[sync] verifying media evidence index"

python -m ai_tutor_agent.knowledge_map.runtime_assets \
  --media-index data/media_evidence_index \
  --require-media-index

echo "[sync] completed"
