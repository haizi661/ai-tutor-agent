"""Learning Plan Builder — generates a multi-step learning plan from user profile and knowledge graph.

The learning plan is a list of Steps, each containing one or more graph nodes.
Steps are ordered by topological dependency (prerequisite_of edges).
Nodes within a step are ordered by their numeric ID.

Usage:
    from ai_tutor_agent.core.learning_plan_builder import build_learning_plan

    plan = build_learning_plan(
        node_map=graph_pipeline.node_map,
        edges=graph_pipeline.edges,
        concept_gaps=state["assessment_concept_gaps"],
        difficulty_level=state["difficulty_level"],
        knowledge_graph=student_state_snapshot.get("knowledge_graph", {}),
        current_topic=state["current_topic"],
    )
"""
from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Any


def _fuzzy_match_node(concept_title: str, node_map: dict[str, dict[str, Any]],
                      min_score: float = 0.35) -> str | None:
    """将概念标题模糊匹配到 node_map 中的节点 ID。统一打分机制，选最高分。

    打分维度（每项 0-1，加权求和）：
    - 精确名称匹配: 1.0 (weight=1.0)
    - 标签匹配: 0.8 (概念标题命中节点 tags)
    - 子串包含: 0.6 (互含)
    - 字符 bigram Jaccard: 0-1 (weight=0.7)
    - 字符 containment ratio: 0-1 (weight=0.5)
    """
    if not concept_title or not node_map:
        return None
    target = concept_title.strip()

    best_nid, best_total = None, 0.0
    target_len = len(target)
    target_chars = set(target)  # pre-compute for tag fuzzy matching
    target_bigrams = {target[i:i + 2] for i in range(len(target) - 1)}
    for nid, node in node_map.items():
        name = str(node.get("name") or "").strip()
        name_len = len(name)
        len_ratio = target_len / max(name_len, 1)  # how dominant target is in name
        total = 0.0

        # 1. Exact name match
        if name == target:
            total += 1.0

        # 2. Substring containment (scaled by length ratio so suffix matches don't dominate)
        has_substring = target in name or name in target
        if has_substring:
            total += 0.6 * len_ratio

        # 3. Tags match
        tags = node.get("tags") or ""
        tag_list = []
        if isinstance(tags, list):
            tag_list = [str(t).strip("[]'\" ") for t in tags]
        elif isinstance(tags, str):
            try:
                import ast
                parsed = ast.literal_eval(tags)
                if isinstance(parsed, list):
                    tag_list = [str(t).strip("[]'\" ") for t in parsed]
            except (ValueError, SyntaxError):
                tag_list = [t.strip() for t in tags.replace("[", "").replace("]", "").replace("'", "").split(",")]
        has_exact_tag = False
        for tag in tag_list:
            if tag:
                if tag == target:
                    total += 1.5  # exact tag match — very strong signal
                    has_exact_tag = True
                    break
                elif target in tag or tag in target:
                    total += 0.7
                    break
                tag_chars = set(tag)
                if target_chars and tag_chars:
                    tag_containment = len(target_chars & tag_chars) / len(target_chars)
                    if tag_containment >= 0.6:
                        total += 0.4
                        break

        # 4. Character bigram Jaccard
        name_bigrams = {name[i:i + 2] for i in range(len(name) - 1)}
        if target_bigrams and name_bigrams:
            bi_inter = len(target_bigrams & name_bigrams)
            bi_union = len(target_bigrams | name_bigrams)
            total += 0.7 * (bi_inter / bi_union)

        # 5. Unigram containment ratio (scaled by length ratio)
        name_chars = set(name)
        if target_chars:
            containment = len(target_chars & name_chars) / len(target_chars)
            total += 0.5 * containment * len_ratio

        # 6. Pure tag bonus: exact tag match WITHOUT substring overlap is a stronger
        #    semantic signal than tag+substring coincidence (e.g. "基本概念" tag on
        #    KM001 vs "基本概念" appearing as suffix in KM021's name)
        if has_exact_tag and not has_substring:
            total += 0.6

        if total > best_total:
            best_total, best_nid = total, nid

    return best_nid if best_total >= min_score else None


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    text = str(values or "").strip()
    if not text or text in {"[]", "无", "None", "none", "null"}:
        return []
    for sep in ("||", ";", "；", ",", "，", "、"):
        if sep in text:
            return [x.strip() for x in text.split(sep) if x.strip()]
    return [text] if text else []


def _node_name(node_map: dict[str, dict[str, Any]], node_id: str) -> str:
    node = node_map.get(node_id) or {}
    return str(node.get("name") or node.get("title") or node.get("concept") or node_id).strip()


def _node_chapter(node: dict[str, Any]) -> str:
    return str(node.get("chapter") or node.get("extra", {}).get("chapter") or "").strip()


def _node_sort_key(node_id: str) -> tuple[int, str]:
    """Sort by the last numeric group in the ID, e.g. KM001 -> (1, 'KM001')."""
    m = re.search(r"(\d+)", str(node_id))
    return (int(m.group(1)), str(node_id)) if m else (9999, str(node_id))


def _is_chapter_anchor(node: dict[str, Any]) -> bool:
    import json as _json
    source_type = str(node.get("source_type") or "").strip().lower()
    extra = node.get("extra") or {}
    if isinstance(extra, str):
        try:
            extra = _json.loads(extra)
        except Exception:
            extra = {}
    extra = extra if isinstance(extra, dict) else {}
    node_role = str(extra.get("node_role") or "").strip().lower()
    return "chapter_anchor" in source_type or node_role == "chapter_anchor"


# ── Topological layer assignment ──

def _compute_topo_layers(
    node_map: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, int]:
    """Assign each node a topological layer (0 = no prerequisites, 1 = depends on layer-0, ...).

    Uses BFS from nodes with no prerequisites.  Nodes unreachable from any root
    get layer = max_layer + 1 so they still appear at the end.
    """
    # Build adjacency: prerequisite -> dependents
    prereq_to_dependents: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = defaultdict(int)
    all_ids = set(node_map.keys())

    for node_id in all_ids:
        in_degree.setdefault(node_id, 0)

    for edge in edges:
        relation = str(edge.get("relation") or "").strip().lower()
        if relation != "prerequisite_of":
            continue
        src = str(edge.get("source") or "").strip()
        tgt = str(edge.get("target") or "").strip()
        if src and tgt and src in all_ids and tgt in all_ids:
            prereq_to_dependents[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    # BFS
    layer: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for node_id in all_ids:
        if in_degree.get(node_id, 0) == 0:
            queue.append((node_id, 0))
            layer[node_id] = 0

    while queue:
        nid, depth = queue.popleft()
        for dep in prereq_to_dependents.get(nid, []):
            new_depth = depth + 1
            if dep not in layer or new_depth > layer[dep]:
                layer[dep] = new_depth
                queue.append((dep, new_depth))

    # Assign unreachable nodes
    if layer:
        max_layer = max(layer.values())
    else:
        max_layer = 0
    for node_id in all_ids:
        if node_id not in layer:
            layer[node_id] = max_layer + 1

    return layer


# ── Gap priority weighting ──

def _compute_gap_priority(
    node_map: dict[str, dict[str, Any]],
    concept_gaps: dict[str, Any],
) -> dict[str, float]:
    """Map concept gaps to node IDs and return a priority score (lower = more urgent).

    Nodes with lower calibrated scores get lower priority numbers (processed first).
    Nodes not in any gap get a default priority of 50.
    """
    gap_priority: dict[str, float] = {}
    for concept_title, raw_gap in (concept_gaps or {}).items():
        gap = dict(raw_gap or {}) if isinstance(raw_gap, dict) else {}
        node_id = str(gap.get("concept_id") or gap.get("node_id") or "").strip()
        if not node_id or node_id not in node_map:
            # Try matching by concept_title
            target = str(gap.get("concept_title") or concept_title or "").strip()
            if target:
                # Exact match first
                for nid, node in node_map.items():
                    name = str(node.get("name") or "").strip()
                    if name == target:
                        node_id = nid
                        break
                # Fuzzy fallback
                if not node_id or node_id not in node_map:
                    fuzzy_id = _fuzzy_match_node(target, node_map)
                    if fuzzy_id:
                        node_id = fuzzy_id
        if not node_id or node_id not in node_map:
            continue
        calibrated = gap.get("calibrated")
        try:
            score = float(str(calibrated))
        except (TypeError, ValueError):
            score = 50.0
        gap_priority[node_id] = score

    return gap_priority


# ── Step aggregation ──

def _nodes_per_step_for_difficulty(difficulty_level: int) -> int:
    """How many nodes to group per step based on learner difficulty level."""
    if difficulty_level <= 1:
        return 1
    if difficulty_level <= 2:
        return 2
    return 3


def _generate_step_name(
    node_ids: list[str],
    node_map: dict[str, dict[str, Any]],
) -> str:
    """Generate a human-readable step name from its node IDs."""
    if not node_ids:
        return "未知步骤"
    if len(node_ids) == 1:
        return _node_name(node_map, node_ids[0])
    # Use chapter name if all nodes share the same chapter
    chapters = set()
    for nid in node_ids:
        node = node_map.get(nid) or {}
        ch = _node_chapter(node)
        if ch:
            chapters.add(ch)
    if len(chapters) == 1:
        return next(iter(chapters))
    # Fallback: first node name + "等"
    return f"{_node_name(node_map, node_ids[0])}等"


def _generate_step_reason(
    layer: int,
    gap_priority: dict[str, float],
    node_ids: list[str],
    is_pruned: bool,
) -> str:
    """Generate a reason string for why this step exists at this position."""
    if is_pruned:
        return "学习目标的前置依赖"
    if layer == 0:
        return "课程起点，无前置依赖"
    # Check if any node in this step has a gap
    min_gap = 100.0
    for nid in node_ids:
        if nid in gap_priority and gap_priority[nid] < min_gap:
            min_gap = gap_priority[nid]
    if min_gap < 50:
        return f"诊断中该部分得分较低({min_gap:.0f}/100)，需优先补齐"
    if layer <= 2:
        return f"前置基础知识（拓扑层 {layer}）"
    return f"进阶内容（拓扑层 {layer}）"


# ── Assessment → mastered mapping ──

_MASTERED_THRESHOLD = 60  # calibrated >= this → consider mastered


def _determine_mastered_from_assessment(
    node_map: dict[str, dict[str, Any]],
    concept_gaps: dict[str, Any],
    knowledge_graph: dict[str, dict[str, Any]],
) -> set[str]:
    """Combine assessment data and student state to determine mastered nodes.

    Sources:
    1. StudentState knowledge_graph where status == 'mastered'
    2. Assessment concept_gaps where calibrated >= _MASTERED_THRESHOLD,
       matched to graph nodes by concept_id or concept name
    """
    mastered: set[str] = set()

    # Source 1: student state mastery
    for node_id, entry in (knowledge_graph or {}).items():
        if isinstance(entry, dict) and entry.get("status") == "mastered":
            mastered.add(node_id)

    # Source 2: assessment calibrated scores
    for _title, gap in (concept_gaps or {}).items():
        if not isinstance(gap, dict):
            continue
        try:
            calibrated = float(str(gap.get("calibrated", 0)))
        except (TypeError, ValueError):
            continue
        if calibrated < _MASTERED_THRESHOLD:
            continue
        # Match to graph node
        node_id = str(gap.get("concept_id") or gap.get("node_id") or "").strip()
        if node_id and node_id in node_map:
            mastered.add(node_id)
            continue
        # Fallback: match by concept name (exact → fuzzy)
        concept_title = str(gap.get("concept_title") or _title or "").strip()
        if concept_title:
            matched = False
            for nid, node in node_map.items():
                name = str(node.get("name") or "").strip()
                if name == concept_title:
                    mastered.add(nid)
                    matched = True
                    break
            if not matched:
                fuzzy_id = _fuzzy_match_node(concept_title, node_map)
                if fuzzy_id:
                    mastered.add(fuzzy_id)

    return mastered


# ── Main builder ──

def build_learning_plan(
    *,
    node_map: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    concept_gaps: dict[str, Any] | None = None,
    difficulty_level: int = 3,
    knowledge_graph: dict[str, dict[str, Any]] | None = None,
    current_topic: str = "",
    target_node_id: str = "",
) -> list[dict[str, Any]]:
    """Build a multi-step learning plan from graph topology.

    Algorithm:
    1. Determine mastered nodes (from student state + assessment calibrated >= 60)
    2. If target specified, prune to prerequisite chain
    3. BFS from roots by topological layer, skip mastered
    4. Within each layer, nodes with lower assessment scores come first
       (branch priority: weaker branches first)
    5. Group layers into steps (respecting difficulty_level for nodes_per_step)

    Returns a list of step dicts with the standard schema.
    """
    if not node_map:
        return []

    concept_gaps = concept_gaps or {}
    knowledge_graph = knowledge_graph or {}

    # ── Phase 1: Determine mastered nodes ──
    mastered = _determine_mastered_from_assessment(node_map, concept_gaps, knowledge_graph)

    # ── Phase 2: Compute topology ──
    layer_map = _compute_topo_layers(node_map, edges)

    # ── Phase 3: Pruning (if target specified) ──
    reachable: set[str] | None = None
    if target_node_id and target_node_id in node_map:
        reachable = _find_prerequisite_chain(node_map, edges, target_node_id)
        reachable.add(target_node_id)

    # ── Phase 4: Collect active nodes by layer ──
    layer_groups: dict[int, list[str]] = defaultdict(list)
    for node_id in node_map:
        if node_id in mastered:
            continue
        if reachable is not None and node_id not in reachable:
            continue
        node = node_map.get(node_id) or {}
        if _is_chapter_anchor(node):
            continue
        layer = layer_map.get(node_id, 0)
        layer_groups[layer].append(node_id)

    if not layer_groups:
        return []

    # ── Phase 5: Within-layer branch priority ──
    # Nodes with lower calibrated scores (from assessment) come first within each layer.
    # Nodes without assessment data keep their default order (by numeric ID).
    gap_priority = _compute_gap_priority(node_map, concept_gaps)

    for layer_num in layer_groups:
        layer_groups[layer_num].sort(key=lambda nid: (
            gap_priority.get(nid, 50.0),  # lower calibrated = higher priority
            _node_sort_key(nid),           # tie-break by ID
        ))

    # ── Phase 6: Aggregate into steps ──
    max_nodes_per_step = _nodes_per_step_for_difficulty(difficulty_level)
    steps: list[dict[str, Any]] = []
    layer_to_step_indices: dict[int, list[int]] = defaultdict(list)

    for layer_num in sorted(layer_groups.keys()):
        nodes_in_layer = layer_groups[layer_num]

        # Split into chunks of max_nodes_per_step
        chunks: list[list[str]] = []
        for i in range(0, len(nodes_in_layer), max_nodes_per_step):
            chunk = nodes_in_layer[i : i + max_nodes_per_step]
            chunks.append(chunk)

        # Further split by chapter if a chunk spans multiple chapters
        final_chunks: list[list[str]] = []
        for chunk in chunks:
            chapter_groups: dict[str, list[str]] = defaultdict(list)
            for nid in chunk:
                node = node_map.get(nid) or {}
                ch = _node_chapter(node) or "未分类"
                chapter_groups[ch].append(nid)
            if len(chapter_groups) <= 1:
                final_chunks.append(chunk)
            else:
                for ch in sorted(chapter_groups.keys()):
                    final_chunks.append(chapter_groups[ch])

        for chunk in final_chunks:
            step_idx = len(steps)
            step = {
                "step_index": step_idx,
                "step_name": _generate_step_name(chunk, node_map),
                "node_ids": chunk,
                "node_names": [_node_name(node_map, nid) for nid in chunk],
                "status": "pending",
                "reason": _generate_step_reason(layer_num, gap_priority, chunk, reachable is not None),
                "estimated_difficulty": _estimate_step_difficulty(chunk, node_map, gap_priority),
                "prerequisite_steps": [],
            }
            steps.append(step)
            layer_to_step_indices[layer_num].append(step_idx)

    # ── Phase 7: Wire prerequisite_steps ──
    sorted_layers = sorted(layer_to_step_indices.keys())
    for i, layer_num in enumerate(sorted_layers):
        if i == 0:
            continue
        prev_layer = sorted_layers[i - 1]
        prev_step_indices = layer_to_step_indices[prev_layer]
        for step_idx in layer_to_step_indices[layer_num]:
            steps[step_idx]["prerequisite_steps"] = prev_step_indices[:]

    # ── Mark first step as in_progress ──
    if steps:
        steps[0]["status"] = "in_progress"

    return steps


def _estimate_step_difficulty(
    node_ids: list[str],
    node_map: dict[str, dict[str, Any]],
    gap_priority: dict[str, float],
) -> int:
    """Estimate step difficulty 1-5 based on gap scores and node metadata."""
    if not node_ids:
        return 3
    scores: list[float] = []
    for nid in node_ids:
        if nid in gap_priority:
            scores.append(gap_priority[nid])
        else:
            scores.append(50.0)
    avg = sum(scores) / len(scores) if scores else 50.0
    # Lower gap score = harder for student → higher difficulty
    # calibrated 0-20 → difficulty 5
    # calibrated 20-40 → difficulty 4
    # calibrated 40-60 → difficulty 3
    # calibrated 60-80 → difficulty 2
    # calibrated 80-100 → difficulty 1
    if avg <= 20:
        return 5
    if avg <= 40:
        return 4
    if avg <= 60:
        return 3
    if avg <= 80:
        return 2
    return 1


def _find_prerequisite_chain(
    node_map: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    target_node_id: str,
) -> set[str]:
    """BFS backwards from target_node_id to find all prerequisite nodes."""
    # Build reverse adjacency: target -> prerequisites
    target_to_prereqs: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        relation = str(edge.get("relation") or "").strip().lower()
        if relation != "prerequisite_of":
            continue
        src = str(edge.get("source") or "").strip()
        tgt = str(edge.get("target") or "").strip()
        if src and tgt:
            target_to_prereqs[tgt].append(src)

    visited: set[str] = set()
    queue: deque[str] = deque([target_node_id])
    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)
        for prereq in target_to_prereqs.get(nid, []):
            if prereq not in visited and prereq in node_map:
                queue.append(prereq)

    visited.discard(target_node_id)
    return visited



# ── Step navigation helpers ──

def find_next_node_in_step(
    step: dict[str, Any],
    visited_nodes: set[str],
    current_node_id: str = "",
) -> str:
    """Find the first unvisited node AFTER the current node in a step.

    Only considers nodes that appear AFTER current_node_id in the step's
    node_ids list. This prevents backward jumps within a round — if a user
    fails node KM001 and chooses 'do_later', the same KM001 won't be
    re-picked as the next node once the system has moved on to KM002.
    """
    node_ids = step.get("node_ids", [])
    if not node_ids:
        return ""

    if current_node_id and current_node_id in node_ids:
        start = node_ids.index(current_node_id) + 1
    else:
        start = 0

    for node_id in node_ids[start:]:
        if node_id not in visited_nodes:
            return node_id
    return ""


def is_step_completed(
    step: dict[str, Any],
    visited_nodes: set[str],
) -> bool:
    """Check if all nodes in a step have been visited (learned)."""
    for node_id in step.get("node_ids", []):
        if node_id not in visited_nodes:
            return False
    return True


def find_current_step_progress(
    plan: list[dict[str, Any]],
    visited_nodes: set[str],
) -> tuple[int, int, int]:
    """Return (current_step_index, nodes_completed_in_step, total_nodes_in_step).

    If all steps are completed, returns (len(plan), 0, 0).
    """
    for i, step in enumerate(plan):
        if step.get("status") == "completed":
            continue
        node_ids = step.get("node_ids", [])
        completed = sum(1 for nid in node_ids if nid in visited_nodes)
        if completed < len(node_ids):
            return i, completed, len(node_ids)
    return len(plan), 0, 0


# ── Dynamic plan update ──

def update_learning_plan(
    *,
    completed_step_index: int,
    plan: list[dict[str, Any]],
    node_map: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    concept_gaps: dict[str, Any] | None = None,
    knowledge_graph: dict[str, dict[str, Any]] | None = None,
    current_topic: str = "",
    target_node_id: str = "",
    nodes_per_step: int = 3,
) -> list[dict[str, Any]]:
    """Recalculate future steps after completing a step.

    Preserves completed steps, rebuilds remaining steps using updated
    mastery state. Delegates to build_learning_plan() for the remaining
    portion, then merges.

    Returns the updated plan.
    """
    if not plan or completed_step_index < 0 or completed_step_index >= len(plan):
        return plan

    concept_gaps = concept_gaps or {}
    knowledge_graph = knowledge_graph or {}

    # Keep completed steps as-is
    preserved = plan[:completed_step_index + 1]
    for step in preserved:
        step["status"] = "completed"

    # Collect nodes already assigned to completed steps
    assigned_nodes: set[str] = set()
    for step in preserved:
        assigned_nodes.update(step.get("node_ids", []))

    # Build augmented knowledge_graph: mark assigned nodes as mastered
    # so build_learning_plan skips them
    augmented_kg = dict(knowledge_graph)
    for nid in assigned_nodes:
        if nid not in augmented_kg:
            augmented_kg[nid] = {"status": "mastered"}

    # Use difficulty_level from preserved steps to infer nodes_per_step
    difficulty_level = 3
    if preserved:
        last_diff = preserved[-1].get("estimated_difficulty", 3)
        if last_diff:
            difficulty_level = int(last_diff)

    # Build remaining plan
    remaining = build_learning_plan(
        node_map=node_map,
        edges=edges,
        concept_gaps=concept_gaps,
        difficulty_level=difficulty_level,
        knowledge_graph=augmented_kg,
        current_topic=current_topic,
        target_node_id=target_node_id,
    )

    if not remaining:
        return preserved

    # Merge: preserved steps + remaining steps with re-indexed step_index
    base_idx = len(preserved)
    for idx, step in enumerate(remaining):
        step["step_index"] = base_idx + idx
        step["status"] = "in_progress" if idx == 0 else "pending"
        # Wire prerequisite_steps: all preserved + previous remaining
        step["prerequisite_steps"] = list(range(base_idx + idx)) if idx > 0 else [base_idx - 1] if base_idx > 0 else []
        preserved.append(step)

    # Re-index all steps for consistency
    for i, step in enumerate(preserved):
        step["step_index"] = i

    return preserved
