"""
Centralized read-only knowledge graph query service.

Reads from course_graph_nodes (original, immutable) and user_knowledge_graph
(per-session state, read-only here). Never writes to either.

Three trigger-time query patterns:
  1. Stuck-point  → detect_prerequisite_gaps / recommend_review_target
  2. New concept  → find_successor_path / locate_in_curriculum
  3. Blind-spot   → detect_blind_spots (proactive, periodic)

Call frequency guidelines:
  - detect_prerequisite_gaps: every time user is stuck (attempt_count >= 1)
  - find_successor_path: when entering a new node for the first time
  - detect_blind_spots: at next_step decision points (not real-time)
"""
from __future__ import annotations

from typing import Any


# ── Status helpers ──

_MASTERED_STATUSES = frozenset({"mastered", "assessed_high"})
_WEAK_STATUSES = frozenset({"not_started", "assessed_low"})
_IN_PROGRESS_STATUSES = frozenset({"in_progress"})


def _node_status(user_kg: dict, title: str) -> str:
    entry = user_kg.get(title, {})
    if not isinstance(entry, dict):
        return "not_started"
    return str(entry.get("status") or "not_started").strip() or "not_started"


def _node_turn_count(user_kg: dict, title: str) -> int:
    entry = user_kg.get(title, {})
    if not isinstance(entry, dict):
        return 0
    return int(entry.get("turn_count") or 0)


# ── Core service ──

class GraphQueryService:
    """
    Read-only service that queries the original course graph structure
    and analyzes it against the user's mastery state.

    Never modifies course_graph_nodes or user_knowledge_graph.
    """

    def __init__(self, course_graph_nodes: dict[str, dict[str, Any]]) -> None:
        self._nodes = course_graph_nodes or {}
        # Pre-build reverse index: title → set of nodes that depend on it
        self._successors: dict[str, list[str]] = {}
        for title, node in self._nodes.items():
            for prereq in self._get_prerequisites(title):
                self._successors.setdefault(prereq, []).append(title)

    # ── Basic accessors ──

    def _get_prerequisites(self, title: str) -> list[str]:
        node = self._nodes.get(title)
        if not node:
            return []
        raw = node.get("prerequisites") or []
        return [str(p).strip() for p in raw if str(p).strip()]

    def _get_neighbors(self, title: str) -> list[str]:
        node = self._nodes.get(title)
        if not node:
            return []
        raw = node.get("neighbors") or []
        return [str(n).strip() for n in raw if str(n).strip()]

    def get_node(self, title: str) -> dict[str, Any] | None:
        return self._nodes.get(title)

    @property
    def all_titles(self) -> list[str]:
        return list(self._nodes.keys())

    # ── 1. Prerequisite chain traversal (recursive BFS) ──

    def find_prerequisite_chain(
        self,
        node_title: str,
        *,
        max_depth: int = 3,
    ) -> list[str]:
        """
        Walk prerequisites recursively up to max_depth.
        Returns a BFS-ordered list of prerequisite titles (no duplicates).
        Deeper ancestors appear later in the list.
        """
        visited: set[str] = set()
        chain: list[str] = []
        frontier = self._get_prerequisites(node_title)
        depth = 0

        while frontier and depth < max_depth:
            next_frontier: list[str] = []
            for prereq in frontier:
                if prereq in visited or prereq == node_title:
                    continue
                visited.add(prereq)
                chain.append(prereq)
                next_frontier.extend(self._get_prerequisites(prereq))
            frontier = next_frontier
            depth += 1

        return chain

    # ── 2. Successor path (downstream nodes) ──

    def find_successor_path(
        self,
        node_title: str,
        *,
        max_depth: int = 3,
    ) -> list[str]:
        """
        Find nodes that list this node (directly or transitively) as a
        prerequisite.  BFS order; deeper successors appear later.
        """
        visited: set[str] = set()
        path: list[str] = []
        frontier = list(self._successors.get(node_title) or [])
        depth = 0

        while frontier and depth < max_depth:
            next_frontier: list[str] = []
            for successor in frontier:
                if successor in visited or successor == node_title:
                    continue
                visited.add(successor)
                path.append(successor)
                next_frontier.extend(self._successors.get(successor) or [])
            frontier = next_frontier
            depth += 1

        return path

    # ── 3. Prerequisite gap detection (stuck-point trigger) ──

    def detect_prerequisite_gaps(
        self,
        node_title: str,
        user_kg: dict,
        *,
        max_depth: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Check whether prerequisites of *node_title* have been mastered
        in the user's knowledge graph.

        Returns a list of gap dicts, ordered by depth (shallowest first):
          [{"title": str, "status": str, "turn_count": int, "depth": int}, ...]

        Empty list means all prerequisites are mastered or there are none.
        """
        gaps: list[dict[str, Any]] = []
        visited: set[str] = set()
        frontier = [(p, 1) for p in self._get_prerequisites(node_title)]

        while frontier:
            prereq, depth = frontier.pop(0)
            if prereq in visited or prereq == node_title or depth > max_depth:
                continue
            visited.add(prereq)

            status = _node_status(user_kg, prereq)
            if status not in _MASTERED_STATUSES:
                gaps.append({
                    "title": prereq,
                    "status": status,
                    "turn_count": _node_turn_count(user_kg, prereq),
                    "depth": depth,
                })

            # Keep traversing even if this one is mastered — deeper gaps matter
            for deeper in self._get_prerequisites(prereq):
                if deeper not in visited:
                    frontier.append((deeper, depth + 1))

        # Sort: shallowest first, then weakest status first
        status_priority = {"not_started": 0, "assessed_low": 1, "in_progress": 2, "skipped": 3}
        gaps.sort(key=lambda g: (g["depth"], status_priority.get(g["status"], 9)))
        return gaps

    # ── 4. Recommend single review target (for hard routing) ──

    def recommend_review_target(
        self,
        node_title: str,
        user_kg: dict,
    ) -> str | None:
        """
        Given a stuck point, find the single most critical prerequisite
        gap to address first.  Returns None if all prerequisites are fine.
        """
        gaps = self.detect_prerequisite_gaps(node_title, user_kg, max_depth=2)
        if not gaps:
            return None
        # Prefer depth-1 not_started, then depth-1 assessed_low, etc.
        return gaps[0]["title"]

    # ── 5. Blind-spot detection (proactive trigger) ──

    def detect_blind_spots(
        self,
        user_kg: dict,
        *,
        current_node: str = "",
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Find graph nodes that are related to the user's learning path
        but have never been visited or have very low mastery.

        Checks neighbors of mastered/in-progress nodes, looking for nodes
        the user hasn't touched.
        """
        # Collect nodes the user has interacted with
        active_nodes: set[str] = set()
        for title, entry in (user_kg or {}).items():
            if isinstance(entry, dict) and entry.get("status") in (
                _MASTERED_STATUSES | _IN_PROGRESS_STATUSES
            ):
                active_nodes.add(title)

        if not active_nodes:
            return []

        # Scan neighbors and prerequisites of active nodes
        candidate_scores: dict[str, float] = {}
        for active in active_nodes:
            for neighbor in self._get_neighbors(active):
                if neighbor in active_nodes or neighbor == current_node:
                    continue
                status = _node_status(user_kg, neighbor)
                if status in _MASTERED_STATUSES:
                    continue
                # Score: not_started > assessed_low > in_progress
                score = candidate_scores.get(neighbor, 0.0)
                if status == "not_started":
                    score += 2.0
                elif status == "assessed_low":
                    score += 1.5
                else:
                    score += 0.5
                candidate_scores[neighbor] = score

        # Sort by score, return top_k
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda kv: -kv[1],
        )
        return [
            {
                "title": title,
                "status": _node_status(user_kg, title),
                "turn_count": _node_turn_count(user_kg, title),
                "score": score,
            }
            for title, score in sorted_candidates[:top_k]
        ]

    # ── 6. Curriculum position (new concept trigger) ──

    def locate_in_curriculum(
        self,
        node_title: str,
    ) -> dict[str, Any]:
        """
        Given a node, return its curriculum position:
        predecessors, current position, and successors (downstream path).
        """
        prerequisites = self.find_prerequisite_chain(node_title, max_depth=2)
        successors = self.find_successor_path(node_title, max_depth=2)
        node = self.get_node(node_title)

        return {
            "title": node_title,
            "exists_in_graph": node is not None,
            "prerequisites": prerequisites,
            "successors": successors,
            "difficulty": str((node or {}).get("difficulty") or ""),
            "target_mastery_level": str((node or {}).get("target_mastery_level") or ""),
        }

    # ── 7. Format helpers for injection into prompts ──

    def format_prerequisite_gaps_hint(
        self,
        gaps: list[dict[str, Any]],
        *,
        current_node: str = "",
    ) -> str:
        """
        Format detected prerequisite gaps as a prompt injection block.
        Returns empty string if no gaps.
        """
        if not gaps:
            return ""

        status_labels = {
            "not_started": "未开始",
            "assessed_low": "测评待补",
            "in_progress": "学习中但未掌握",
            "skipped": "已跳过",
        }
        lines = [
            "",
            "# 前驱节点缺口检测结果",
            f"当前节点【{current_node}】存在以下前置知识缺口：",
        ]
        for gap in gaps[:3]:
            label = status_labels.get(gap["status"], gap["status"])
            depth_tag = "直接前置" if gap["depth"] == 1 else f"深层前置(层{gap['depth']})"
            lines.append(
                f"- 【{gap['title']}】状态：{label}，互动轮次：{gap['turn_count']}，关系：{depth_tag}"
            )
        lines.extend([
            "",
            "**教学策略要求**：",
            "- 当前节点的卡点可能源于上述前置知识未打牢",
            "- 优先用 1-2 句话探测学生对最关键前置节点的理解",
            "- 如果确认前置缺口，建议引导学生先补前置，而不是反复解释当前节点",
        ])
        return "\n".join(lines)

    def format_successor_path_hint(
        self,
        node_title: str,
        successors: list[str],
    ) -> str:
        """Format successor path info for new-concept orientation."""
        if not successors:
            return ""

        lines = [
            "",
            "# 学习路径定位",
            f"当前节点【{node_title}】在课程图谱中的下游路径：",
            f"- 学完本节点后可以进入：{'、'.join(successors[:4])}",
            "- 请在讲解开头简要点明本节点在整体路径中的位置，帮助学生建立方向感。",
        ]
        return "\n".join(lines)

    def format_blind_spots_hint(
        self,
        blind_spots: list[dict[str, Any]],
    ) -> str:
        """Format blind-spot recommendations for next-step suggestions."""
        if not blind_spots:
            return ""

        labels = []
        for spot in blind_spots[:3]:
            labels.append(f"【{spot['title']}】")
        return f"图谱盲区提示：以下相关节点长期未被访问，建议主动推荐复习：{'、'.join(labels)}"
