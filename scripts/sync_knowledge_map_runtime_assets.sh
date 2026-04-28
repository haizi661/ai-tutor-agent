#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMIT_REF="${1:-8c15fdf}"

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

echo "[sync] rebuilding 27-style A2 viewer data.js from graph.json"

python -m ai_tutor_agent.knowledge_map.viewer_data \
  --graph-json a2-control-theory/graph.json \
  --output a2-control-theory/viewer/data.js

echo "[sync] verifying media evidence index"

python -m ai_tutor_agent.knowledge_map.runtime_assets \
  --media-index data/media_evidence_index \
  --require-media-index

echo "[sync] completed"
