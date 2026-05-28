#!/bin/bash
# scripts/check_runtime_assets.sh
# 检查 AI Tutor Agent 运行资产完整性
#
# 用法:
#   bash scripts/check_runtime_assets.sh
#
# 检查项:
#   1. 图谱 B nodes/edges CSV 存在
#   2. 图谱 B JSON 存在
#   3. media_evidence_index/batch_summary.json 存在且格式正确
#   4. GraphRAGPipeline 默认读取图谱 B
#   5. 内部 dangling refs 检查

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

check_warn() {
    echo -e "  ${YELLOW}!${NC} $1"
    WARN=$((WARN + 1))
}

echo ""
echo "=========================================="
echo "  AI Tutor Agent — 运行资产检查"
echo "=========================================="
echo ""

# ── 1. 图谱 B CSV ──────────────────────────────────────────────────────────
echo "[1] 图谱 B CSV 文件"

NODES_CSV="$DATA_DIR/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv"
EDGES_CSV="$DATA_DIR/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv"

if [ -f "$NODES_CSV" ]; then
    NODES_COUNT=$(wc -l < "$NODES_CSV" | tr -d ' ')
    check_pass "nodes.csv 存在 ($NODES_COUNT 行)"
else
    check_fail "nodes.csv 不存在: $NODES_CSV"
fi

if [ -f "$EDGES_CSV" ]; then
    EDGES_COUNT=$(wc -l < "$EDGES_CSV" | tr -d ' ')
    check_pass "edges.csv 存在 ($EDGES_COUNT 行)"
else
    check_fail "edges.csv 不存在: $EDGES_CSV"
fi

# ── 2. 图谱 B JSON ──────────────────────────────────────────────────────────
echo ""
echo "[2] 图谱 B JSON"

GRAPH_JSON="$DATA_DIR/knowledge_map_outputs/auto_control_knowledge_map_v2.json"

if [ -f "$GRAPH_JSON" ]; then
    # Check if valid JSON
    if python3 -c "import json; json.load(open('$GRAPH_JSON'))" 2>/dev/null; then
        check_pass "graph JSON 存在且格式正确"
    else
        check_fail "graph JSON 存在但格式无效"
    fi
else
    check_fail "graph JSON 不存在: $GRAPH_JSON"
fi

# ── 3. media_evidence_index ─────────────────────────────────────────────────
echo ""
echo "[3] media_evidence_index"

MEDIA_INDEX_DIR="$DATA_DIR/media_evidence_index"
BATCH_SUMMARY="$MEDIA_INDEX_DIR/batch_summary.json"

if [ -d "$MEDIA_INDEX_DIR" ]; then
    ASSET_COUNT=$(find "$MEDIA_INDEX_DIR" -name "*_annotated_assets.jsonl" | wc -l | tr -d ' ')
    check_pass "media_evidence_index 目录存在 ($ASSET_COUNT 个 annotated_assets 文件)"
else
    check_fail "media_evidence_index 目录不存在: $MEDIA_INDEX_DIR"
fi

if [ -f "$BATCH_SUMMARY" ]; then
    # Check if valid JSON
    if python3 -c "import json; json.load(open('$BATCH_SUMMARY'))" 2>/dev/null; then
        check_pass "batch_summary.json 存在且格式正确"
    else
        check_fail "batch_summary.json 存在但格式无效"
    fi
else
    check_fail "batch_summary.json 不存在: $BATCH_SUMMARY"
fi

# ── 4. GraphRAGPipeline 配置检查 ────────────────────────────────────────────
echo ""
echo "[4] GraphRAGPipeline 配置"

GRAPH_RAG_MODULE="$PROJECT_ROOT/ai_tutor_agent/knowledge_map/graph_rag_pipeline.py"

if [ -f "$GRAPH_RAG_MODULE" ]; then
    # Check if it references Graph B
    if grep -q "auto_control_knowledge_map_v2" "$GRAPH_RAG_MODULE" 2>/dev/null; then
        check_pass "graph_rag_pipeline.py 引用图谱 B (v2)"
    else
        check_warn "graph_rag_pipeline.py 未找到图谱 B 引用，请手动确认"
    fi
else
    check_warn "graph_rag_pipeline.py 不存在"
fi

# ── 5. 内部 dangling refs 检查 ──────────────────────────────────────────────
echo ""
echo "[5] 内部 dangling refs 检查"

# Check if there are references to old Graph A paths
OLD_GRAPH_REFS=$(grep -r "auto_control_knowledge_map\.json" "$PROJECT_ROOT/ai_tutor_agent/" --include="*.py" 2>/dev/null | grep -v "v2" | grep -v "__pycache__" | wc -l | tr -d ' ')

if [ "$OLD_GRAPH_REFS" -eq 0 ]; then
    check_pass "无旧 Graph A 路径引用"
else
    check_warn "发现 $OLD_GRAPH_REFS 处旧 Graph A 路径引用"
fi

# Check for references to old docs/archive paths in active code
ARCHIVE_REFS=$(grep -r "docs/archive/a2-control-theory" "$PROJECT_ROOT/ai_tutor_agent/" --include="*.py" 2>/dev/null | grep -v "__pycache__" | wc -l | tr -d ' ')

if [ "$ARCHIVE_REFS" -eq 0 ]; then
    check_pass "无归档路径引用在活跃代码中"
else
    check_warn "发现 $ARCHIVE_REFS 处归档路径引用在活跃代码中"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "  检查结果"
echo "=========================================="
echo -e "  ${GREEN}通过: $PASS${NC}"
echo -e "  ${YELLOW}警告: $WARN${NC}"
echo -e "  ${RED}失败: $FAIL${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}存在失败项，请修复后重试。${NC}"
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo -e "${YELLOW}存在警告项，请确认。${NC}"
    exit 0
else
    echo -e "${GREEN}所有检查通过。${NC}"
    exit 0
fi
