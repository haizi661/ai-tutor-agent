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
    """章序 + 拓扑序 + difficulty 排序。

    排序优先级:
    1. 章序(第一优先级,跨章不递减)
    2. 拓扑深度(浅在先)
    3. 难度(低在先)
    4. ID 数字升序
    """
    topo_depth = _compute_topo_order(candidates, edges)

    def sort_key(node_id: str) -> tuple:
        ch_order = _get_chapter_order(node_id)
        depth = topo_depth.get(node_id, 0)
        diff = get_node_difficulty(node_id)
        # ID 数字:KM042 → 42
        id_num = 0
        try:
            id_num = int("".join(c for c in node_id if c.isdigit()))
        except ValueError:
            id_num = 9999
        return (ch_order, depth, diff, id_num)

    return sorted(candidates, key=sort_key)


# ── Step 4: 选 9-12 节点 ───────────────────────

def select_nodes(
    sorted_candidates: list[str],
    profile: StudentProfile,
    node_count: int = 10,
    node_range: tuple[int, int] = (9, 12),
) -> list[str]:
    """从已排序候选集中选 9-12 个节点。

    优先前部(章序小 + 拓扑浅),同时看紧迫度高的先选。
    """
    if not sorted_candidates:
        return []
    total = len(sorted_candidates)

    # 计算紧迫度作为辅助排序
    urgency_scores = {
        nid: compute_urgency(nid, profile)
        for nid in sorted_candidates[:max(node_count * 2, total)]
    }

    # 在已排序基础上,按"紧迫度降序"重排
    # 但保留章序约束:同章内按紧迫度降
    chapter_groups: dict[str, list[str]] = defaultdict(list)
    for nid in sorted_candidates:
        ch = _get_node_chapter(nid)
        chapter_groups[ch].append(nid)
    reordered: list[str] = []
    for ch in sorted(chapter_groups.keys(), key=lambda c: _CHAPTER_ORDER.get(c, 999)):
        group = chapter_groups[ch]
        # 同章内按紧迫度降序
        group.sort(key=lambda nid: -urgency_scores.get(nid, 0.5))
        reordered.extend(group)

    # 选前 node_count 个,弹性控制在 node_range 内
    selected = reordered[:node_count]

    # 补/截断到 range
    if len(selected) < node_range[0]:
        # 补:从 reordered 剩余头部补
        tail = [n for n in reordered if n not in selected]
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

def generate_step_names(
    raw_steps: list[list[str]],
) -> list[str]:
    """根据每个 step 的节点信息,生成有区分度的 step 名称。

    规则:
    - step 名称 = 第一个节点的名称(代表该 step 的核心内容主题)
    - 不暴露章节、图谱 ID 等内部实现细节
    - 若名称过长(>12 字)则截断并加"…"
    - 纯 fallback → "第 N 步"

    理由:step 可能跨章节或重组,用节点名作为 step 名让用户
    直觉地知道该 step 学什么,且不受图谱结构变化影响。
    """
    name_map = get_node_name_map()

    names: list[str] = []
    for idx, node_ids in enumerate(raw_steps):
        name = name_map.get(node_ids[0], node_ids[0]) if node_ids else ""
        if len(name) > 12:
            name = name[:11] + "…"
        if name:
            names.append(name)
        else:
            names.append(f"第{idx + 1}步")
    return names


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
) -> LearningPlan:
    """主入口:根据学生画像 + 图谱 + 历史路径,生成一次学习路径。

    逻辑:
    1. 如果 previous_plan 存在且有 in_progress step → 续上(resume)
    2. 否则生成新 plan(cold_start / replan)

    Args:
        profile: 学生画像
        edges: 图谱前置边
        previous_plan: 上次的路径(用于续上)
        goal: 学习目标(complete / module / review / weakness)
        n_steps: 目标 step 数
        node_count_target: 目标节点数
        node_range: 允许的节点数范围
        session_index: 第几次 session

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

    # 如果候选太少(< 6) → 从已 mastered 补充 weakest
    if len(candidates) < 6:
        # 找已 mastered 中 mastery 最低的
        mastered_list = list(mastered)
        mastered_list.sort(key=lambda nid: profile.get_mastery(nid))
        candidates.extend(mastered_list[:6])

    # Step 2-3: 排序
    sorted_candidates = sort_candidates(candidates, edges)

    # Step 4: 选 9-12 节点
    selected = select_nodes(sorted_candidates, profile, node_count_target, node_range)

    # Step 5: 聚类成 step
    raw_steps = cluster_into_steps(selected, n_steps=n_steps)

    # Step 6: entry_mode
    steps: list[StepEntry] = []
    step_names = generate_step_names(raw_steps)

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


def _refresh_previous_plan(plan: LearningPlan, profile: StudentProfile) -> None:
    """续上逻辑:更新已有 plan 的 entry_mode 与 step 名称(基于新画像与新命名逻辑)。"""
    # 刷新 step 名称(内容驱动,可能随代码更新而变化)
    raw_steps = [step.node_ids for step in plan.steps if step.node_ids]
    if raw_steps:
        new_names = generate_step_names(raw_steps)
        for step, new_name in zip(plan.steps, new_names):
            step.step_name = new_name

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
