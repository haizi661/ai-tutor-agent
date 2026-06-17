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
    get_node_chapter_map,
    get_node_difficulty,
    get_node_estimated_time,
    get_node_importance,
    get_node_name_map,
    get_node_primary_ability,
    get_ability_names,
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


_DUMMY_EDGES: list[dict] = []

# 节点重要性排序权重(core 优先于 supporting)
_IMPORTANCE_ORDER: dict[str, int] = {"core": 0, "supporting": 1, "other": 2}

# ── 章节映射(从 V2 JSON 动态加载,不再硬编码) ──
_NODE_CHAPTER: dict[str, str] = {}
_CHAPTER_ORDER: dict[str, int] = {}


_CN_NUM = "一二三四五六七八九十"

def _chapter_sort_key(chapter: str) -> int:
    """从章节名中提取数值序号(如 '第三章' → 3, '第五、六章' → 5)。"""
    for idx, ch in enumerate(chapter, start=1):
        if ch in _CN_NUM:
            return _CN_NUM.index(ch) + 1
    return 999


def _ensure_chapter_loaded() -> None:
    global _NODE_CHAPTER, _CHAPTER_ORDER
    if _NODE_CHAPTER:
        return
    _NODE_CHAPTER = get_node_chapter_map()
    chapters = sorted(set(c for c in _NODE_CHAPTER.values() if c), key=_chapter_sort_key)
    _CHAPTER_ORDER = {c: idx for idx, c in enumerate(chapters)}


def _get_node_chapter(node_id: str) -> str:
    _ensure_chapter_loaded()
    return _NODE_CHAPTER.get(node_id, "其他")


def _get_chapter_order(node_id: str) -> int:
    _ensure_chapter_loaded()
    ch = _NODE_CHAPTER.get(node_id, "其他")
    return _CHAPTER_ORDER.get(ch, 999)


# ── 工具函数 ───────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


# ── 算法 7 步 ──────────────────────────────────────

# ── Step 1: 候选集 ────────────────────────────

def compute_candidates(
    all_node_ids: list[str] | None = None,
    mastered_set: set[str] | None = None,
    include_all: bool = False,
) -> list[str]:
    """候选集 = 全图谱 - 已 mastered

    已 mastered 的定义:
    - mastery >= 0.85 AND confidence >= 0.7(即 profile.is_mastered)

    include_all=True 时忽略 mastered 状态，返回全部节点（用于完整轮次复习）。
    """
    if all_node_ids is None:
        all_node_ids = get_all_node_ids()
    if include_all:
        return list(all_node_ids)
    mastered = mastered_set or set()
    return [nid for nid in all_node_ids if nid not in mastered]


# ── Step 2: 紧迫度计算 ─────────────────────────

def compute_context_boost(
    wrong_question_book: list[dict[str, Any]] | None = None,
    question_help_records: list[dict[str, Any]] | None = None,
) -> dict[str, float]:
    """从错题本和临时提问中计算每节点的上下文紧迫加成。

    - 错题本: 每道未掌握的错题 +0.12，有 misconception/wrong_reason 的额外 +0.08
    - 临时提问: 每个围绕该节点的提问 +0.08（反映用户主动关注）
    - 每节点上限 1.0
    """
    from collections import defaultdict

    boost: dict[str, float] = defaultdict(float)
    # 错题本
    for entry in (wrong_question_book or []):
        nid = str(entry.get("node_id", "")).strip()
        if not nid:
            continue
        if entry.get("mastered"):
            continue
        boost[nid] += 0.12
        if entry.get("misconception") or entry.get("wrong_reason"):
            boost[nid] += 0.08

    # 临时提问：用户在某个节点上主动求助，说明关注/困惑
    for record in (question_help_records or []):
        nid = str(record.get("node_id", "")).strip()
        if not nid:
            continue
        boost[nid] += 0.08

    return {nid: min(1.0, v) for nid, v in boost.items()}


def compute_freshness_boost(
    candidates: list[str],
    previously_planned: set[str] | None = None,
    session_index: int = 0,
) -> dict[str, float]:
    """为从未被任何学习路径选中的节点提供新鲜度加成。

    防止尾部节点因确定性排序被反复跳过的覆盖缺口。
    加成值随 session 递增，确保不同 importance 层级的节点最终都能被覆盖：
    - session 0-1: 0.25（同 importance 内优先）
    - session 2-3: 0.40（跨 supporting 壁垒）
    - session 4+:  0.55（跨 optional 壁垒）

    经 context_boost 20% 权重折算后分别为 0.05/0.08/0.11 urgency。
    """
    if not previously_planned:
        return {}
    if session_index <= 1:
        value = 0.25
    elif session_index <= 3:
        value = 0.40
    else:
        value = 0.55
    return {nid: value for nid in candidates if nid not in previously_planned}


def compute_urgency(
    node_id: str,
    profile: StudentProfile,
    context_boost: float = 0.0,
) -> float:
    """紧迫度公式:值越大越应该优先选。

    Priority(v) =
      0.35 × KnowledgeGap(v) +
      0.15 × Uncertainty(v) +
      0.30 × FailureHistory(v) +
      0.20 × ContextBoost(v)

    Gap = 1 - mastery, Uncertainty = 1 - confidence。
    FailureHistory: 失败 1 次=0.3, 2 次=0.6, 3+=1.0。
    ContextBoost: 来自错题本和临时提问的预计算加成（0-1）。

    权重设计原因: failure_hist 权重高于 uncertainty,因为确凿的失败
    证据比"未测试所以不确定"更应该驱动优先级。
    """
    mastery = profile.get_mastery(node_id)
    confidence = profile.get_confidence(node_id)
    failure_count = profile.get_failure_count(node_id)
    gap = 1.0 - mastery
    uncertainty = 1.0 - confidence
    failure_hist = _clamp(float(failure_count) * 0.3)

    priority = (
        0.35 * gap +
        0.15 * uncertainty +
        0.30 * failure_hist +
        0.20 * _clamp(context_boost)
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
    context_boost: dict[str, float] | None = None,
    assessment_node_ids: set[str] | None = None,
) -> list[str]:
    """从候选集中选 9-12 个节点。

    选择策略(画像驱动加权评分):
    使用加权复合评分代替严格层级排序,让画像差异能真正影响节点选择。
    权重设计:
    - urgency(60%): 画像驱动的紧迫度,含 mastery gap + confidence + 错题/提问加成
    - importance(15%): core > supporting > other
    - depth(5%): 拓扑深度,浅层优先
    - difficulty(5%): 难度,简单优先
    - id tiebreaker(15%): 稳定 ID 排序

    关键改进: urgency 权重从三级键提升到主导因子,
    不同画像下相同 importance/depth 的节点会产生不同的选择结果。

    assessment_node_ids: 经测评校准匹配到的节点 ID 集,这些节点获得
    额外复合分加成以确保它们进入学习路径(以 quick_check/short_learning 模式)。
    """
    if not sorted_candidates:
        return []
    total = len(sorted_candidates)

    boost_map = context_boost or {}
    # 计算紧迫度
    urgency_scores = {
        nid: compute_urgency(nid, profile, boost_map.get(nid, 0.0))
        for nid in sorted_candidates[:max(node_count * 2, total)]
    }

    # 从知识图谱前置边推导拓扑深度
    topo_depth = _compute_topo_order(sorted_candidates, edges or _DUMMY_EDGES)

    # ── 加权复合评分(画像驱动) ──
    _IMP_SCORE: dict[str, float] = {"core": 1.0, "supporting": 0.55, "other": 0.1}

    scored: list[tuple] = []
    for nid in sorted_candidates[:max(node_count * 2, total)]:
        importance = get_node_importance(nid)
        imp_base = _IMP_SCORE.get(importance, 0.1)
        d = float(topo_depth.get(nid, 0))
        urgency = urgency_scores.get(nid, 0.5)
        diff = get_node_difficulty(nid)
        id_num = int("".join(c for c in nid if c.isdigit()) or 0)

        # depth_score: shallower → higher score (0→1.0, 5+→0.0)
        depth_score = max(0.0, 1.0 - d / 5.0)
        # diff_score: easier → higher score (1→1.0, 5→0.0)
        diff_score = 1.0 - (diff - 1) / 4.0
        # id_score: tiny tiebreaker
        id_score = 1.0 / (id_num + 20)

        # assessment 测评校准节点获得额外加成，确保这些自评已掌握
        # 但可能需要验证的知识点进入学习路径（以 quick_check 模式呈现）
        assessment_bonus = 0.25 if (assessment_node_ids and nid in assessment_node_ids) else 0.0

        composite = (
            0.15 * imp_base +
            0.05 * depth_score +
            0.60 * urgency +
            0.05 * diff_score +
            0.15 * id_score +
            assessment_bonus
        )
        # 负数使高 composite 排前面
        scored.append((-composite, id_num, nid))

    scored.sort()
    selected = [nid for _, _, nid in scored]

    # 弹性控制范围
    if len(selected) < node_range[0]:
        tail = [n for n in sorted_candidates if n not in selected]
        needed = node_range[0] - len(selected)
        selected.extend(tail[:needed])
    elif len(selected) > node_range[1]:
        selected = selected[:node_range[1]]

    # ── 新鲜度保留：确保从未被规划过的节点至少占 1-2 个名额 ──
    fresh_set = {nid for nid, boost in boost_map.items() if boost >= 0.40}
    fresh_unselected = [nid for nid in fresh_set if nid in sorted_candidates and nid not in selected]
    if fresh_unselected and len(selected) >= node_range[0]:
        # 按 urgency 排序 fresh 候选
        fresh_unselected.sort(key=lambda nid: -urgency_scores.get(nid, 0.0))
        reserve_count = min(2, len(fresh_unselected))
        # 从 selected 末尾替换（去掉 urgency 最低且非 fresh 的节点）
        for i in range(reserve_count):
            # 找一个可替换的非 fresh 节点（从后往前找）
            swap_idx = -1
            for j in range(len(selected) - 1, -1, -1):
                if selected[j] not in fresh_set:
                    swap_idx = j
                    break
            if swap_idx >= 0 and i < len(fresh_unselected):
                selected[swap_idx] = fresh_unselected[i]

    return selected


def _sort_step_nodes(
    node_ids: list[str],
    edges: list[dict[str, str]] | None = None,
) -> list[str]:
    """对 step 内节点排序：拓扑深度(前置先学) → 难度(易先) → ID。

    确保教学顺序合理：先学前置知识，同深度内从简单到难。
    """
    if len(node_ids) <= 1:
        return list(node_ids)
    topo_depth = _compute_topo_order(node_ids, edges)
    return sorted(node_ids, key=lambda nid: (
        topo_depth.get(nid, 0),
        get_node_difficulty(nid),
        int("".join(c for c in nid if c.isdigit()) or 0),
    ))


# ── Step 5: 聚类成 4 step ──────────────────────

def cluster_into_steps(
    selected: list[str],
    n_steps: int = 4,
    per_step_range: tuple[int, int] = (2, 4),
    edges: list[dict[str, str]] | None = None,
) -> list[list[str]]:
    """将选中的节点聚类成 4 step。

    规则（V2 能力驱动聚类）:
    1. 按 primary_ability 分组——同能力维度的节点尽量在一起
    2. 跨章节自然允许——同一能力可能跨越多个章节
    3. step 内按拓扑深度(前置先学) → 难度(易→难) → ID 排序
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

    # ── step 内排序：拓扑深度 → 难度 → ID ──
    raw_steps = [_sort_step_nodes(step, edges) for step in raw_steps]

    return raw_steps


# ── Step 6: entry_mode 决策 ────────────────────

def resolve_entry_modes(
    node_ids: list[str],
    profile: StudentProfile,
    force_review: bool = False,
) -> dict[str, str]:
    """决策一个 step 中每节点的 entry_mode。

    传入节点元数据（difficulty / importance），让 entry_mode
    能按节点属性差异化——辅助/简单节点可以精简学，核心/难节点必须完整学。

    force_review=True 时（全部 mastered 后的巩固复习），将掌握度最低的
    节点从 quick_check 升级为 short_learning，确保有实际复习内容而非仅 2 道检测题。
    """
    modes = {
        nid: profile.get_entry_mode(
            nid,
            node_difficulty=get_node_difficulty(nid),
            node_importance=get_node_importance(nid),
        )
        for nid in node_ids
    }
    if force_review:
        # 找出所有 quick_check 节点，按 mastery 升序，最低的一半升级为 short_learning
        qc_nodes = sorted(
            [nid for nid, m in modes.items() if m == "quick_check"],
            key=lambda nid: profile.get_mastery(nid),
        )
        upgrade_count = max(1, len(qc_nodes) // 2)  # 至少升级 1 个
        for nid in qc_nodes[:upgrade_count]:
            modes[nid] = "short_learning"
    return modes


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
    per_step_range: tuple[int, int] = (2, 4),
    session_index: int = 0,
    llm: Any | None = None,
    context_boost: dict[str, float] | None = None,
    freshness_boost: dict[str, float] | None = None,
    force_review: bool = False,
    include_all: bool = False,
    assessment_node_ids: set[str] | None = None,
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
        context_boost: node_id → 上下文紧迫加成(错题本+临时提问)
        freshness_boost: node_id → 新鲜度加成(从未被规划过的节点)
        force_review: 全部 mastered 后仍强制从薄弱节点生成复习路径
        include_all: 候选集包含全部节点（不排除已 mastered），用于完整轮次复习

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
    candidates = compute_candidates(all_node_ids, mastered, include_all=include_all)

    # 如果候选不足 → 从已 mastered 补充 weakest 填到 range 下限
    # 候选为 0 时：若是强制复习模式（consolidate_weak）则补充，否则交由上层触发 completion
    # include_all 模式下候选集已包含全部节点，不需要补充
    if not include_all and len(candidates) < node_range[0]:
        if len(candidates) > 0 or force_review:
            needed = node_range[0] - len(candidates)
            mastered_list = list(mastered)
            mastered_list.sort(key=lambda nid: profile.get_mastery(nid))
            candidates.extend(mastered_list[:needed])

    # Step 2-3: 排序
    sorted_candidates = sort_candidates(candidates, edges)

    # 合并 context_boost + freshness_boost
    merged_boost = dict(context_boost or {})
    for nid, v in (freshness_boost or {}).items():
        merged_boost[nid] = min(1.0, merged_boost.get(nid, 0.0) + v)

    # Step 4: 选 9-12 节点(知识图谱驱动,传递 edges 推导深度+错题/提问/新鲜度加成)
    selected = select_nodes(sorted_candidates, profile, node_count_target, node_range, edges=edges, context_boost=merged_boost, assessment_node_ids=assessment_node_ids)

    # Step 5: 聚类成 step（step 内按拓扑深度+难度排序）
    raw_steps = cluster_into_steps(selected, n_steps=n_steps, per_step_range=per_step_range, edges=edges)

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

        # 先解析 entry_modes（reason 需要用到）
        entry_modes = resolve_entry_modes(node_ids, profile, force_review=force_review)

        if step_ability:
            ability_names = get_ability_names()
            step_goal = f"掌握{ability_names.get(step_ability, step_ability)}"
        else:
            step_goal = ""

        # 计算 reason
        failed = sum(1 for nid in node_ids if profile.get_failure_count(nid) >= 1)
        new_nodes = sum(1 for nid in node_ids if profile.get_confidence(nid) < 0.3)
        quick_count = sum(1 for m in entry_modes.values() if m == "quick_check")
        short_count = sum(1 for m in entry_modes.values() if m == "short_learning")
        full_count = sum(1 for m in entry_modes.values() if m == "full_learning")

        parts: list[str] = []
        if session_index > 0:
            parts.append(f"第{session_index + 1}轮路径")
        if failed >= 2:
            parts.append(f"{failed}个节点需要重学")
        elif failed == 1:
            parts.append("含1个待重学节点")
        if new_nodes >= len(node_ids) * 0.7 and session_index > 0:
            parts.append("进入新章节")
        # 教学模式分布
        mode_parts = []
        if full_count:
            mode_parts.append(f"{full_count}个完整学")
        if short_count:
            mode_parts.append(f"{short_count}个精简学")
        if quick_count:
            mode_parts.append(f"{quick_count}个快速测")
        if mode_parts:
            parts.append("，".join(mode_parts))
        if step_ability:
            ability_names = get_ability_names()
            ab_label = ability_names.get(step_ability, step_ability)
            parts.append(f"主攻{ab_label}")
        if chapter and chapter != "其他":
            parts.append(f"章节：{chapter}")

        reason = "；".join(parts) if parts else "基于当前画像与递进逻辑的推荐"
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
