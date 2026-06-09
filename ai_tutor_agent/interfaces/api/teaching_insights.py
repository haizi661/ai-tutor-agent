"""教学洞察 API — 聚合 teaching_episodes 数据，展示教学策略效果。"""

from collections import Counter, defaultdict
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...knowledge_map.student_state import StudentStateStore
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["teaching_insights"])


def _load_store(request: Request) -> StudentStateStore:
    runtime = get_runtime(request)
    store = getattr(runtime, "student_state_store", None)
    if store is None:
        raise RuntimeError("Student state store not available")
    return store


def _aggregate_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """将原始 teaching_episodes 列表聚合为教学洞察结构。"""
    if not episodes:
        return {
            "summary": {
                "total_episodes": 0,
                "strategy_distribution": {},
                "affect_distribution": {},
                "entry_mode_distribution": {},
                "total_nodes_visited": 0,
            },
            "node_details": [],
            "recent_episodes": [],
        }

    # --- Summary ---
    strategy_dist: dict[str, int] = dict(Counter(e.get("strategy", "") for e in episodes))
    affect_dist: dict[str, int] = dict(Counter(e.get("affect", "") for e in episodes))
    entry_mode_dist: dict[str, int] = dict(Counter(e.get("entry_mode", "") for e in episodes))

    # Remove empty-string keys
    for d in (strategy_dist, affect_dist, entry_mode_dist):
        d.pop("", None)

    # --- Per-node aggregation ---
    node_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ep in episodes:
        nid = ep.get("node_id", "")
        if nid:
            node_groups[nid].append(ep)

    node_details = []
    for nid, group in sorted(node_groups.items(), key=lambda kv: max(
        e.get("created_at", "") for e in kv[1]
    ), reverse=True):
        title = group[0].get("node_title") or nid
        attempt_count = max(e.get("attempt_count", 0) for e in group)
        strategies = dict(Counter(e.get("strategy", "") for e in group))
        strategies.pop("", None)
        affects = dict(Counter(e.get("affect", "") for e in group))
        affects.pop("", None)
        entry_modes = dict(Counter(e.get("entry_mode", "") for e in group))
        entry_modes.pop("", None)
        created_times = [e.get("created_at", "") for e in group if e.get("created_at")]
        node_details.append({
            "node_id": nid,
            "node_title": title,
            "attempt_count": attempt_count,
            "total_visits": len(group),
            "strategy_distribution": strategies,
            "affect_distribution": affects,
            "entry_mode_distribution": entry_modes,
            "first_seen": min(created_times) if created_times else "",
            "latest_seen": max(created_times) if created_times else "",
        })

    # --- Summary totals ---
    summary = {
        "total_episodes": len(episodes),
        "strategy_distribution": strategy_dist,
        "affect_distribution": affect_dist,
        "entry_mode_distribution": entry_mode_dist,
        "total_nodes_visited": len(node_details),
    }

    # --- Recent episodes (last 10) ---
    sorted_ep = sorted(
        episodes,
        key=lambda e: e.get("created_at", ""),
        reverse=True,
    )
    recent = sorted_ep[:10]

    return {
        "summary": summary,
        "node_details": node_details,
        "recent_episodes": recent,
    }


@router.get("/students/{student_id}/teaching-insights")
async def get_teaching_insights(
    student_id: str,
    request: Request,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """返回某个学习者的教学洞察聚合数据，可按日期范围筛选 (ISO 8601)。"""
    store = _load_store(request)
    try:
        state = store.load(student_id)
    except Exception:
        return JSONResponse(
            content={"summary": {"total_episodes": 0}, "node_details": [], "recent_episodes": []},
            status_code=200,
        )

    episodes: list[dict[str, Any]] = list(getattr(state, "teaching_episodes", []) or [])

    # 日期范围过滤（ISO 8601 字符串字典序可直接比较）
    if start:
        episodes = [e for e in episodes if (e.get("created_at") or "") >= start]
    if end:
        end_iso = end if "T" in end else end + "T23:59:59"
        episodes = [e for e in episodes if (e.get("created_at") or "") <= end_iso]

    result = _aggregate_episodes(episodes)

    # Attach snapshot info for frontend display
    result["snapshot"] = {
        "current_node_id": getattr(state, "current_node_id", ""),
        "student_id": student_id,
    }

    return result
