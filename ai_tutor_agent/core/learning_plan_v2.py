"""Learning Plan v2 — 自适应学习路径生成器(支持多次生成、节点重入、错题驱动)。

完整产品规则:
1. **多次生成**:完整学习旅程 = 4-5 次路径,每次 9-12 节点 / 4 step
2. **节点重入**:一次失败,下次路径可重新进入该节点(entry_mode 自动升级)
3. **错题驱动**:错题节点下次路径优先级 ↑↑,自动加入候选
4. **画像驱动**:mastery + confidence + source 决定 entry_mode
5. **章序硬约束**:step 内同 chapter,step 间章序不递减
6. **续上次**:进入时检测是否有 in_progress 路径,有就续上

算法 7 步:
  1. 候选集 = 全图谱 - 已 mastered
  2. 紧迫度公式 = 0.30×Goal + 0.25×PrereqImport + 0.20×Gap + 0.15×Uncertainty + 0.10×Failure
  3. 章序 + 拓扑排序
  4. 选 9-12 节点(有弹性)
  5. 聚类成 4 step(同 chapter + ability)
  6. entry_mode 决策(每节点)
  7. step 命名 + 持久化

输入:StudentProfile + 节点图谱 + 历史路径
输出:LearningPlan dataclass
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .ability_mapper import (
    get_all_node_ids,
    get_node_difficulty,
    get_node_estimated_time,
    get_node_importance,
    get_node_name_map,
    get_node_primary_ability,
)
from .student_profile import StudentProfile


# ── 外部接口(给 nodes/learning_plan_generator.py 用) ──

ENABLE_CACHING = True

# ── Dataclasses ─────────────────────────────────────

@dataclass
class StepEntry:
    step_index: int = 0
    step_name: str = ""
    step_goal: str = ""
    step_ability: str = ""
    chapter: str = ""
    node_ids: list[str] = field(default_factory=list)
    entry_modes: dict[str, str] = field(default_factory=dict)
    reason: str = ""
    status: str = "pending"  # pending | in_progress | completed

    def to_dict(self) -> dict[str, Any]:
        name_map = get_node_name_map()
        return {
            "step_index": self.step_index,
            "step_name": self.step_name,
            "step_goal": self.step_goal,
            "step_ability": self.step_ability,
            "chapter": self.chapter,
            "node_ids": list(self.node_ids),
            "node_names": [name_map.get(nid, nid) for nid in self.node_ids],
            "entry_modes": dict(self.entry_modes),
            "reason": self.reason,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "StepEntry":
        return cls(
            step_index=int(raw.get("step_index", 0)),
            step_name=str(raw.get("step_name", "")),
            step_goal=str(raw.get("step_goal", "")),
            step_ability=str(raw.get("step_ability", "")),
            chapter=str(raw.get("chapter", "")),
            node_ids=list(raw.get("node_ids", [])),
            entry_modes=dict(raw.get("entry_modes", {})),
            reason=str(raw.get("reason", "")),
            status=str(raw.get("status", "pending")),
        )


@dataclass
class LearningPlan:
    steps: list[StepEntry] = field(default_factory=list)
    total_nodes: int = 0
    total_steps: int = 0
    generated_at: str = ""
    source: str = ""      # cold_start / replan / resume
    session_index: int = 0  # 第几次 session

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "total_nodes": self.total_nodes,
            "total_steps": self.total_steps,
            "generated_at": self.generated_at,
            "source": self.source,
            "session_index": self.session_index,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LearningPlan":
        return cls(
            steps=[StepEntry.from_dict(s) for s in raw.get("steps", [])],
            total_nodes=int(raw.get("total_nodes", 0)),
            total_steps=int(raw.get("total_steps", 0)),
            generated_at=str(raw.get("generated_at", "")),
            source=str(raw.get("source", "")),
            session_index=int(raw.get("session_index", 0)),
        )

    def resolve_status(self) -> str:
        """解析路径整体状态: all_completed / in_progress / blocked"""
        if not self.steps:
            return "completed"
        any_in_progress = any(s.status == "in_progress" for s in self.steps)
        all_completed = all(s.status == "completed" for s in self.steps)
        if all_completed:
            return "completed"
        if any_in_progress:
            return "in_progress"
        return "blocked"

    def get_current_step(self) -> int | None:
        """返回当前 in_progress 的 step_index,无则 None。"""
        for s in self.steps:
            if s.status == "in_progress":
                return s.step_index
        return None

    def get_in_progress_nodes(self) -> list[str]:
        """返回当前 in_progress step 中尚未完成的节点列表。"""
        cur = self.get_current_step()
        if cur is None:
            return []
        step = self.steps[cur]
        return list(step.node_ids)

    def get_all_node_ids(self) -> list[str]:
        result = []
        for s in self.steps:
            result.extend(s.node_ids)
        return result

    def get_mastered_count(self, profile: StudentProfile) -> int:
        return sum(1 for nid in self.get_all_node_ids() if profile.is_mastered(nid))


# ── Step 模板(供快速生成用) ─────────────────────────

# 自动控制原理 6 步模板(基于章节 + ability)
_STEP_TEMPLATE = [
    {
        "step_name": "建立自动控制基础认知",
        "step_ability": "B",
        "node_ids": ["KM001", "KM002", "KM003", "KM004", "KM005", "KM006"],
        "chapter": "第一章",
    },
    {
        "step_name": "建立数学建模能力",
        "step_ability": "C",
        "node_ids": ["KM007", "KM008", "KM009", "KM010", "KM011"],
        "chapter": "第二章",
    },
    {
        "step_name": "掌握时域分析与稳定性",
        "step_ability": "E",
        "node_ids": ["KM012", "KM013", "KM014", "KM015", "KM016", "KM017", "KM018", "KM019"],
        "chapter": "第三章",
    },
    {
        "step_name": "掌握根轨迹分析法",
        "step_ability": "G",
        "node_ids": ["KM020", "KM021", "KM022", "KM023", "KM024", "KM025"],
        "chapter": "第四章",
    },
    {
        "step_name": "掌握频域分析与校正",
        "step_ability": "H",
        "node_ids": ["KM026", "KM027", "KM028", "KM029", "KM030", "KM031", "KM032", "KM033", "KM034"],
        "chapter": "第五、六章",
    },
    {
        "step_name": "进入离散系统与综合",
        "step_ability": "H",
        "node_ids": ["KM035", "KM036", "KM037", "KM038", "KM039", "KM040", "KM041", "KM042"],
        "chapter": "第七~十章",
    },
]

# 节点 → 章节映射(快速查找)
_NODE_CHAPTER: dict[str, str] = {
    "KM001": "第一章", "KM002": "第一章", "KM003": "第一章", "KM004": "第一章",
    "KM005": "第一章", "KM006": "第一章",
    "KM007": "第二章", "KM008": "第二章", "KM009": "第二章", "KM010": "第二章",
    "KM011": "第二章",
    "KM012": "第三章", "KM013": "第三章", "KM014": "第三章", "KM015": "第三章",
    "KM016": "第三章", "KM017": "第三章", "KM018": "第三章", "KM019": "第三章",
    "KM020": "第四章", "KM021": "第四章", "KM022": "第四章", "KM023": "第四章",
    "KM024": "第四章", "KM025": "第四章",
    "KM026": "第五章", "KM027": "第五章", "KM028": "第五章", "KM029": "第五章",
    "KM030": "第六章", "KM031": "第六章", "KM032": "第六章", "KM033": "第六章",
    "KM034": "第六章",
    "KM035": "第七章", "KM036": "第七章", "KM037": "第七章",
    "KM038": "第八章", "KM039": "第八章", "KM040": "第八章",
    "KM041": "第九章",
    "KM042": "第十章",
}

# 章节顺序索引(跨章排序用)
_CHAPTER_ORDER: dict[str, int] = {
    "第一章": 1, "第二章": 2, "第三章": 3, "第四章": 4,
    "第五章": 5, "第六章": 6, "第七章": 7, "第八章": 8,
    "第九章": 9, "第十章": 10,
}

_DUMMY_EDGES: list[dict] = []

# 节点重要性排序权重(core 优先于 supporting)
_IMPORTANCE_ORDER: dict[str, int] = {"core": 0, "supporting": 1, "other": 2}


# ── 工具函数 ───────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def _get_node_chapter(node_id: str) -> str:
    return _NODE_CHAPTER.get(node_id, "其他")


def _get_chapter_order(node_id: str) -> int:
    ch = _get_node_chapter(node_id)
    return _CHAPTER_ORDER.get(ch, 999)


# ── 算法 7 步 ──────────────────────────────────────

# ── Step 1: 候选集 ────────────────────────────

def compute_candidates(
    all_node_ids: list[str] | None = None,
    mastered_set: set[str] | None = None,
) -> list[str]:
    """候选集 = 全图谱 - 已 mastered

    已 mastered 的定义:
    - mastery >= 0.85 AND confidence >= 0.7(即 profile.is_mastered)
    """
    if all_node_ids is None:
        all_node_ids = get_all_node_ids()
    mastered = mastered_set or set()
    return [nid for nid in all_node_ids if nid not in mastered]


# ── Step 2: 紧迫度计算 ─────────────────────────

def compute_urgency(
    node_id: str,
    profile: StudentProfile,
    goal_relevance: float = 0.5,
    prereq_importance: float = 0.3,
) -> float:
    """紧迫度公式:值越大越应该优先选。

    Priority(v) =
      0.30 × GoalRelevance(v) +
      0.25 × PrerequisiteImportance(v) +
      0.20 × KnowledgeGap(v) +
      0.15 × Uncertainty(v) +
      0.10 × FailureHistory(v)
    """
    mastery = profile.get_mastery(node_id)
    confidence = profile.get_confidence(node_id)
    failure_count = profile.get_failure_count(node_id)
    gap = 1.0 - mastery  # 知识缺口
    uncertainty = 1.0 - confidence  # 不确定性(默认 0.8)

    # FailureHistory: 失败 1 次 = 0.3, 2 次 = 0.6, 3+ = 1.0
    failure_hist = _clamp(float(failure_count) * 0.3)

    priority = (
        0.30 * goal_relevance +
        0.25 * prereq_importance +
        0.20 * gap +
        0.15 * uncertainty +
        0.10 * failure_hist
    )
    return _clamp(priority)


# ── Step 3: 章序 + 拓扑排序 ────────────────────

def _compute_topo_order(
    candidates: list[str],
    edges: list[dict[str, str]] | None = None,
) -> dict[str, int]:
    """用 BFS 计算图谱里候选节点的拓扑深度。

    只考虑候选节点之间的 prerequisite_of 边。
    无前置的节点 depth=0,每依赖一个前置 depth+1。
    如果边不存在(平时),用默认深度 = 0。
    """
    candidate_set = set(candidates)
    edges = edges or _DUMMY_EDGES
    in_degree: dict[str, int] = {}
    prereq_to_dependents: dict[str, list[str]] = defaultdict(list)
    for nid in candidates:
        in_degree.setdefault(nid, 0)
    for edge in edges:
        relation = str(edge.get("relation", "")).strip().lower()
        if relation not in ("", "prerequisite_of"):
            continue
        src = str(edge.get("source", "")).strip()
        tgt = str(edge.get("target", "")).strip()
        if src in candidate_set and tgt in candidate_set:
            prereq_to_dependents[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1
    depth: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for nid in candidates:
        if in_degree.get(nid, 0) == 0:
            queue.append((nid, 0))
            depth[nid] = 0
    while queue:
        nid, d = queue.popleft()
        for dep in prereq_to_dependents.get(nid, []):
            new_d = d + 1
            if dep not in depth or new_d > depth[dep]:
                depth[dep] = new_d
                queue.append((dep, new_d))
    for nid in candidates:
        depth.setdefault(nid, 0)
    return depth


def sort_candidates(
    candidates: list[str],
    edges: list[dict[str, str]] | None = None,
) -> list[str]:
    """拓扑深度 + difficulty 排序。

    排序优先级:
    1. 拓扑深度(浅在先)
    2. 难度(低在先)
    3. ID 数字升序
    """
    topo_depth = _compute_topo_order(candidates, edges)

    def sort_key(node_id: str) -> tuple:
        depth = topo_depth.get(node_id, 0)
        diff = get_node_difficulty(node_id)
        # ID 数字:KM042 → 42
        id_num = 0
        try:
            id_num = int("".join(c for c in node_id if c.isdigit()))
        except ValueError:
            id_num = 9999
        return (depth, diff, id_num)

    return sorted(candidates, key=sort_key)


# ── Step 4: 选 9-12 节点 ───────────────────────

def select_nodes(
    sorted_candidates: list[str],
    profile: StudentProfile,
    node_count: int = 10,
    node_range: tuple[int, int] = (9, 12),
    edges: list[dict[str, str]] | None = None,
) -> list[str]:
    """从候选集中选 9-12 个节点。

    选择策略(知识图谱驱动,非章节):
    1. importance (core → supporting → other)
    2. 拓扑深度(浅在先;能力缺口拉取:同深度内薄弱能力优先)
    3. 紧迫度(越高越先)
    4. 难度(低在先)
    5. ID 数字升序
    """
    if not sorted_candidates:
        return []
    total = len(sorted_candidates)

    # 计算紧迫度
    urgency_scores = {
        nid: compute_urgency(nid, profile)
        for nid in sorted_candidates[:max(node_count * 2, total)]
    }

    # 从知识图谱前置边推导拓扑深度
    topo_depth = _compute_topo_order(sorted_candidates, edges or _DUMMY_EDGES)
    has_real_edges = bool(edges)

    # 评分排序(不再按章节分组)
    if has_real_edges:
        # 计算每能力的平均缺口(用于同深度内排序)
        ability_gaps: dict[str, float] = {}
        for nid2 in sorted_candidates:
            ab2 = get_node_primary_ability(nid2)
            if ab2 and ab2 not in ability_gaps:
                ab_nodes2 = [x for x in sorted_candidates if get_node_primary_ability(x) == ab2]
                if ab_nodes2:
                    g2 = [1.0 - profile.get_mastery(x) for x in ab_nodes2]
                    ability_gaps[ab2] = sum(g2) / len(g2) if g2 else 0.5
                else:
                    ability_gaps[ab2] = 0.5

    scored: list[tuple] = []
    for nid in sorted_candidates[:max(node_count * 2, total)]:
        imp = _IMPORTANCE_ORDER.get(get_node_importance(nid), 2)
        d = float(topo_depth.get(nid, 0))
        urgency = urgency_scores.get(nid, 0.5)
        diff = get_node_difficulty(nid)
        id_num = int("".join(c for c in nid if c.isdigit()) or 0)

        if has_real_edges:
            # 能力缺口拉取:同深度内薄弱能力优先
            ab = get_node_primary_ability(nid)
            gap = ability_gaps.get(ab, 0.5)
            pull = 0.0
            if gap > 0.7:
                pull = 0.5
            elif gap > 0.5:
                pull = 0.25
            adj_depth = max(0.0, d - pull)

            # 真实知识图谱: importance > 深度 > 紧迫度 > 难度 > ID
            scored.append((imp, adj_depth, -urgency, diff, id_num, nid))
        else:
            # 无图(测试环境 fallback): importance > 难度 > ID
            scored.append((imp, diff, id_num, nid))

    scored.sort()
    if has_real_edges:
        selected = [nid for _, _, _, _, _, nid in scored]
    else:
        selected = [nid for _, _, _, nid in scored]

    # 弹性控制范围
    if len(selected) < node_range[0]:
        tail = [n for n in sorted_candidates if n not in selected]
        needed = node_range[0] - len(selected)
        selected.extend(tail[:needed])
    elif len(selected) > node_range[1]:
        selected = selected[:node_range[1]]

    return selected


# ── Step 5: 聚类成 4 step ──────────────────────

def cluster_into_steps(
    selected: list[str],
    n_steps: int = 4,
    per_step_range: tuple[int, int] = (2, 4),
) -> list[list[str]]:
    """将选中的节点聚类成 4 step。

    规则（V2 能力驱动聚类）:
    1. 按 primary_ability 分组——同能力维度的节点尽量在一起
    2. 跨章节自然允许——同一能力可能跨越多个章节
    3. 组内按章序 + ID 保持拓扑序（不打破前置依赖）
    4. 每 step 节点数 ∈ [2, 4]
    5. 最终 step 数 = n_steps(有弹性)
    """
    if not selected:
        return []

    min_n, max_n = per_step_range

    # ── 1. 按 primary_ability 分组 ──
    ability_groups: dict[str, list[str]] = defaultdict(list)
    for nid in selected:
        ab = get_node_primary_ability(nid)
        ability_groups[ab].append(nid)

    # 组内按章序 + ID 排序（保持拓扑依赖顺序）
    for ab in ability_groups:
        ability_groups[ab].sort(key=lambda nid: (
            _get_chapter_order(nid),
            int("".join(c for c in nid if c.isdigit()) or 0),
        ))

    # ability 间按最小章序排列
    sorted_abilities = sorted(
        ability_groups.keys(),
        key=lambda ab: min(
            (_get_chapter_order(nid) for nid in ability_groups[ab]),
            default=999,
        ),
    )

    # ── 2. 将 ability 组拆成 step（均匀分配，避免 4+2 式的不均衡）──
    raw_steps: list[list[str]] = []
    for ab in sorted_abilities:
        nodes = ability_groups[ab]
        total = len(nodes)
        if total <= max_n:
            raw_steps.append(list(nodes))
            continue
        # 计算合理的切分数：ceil(total / max_n)，使每 chunk 在 [min_n, max_n] 内
        n_chunks = max(1, (total + max_n - 1) // max_n)
        # 如果每块少于 min_n，减少块数
        while n_chunks > 1 and total // n_chunks < min_n:
            n_chunks -= 1
        base_size = total // n_chunks
        extra = total % n_chunks
        start = 0
        for i in range(n_chunks):
            size = base_size + (1 if i < extra else 0)
            raw_steps.append(nodes[start:start + size])
            start += size

    # ── 4. 调整 step 数到 target ──
    target = n_steps
    while len(raw_steps) > target:
        # 合并最相邻的 2 个 step
        best_idx = -1
        best_sum = max_n + 1
        for i in range(len(raw_steps) - 1):
            merged_len = len(raw_steps[i]) + len(raw_steps[i + 1])
            if merged_len <= max_n and merged_len < best_sum:
                best_sum = merged_len
                best_idx = i
        if best_idx >= 0:
            raw_steps[best_idx].extend(raw_steps[best_idx + 1])
            del raw_steps[best_idx + 1]
        else:
            # 不能合法合并了，强制合并最小一个
            if len(raw_steps) >= 2:
                smallest = min(range(len(raw_steps)), key=lambda i: len(raw_steps[i]))
                if smallest > 0:
                    raw_steps[smallest - 1].extend(raw_steps[smallest])
                else:
                    raw_steps[smallest].extend(raw_steps[smallest + 1])
                del raw_steps[smallest if smallest > 0 else smallest + 1]
            else:
                break

    while len(raw_steps) < target and len(raw_steps) > 0:
        # 拆分最大 step
        largest_idx = max(range(len(raw_steps)), key=lambda i: len(raw_steps[i]))
        largest = raw_steps[largest_idx]
        if len(largest) >= 3:
            mid = len(largest) // 2
            raw_steps[largest_idx] = largest[:mid]
            raw_steps.insert(largest_idx + 1, largest[mid:])
        else:
            break

    return raw_steps


# ── Step 6: entry_mode 决策 ────────────────────

def resolve_entry_modes(
    node_ids: list[str],
    profile: StudentProfile,
) -> dict[str, str]:
    """决策一个 step 中每节点的 entry_mode。"""
    return {
        nid: profile.get_entry_mode(nid)
        for nid in node_ids
    }


# ── Step 7: step 命名 ──────────────────────────

_STEP_NAME_MAX_LEN = 12
_STEP_NAME_MIN_LEN = 4


def _rule_based_step_names(raw_steps: list[list[str]]) -> list[str]:
    """规则兜底:step 名称 = 第一个节点的名称(截断到 12 字)。

    仅在 LLM 命名不可用(失败/未提供)时使用。
    """
    name_map = get_node_name_map()
    names: list[str] = []
    for idx, node_ids in enumerate(raw_steps):
        name = name_map.get(node_ids[0], node_ids[0]) if node_ids else ""
        if len(name) > _STEP_NAME_MAX_LEN:
            name = name[:_STEP_NAME_MAX_LEN - 1] + "…"
        if name:
            names.append(name)
        else:
            names.append(f"第{idx + 1}步")
    return names


def _sanitize_llm_name(name: str) -> str:
    """清理 LLM 返回的名字:strip、去掉引号/JSON 噪声、限长。"""
    if not name:
        return ""
    name = str(name).strip()
    # 去掉常见 LLM 噪声:引号、书名号、JSON 包装
    for ch in ['"', "'", "`", "「", "」", "《", "》", "【", "】"]:
        name = name.replace(ch, "")
    name = name.strip()
    if not name:
        return ""
    if len(name) > _STEP_NAME_MAX_LEN:
        name = name[:_STEP_NAME_MAX_LEN - 1] + "…"
    return name


def _parse_llm_step_names(raw: str, expected_count: int) -> list[str] | None:
    """解析 LLM 返回的 step 名字 JSON 数组。

    兼容:
    - 纯 JSON 数组: ["a","b","c","d"]
    - JSON 嵌入在文本中(取第一个 [...] 块)
    - 行号前缀("1. xxx")
    - 退路:按行切,取前 N 行非空
    """
    import json
    import re

    text = (raw or "").strip()
    if not text:
        return None

    # 1) 尝试找 [...] JSON 块
    match = re.search(r"\[[^\[\]]*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list) and len(parsed) >= expected_count:
                cleaned = [_sanitize_llm_name(str(x)) for x in parsed[:expected_count]]
                if all(cleaned):
                    return cleaned
        except (json.JSONDecodeError, ValueError):
            pass

    # 2) 退路:按行切,去掉 "1." "1、" 等行号前缀
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned_lines: list[str] = []
    for ln in lines:
        # 去行号前缀
        ln2 = re.sub(r"^\s*\d+[\.\、\:]\s*", "", ln)
        ln2 = re.sub(r"^\s*[\-\*]\s*", "", ln2)
        cleaned = _sanitize_llm_name(ln2)
        if cleaned and len(cleaned) >= _STEP_NAME_MIN_LEN:
            cleaned_lines.append(cleaned)
    if len(cleaned_lines) >= expected_count:
        return cleaned_lines[:expected_count]

    return None


def _build_step_naming_prompt(raw_steps: list[list[str]]) -> str:
    """构造 LLM prompt,请求为每个 step 生成 4-12 字的主题名。"""
    name_map = get_node_name_map()
    ability_map = get_node_name_map()  # node name fallback
    try:
        from .ability_mapper import get_ability_names
        ability_codes = get_ability_names()
    except Exception:
        ability_codes = {}

    lines: list[str] = []
    lines.append(
        "你是「自动控制原理」教学助手。请为下面的每个学习步骤(step)生成一个简洁、有学习引导感的中文主题名。\n"
    )
    lines.append("严格要求:")
    lines.append(f"- 每个名字 4-{_STEP_NAME_MAX_LEN} 个中文字符(避免太长或太短)")
    lines.append("- 名字要覆盖该 step 多个节点的核心主题,而非只取第一个节点名")
    lines.append("- 用动词/名词短语,如「建立自动控制基础」「掌握数学建模」「攻克时域分析」")
    lines.append("- 多个 step 名字之间要有明显区分(不要重复主题词)")
    lines.append(f"- 共 {len(raw_steps)} 步,直接返回 JSON 数组,不要任何额外说明\n")

    for idx, node_ids in enumerate(raw_steps):
        lines.append(f"Step {idx + 1} 包含以下 {len(node_ids)} 个节点:")
        for nid in node_ids:
            nname = name_map.get(nid, nid)
            try:
                ab = get_node_primary_ability(nid)
                ab_label = ability_codes.get(ab, ab)
            except Exception:
                ab_label = ""
            if ab_label:
                lines.append(f"  - {nid} {nname} (主能力:{ab_label})")
            else:
                lines.append(f"  - {nid} {nname}")
        lines.append("")

    lines.append(
        f"请返回 JSON 数组(共 {len(raw_steps)} 项,顺序与上面 step 对应):\n"
        "[\"Step1名\", \"Step2名\", ...]"
    )
    return "\n".join(lines)


def _call_llm_for_text(llm: Any, prompt: str) -> str | None:
    """用多种接口适配 LLM 对象(ChatOpenAI / AnswerProvider 等)。

    优先顺序:
    1. .predict(text) — LangChain ChatOpenAI 单文本输入
    2. .get_answer(prompt) — 项目自定义 AnswerProvider(测试 mock)
    3. .invoke([HumanMessage(prompt)]) — LangChain 标准消息接口

    Returns: LLM 返回文本,失败返回 None
    """
    # 1) predict (ChatOpenAI)
    predict = getattr(llm, "predict", None)
    if callable(predict):
        try:
            result = predict(prompt)
            return str(result) if result else None
        except Exception:
            pass

    # 2) get_answer (AnswerProvider, 测试用)
    get_answer = getattr(llm, "get_answer", None)
    if callable(get_answer):
        try:
            result = get_answer(prompt)
            return str(result) if result else None
        except Exception:
            pass

    # 3) invoke with messages (LangChain 标准)
    invoke = getattr(llm, "invoke", None)
    if callable(invoke):
        try:
            from langchain_core.messages import HumanMessage
            result = invoke([HumanMessage(content=prompt)])
            if hasattr(result, "content"):
                return str(result.content)
            return str(result) if result else None
        except Exception:
            pass

    return None


def generate_step_names_with_llm(
    raw_steps: list[list[str]],
    llm: Any | None,
) -> list[str]:
    """用 LLM 生成 step 名字;LLM 不可用或失败时降级到规则。

    Args:
        raw_steps: 每 step 的节点 ID 列表
        llm: ChatOpenAI / AnswerProvider 实例(或 None/不可用 → 规则)

    Returns:
        与 raw_steps 等长的名字列表
    """
    fallback = _rule_based_step_names(raw_steps)
    if not raw_steps or llm is None:
        return fallback

    prompt = _build_step_naming_prompt(raw_steps)
    try:
        raw_response = _call_llm_for_text(llm, prompt)
    except Exception:
        return fallback

    if not raw_response:
        return fallback

    parsed = _parse_llm_step_names(raw_response, len(raw_steps))
    if parsed is None:
        return fallback
    return parsed


def generate_step_names(
    raw_steps: list[list[str]],
    llm: Any | None = None,
) -> list[str]:
    """根据每个 step 的节点信息,生成有区分度的 step 名称。

    默认使用 LLM 命名(更自然、跨节点抽象);llm=None 或 LLM
    失败时降级到规则(取第一个节点名 + 截断)。

    Args:
        raw_steps: 每 step 的节点 ID 列表
        llm: AnswerProvider 实例(可选)

    Returns:
        与 raw_steps 等长的名字列表
    """
    if llm is not None:
        return generate_step_names_with_llm(raw_steps, llm)
    return _rule_based_step_names(raw_steps)


# ── 主入口 ──────────────────────────────────────

def generate_learning_plan_v2(
    profile: StudentProfile,
    edges: list[dict[str, str]] | None = None,
    previous_plan: LearningPlan | None = None,
    goal: str = "complete",
    n_steps: int = 4,
    node_count_target: int = 10,
    node_range: tuple[int, int] = (9, 12),
    session_index: int = 0,
    llm: Any | None = None,
) -> LearningPlan:
    """主入口:根据学生画像 + 图谱 + 历史路径,生成一次学习路径。

    逻辑:
    1. 如果 previous_plan 存在且有 in_progress step → 续上(resume)
       (resume 不重新生成 step 名字,保留已有名字)
    2. 否则生成新 plan(cold_start / replan),可用 llm 生成 step 名字

    Args:
        profile: 学生画像
        edges: 图谱前置边
        previous_plan: 上次的路径(用于续上)
        goal: 学习目标(complete / module / review / weakness)
        n_steps: 目标 step 数
        node_count_target: 目标节点数
        node_range: 允许的节点数范围
        session_index: 第几次 session
        llm: 可选 AnswerProvider,用于 LLM 生成 step 名字

    Returns:
        LearningPlan
    """
    # ── 续上逻辑 ──
    if previous_plan and previous_plan.resolve_status() == "in_progress":
        # 直接续上:只更新 entry_mode(可能有新失败)
        _refresh_previous_plan(previous_plan, profile)
        previous_plan.source = "resume"
        return previous_plan

    # ── 新生成 ──
    all_node_ids = get_all_node_ids()
    mastered = profile.get_mastered_concept_ids()

    # Step 1: 候选集
    candidates = compute_candidates(all_node_ids, mastered)

    # 如果候选不足 → 从已 mastered 补充 weakest 填到 range 下限
    if len(candidates) < node_range[0]:
        needed = node_range[0] - len(candidates)
        mastered_list = list(mastered)
        mastered_list.sort(key=lambda nid: profile.get_mastery(nid))
        candidates.extend(mastered_list[:needed])

    # Step 2-3: 排序
    sorted_candidates = sort_candidates(candidates, edges)

    # Step 4: 选 9-12 节点(知识图谱驱动,传递 edges 推导深度)
    selected = select_nodes(sorted_candidates, profile, node_count_target, node_range, edges=edges)

    # Step 5: 聚类成 step
    raw_steps = cluster_into_steps(selected, n_steps=n_steps)

    # Step 6: entry_mode
    steps: list[StepEntry] = []
    step_names = generate_step_names(raw_steps, llm=llm)

    # 计算每 step 的 ability
    for idx, node_ids in enumerate(raw_steps):
        step_abilities = {
            get_node_primary_ability(nid) for nid in node_ids if get_node_primary_ability(nid)
        }
        step_ability = next(iter(step_abilities)) if step_abilities else ""
        chs = sorted({_get_node_chapter(nid) for nid in node_ids},
                     key=lambda c: _CHAPTER_ORDER.get(c, 999))
        chapter = chs[0] if chs else ""

        # 计算 reason
        low_mastery = sum(1 for nid in node_ids if profile.get_mastery(nid) < 0.4)
        failed = sum(1 for nid in node_ids if profile.get_failure_count(nid) >= 1)
        if failed >= 2:
            reason = f"含 {failed} 个需要重学的节点,基于错题驱动"
        elif low_mastery >= 2:
            reason = f"含 {low_mastery} 个薄弱节点,需要完整学习"
        else:
            reason = "基于当前画像与递进逻辑的推荐"
        if step_ability:
            ability_map = {"A": "数学基础", "B": "基本概念", "C": "建模", "D": "稳定性",
                           "E": "时域", "F": "稳态误差", "G": "根轨迹", "H": "频域校正"}
            step_goal = f"掌握{ability_map.get(step_ability, step_ability)}核心能力"

        entry_modes = resolve_entry_modes(node_ids, profile)
        step = StepEntry(
            step_index=idx,
            step_name=step_names[idx] if idx < len(step_names) else f"第{idx + 1}步",
            step_goal=step_goal or "",
            step_ability=step_ability,
            chapter=chapter,
            node_ids=node_ids,
            entry_modes=entry_modes,
            reason=reason,
            status="in_progress" if idx == 0 else "pending",
        )
        steps.append(step)

    plan = LearningPlan(
        steps=steps,
        total_nodes=sum(len(s.node_ids) for s in steps),
        total_steps=len(steps),
        generated_at=_now_iso(),
        source="replan" if session_index > 0 else "cold_start",
        session_index=session_index,
    )
    return plan


def _step_name_looks_rule_based(step: StepEntry) -> bool:
    """判断 step_name 是否由老规则生成(等于首节点名或"第N步"兜底)。

    用于检测需要 LLM 重命名的旧 plan。规则:
    - 空名 → 需要重命名
    - "第N步"格式 → 规则兜底,需要重命名
    - 等于该 step 第一个节点的名称 → 规则生成,需要重命名
    - 其他 → 保留(可能是 LLM 生成或人工标注)
    """
    if not step.step_name:
        return True
    import re
    if re.match(r"^第\d+步$", step.step_name):
        return True
    if step.node_ids:
        first_name = get_node_name_map().get(step.node_ids[0], "")
        if first_name and step.step_name == first_name:
            return True
    return False


def _refresh_previous_plan(
    plan: LearningPlan,
    profile: StudentProfile,
    llm: Any | None = None,
) -> None:
    """续上逻辑:更新已有 plan 的 entry_mode;必要时重命名。

    重命名触发条件(满足任一):
    - step_name 为空
    - step_name 是"第N步"兜底
    - step_name 等于该 step 第一个节点名(老规则生成特征)

    重命名方式:
    - llm 可用且所有需要重命名的 step 同属一个 raw_steps 列表
      → 一次 LLM 调用批量重命名(避免多次 LLM 往返)
    - 否则 → 单个 step 用规则兜底
    """
    needs_rename_idx = [i for i, s in enumerate(plan.steps) if _step_name_looks_rule_based(s)]
    if not needs_rename_idx:
        return

    # 收集需要重命名的 raw_steps
    raw_steps_to_rename = [plan.steps[i].node_ids for i in needs_rename_idx]
    new_names = generate_step_names(raw_steps_to_rename, llm=llm)

    for idx, new_name in zip(needs_rename_idx, new_names):
        if new_name:
            plan.steps[idx].step_name = new_name

    for step in plan.steps:
        step.entry_modes = resolve_entry_modes(step.node_ids, profile)
        # 如果有节点是新失败(failure_count 在之前路径里增加的),改状态
        has_failed = any(
            profile.get_failure_count(nid) >= 1 for nid in step.node_ids
        )
        if has_failed and step.status != "completed":
            step.reason = "续上 + 错题驱动(上次留了错题)"

    # 如果路径全完成但还有 massive failed 节点 → 下次触发 replan
    all_completed = all(s.status == "completed" for s in plan.steps)
    total_failed = sum(
        profile.get_failure_count(nid) for step in plan.steps for nid in step.node_ids
    )
    if all_completed and total_failed > 0:
        plan.source = "replan_after_completion"


# ── 快速创建(给测试用) ────────────────────────

def make_plan_for_profile(
    profile: StudentProfile,
    edges: list[dict[str, str]] | None = None,
    session_index: int = 0,
) -> LearningPlan:
    """快速创建路径(跳过续上逻辑,直接生成)。"""
    return generate_learning_plan_v2(
        profile=profile,
        edges=edges,
        previous_plan=None,
        session_index=session_index,
    )


def simulate_multi_session(
    profile: StudentProfile,
    edges: list[dict[str, str]] | None = None,
    n_sessions: int = 4,
) -> list[LearningPlan]:
    """模拟多次路径生成(每次更新画像后重新生成)。

    用于测试 / 演示:每次学完后更新 mastery,触发下次生成。
    """
    plans: list[LearningPlan] = []
    current_profile = profile

    for i in range(n_sessions):
        # 生成路径
        plan = make_plan_for_profile(current_profile, edges, session_index=i)
        plans.append(plan)

        # 模拟"路径完成"——标记所有节点 mastered,但保留 failure
        for step in plan.steps:
            for nid in step.node_ids:
                mode = step.entry_modes.get(nid, "full_learning")
                if mode == "quick_check":
                    current_profile.mark_mastered(nid)
                elif mode == "short_learning":
                    current_profile.mark_mastered(nid)
                else:
                    current_profile.mark_mastered(nid)

        # 如果所有节点都 mastered → 停
        if current_profile.get_mastered_concept_ids() == set(get_all_node_ids()):
            break

    return plans
