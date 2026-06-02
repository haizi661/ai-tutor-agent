"""Student Profile — 学生画像管理。

每个概念节点维护:
- mastery: 0.0 - 1.0 掌握度估计
- confidence: 0.0 - 1.0 系统对该估计的信任度
- source: self_assessment / quick_check / practice / test / default / merged
- risk: low / medium / high 风险等级
- failure_count: 错题次数
- last_score: 最近一次测验得分(0-1)
- last_updated: ISO 时间戳

支持的操作:
1. 从自评初始化
2. 跳过自评时使用默认冷启动画像
3. 测验后更新(加权,不覆盖)
4. 练习后更新
5. 序列化(to_dict / from_dict)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from .ability_mapper import (
    get_default_mastery_when_skipped,
    map_self_scores_to_concept_mastery,
    reset_cache as _reset_ability_mapper_cache,
)


SOURCE_WEIGHTS: dict[str, float] = {
    "default": 0.2,
    "self_assessment": 0.3,
    "quick_check": 0.7,
    "practice": 0.85,
    "test": 0.95,
    "merged": 0.8,  # 多源加权合并后的来源
}


@dataclass
class ConceptMastery:
    """单概念画像。"""

    mastery: float
    confidence: float
    source: str
    risk: str = "low"
    failure_count: int = 0
    last_score: float = 0.0
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mastery": round(float(self.mastery), 4),
            "confidence": round(float(self.confidence), 4),
            "source": str(self.source),
            "risk": str(self.risk),
            "failure_count": int(self.failure_count),
            "last_score": round(float(self.last_score), 4),
            "last_updated": str(self.last_updated),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ConceptMastery":
        return cls(
            mastery=float(raw.get("mastery", 0.0) or 0.0),
            confidence=float(raw.get("confidence", 0.0) or 0.0),
            source=str(raw.get("source", "default") or "default"),
            risk=str(raw.get("risk", "low") or "low"),
            failure_count=int(raw.get("failure_count", 0) or 0),
            last_score=float(raw.get("last_score", 0.0) or 0.0),
            last_updated=str(raw.get("last_updated", "") or ""),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def _infer_risk(mastery: float, confidence: float, failure_count: int) -> str:
    if failure_count >= 2:
        return "high"
    if mastery < 0.4 or (mastery < 0.6 and confidence < 0.4):
        return "high"
    if mastery < 0.6 or confidence < 0.5:
        return "medium"
    return "low"


# ── 画像主类 ─────────────────────────────────────────

class StudentProfile:
    """学生画像管理器:支持初始化、增量更新、序列化。"""

    def __init__(self, profile_id: str = "default_student") -> None:
        self.profile_id = profile_id
        self.concept_mastery: dict[str, ConceptMastery] = {}
        self.created_at: str = _now_iso()
        self.last_updated: str = self.created_at

    # ── 初始化 ──────────────────────────────────────

    def init_from_self_assessment(self, self_scores: dict[str, int]) -> int:
        """用 8 维自评分数初始化。返回写入的概念数。"""
        if not self._ensure_mapper_loaded():
            return 0
        mapped = map_self_scores_to_concept_mastery(self_scores)
        return self._bulk_set(mapped)

    def init_from_default(self) -> int:
        """跳过自评时使用默认冷启动画像。"""
        if not self._ensure_mapper_loaded():
            return 0
        mapped = get_default_mastery_when_skipped()
        return self._bulk_set(mapped)

    def _bulk_set(self, mapped: dict[str, dict[str, Any]]) -> int:
        now = _now_iso()
        for concept_id, payload in mapped.items():
            self.concept_mastery[concept_id] = ConceptMastery(
                mastery=_clamp(payload.get("mastery", 0.0)),
                confidence=_clamp(payload.get("confidence", 0.2)),
                source=str(payload.get("source", "default")),
                risk=str(payload.get("risk", "low")),
                failure_count=0,
                last_score=0.0,
                last_updated=now,
            )
        self.last_updated = now
        return len(mapped)

    def _ensure_mapper_loaded(self) -> bool:
        """轻量自检:确保 ability_mapper 可用。"""
        try:
            from . import ability_mapper  # noqa: F401
            return True
        except Exception:
            return False

    # ── 增量更新 ───────────────────────────────────

    def update_after_quiz(
        self,
        concept_id: str,
        observed_score: float,
        passed: bool,
    ) -> ConceptMastery:
        """测验后更新:加权更新(不覆盖)。

        new_mastery = old_mastery * (1 - new_confidence) + observed_score * new_confidence
        new_confidence = max(old_confidence, SOURCE_WEIGHTS['test'])

        passed 标 mastered,否则 failure_count += 1
        """
        new_confidence = SOURCE_WEIGHTS["test"]
        old = self.concept_mastery.get(concept_id) or ConceptMastery(
            mastery=0.0, confidence=0.0, source="default"
        )
        observed = _clamp(observed_score)
        new_mastery = old.mastery * (1 - new_confidence) + observed * new_confidence
        new_mastery = _clamp(new_mastery)
        failure_count = old.failure_count + (0 if passed else 1)
        merged = ConceptMastery(
            mastery=new_mastery,
            confidence=max(old.confidence, new_confidence),
            source="merged",
            risk=_infer_risk(new_mastery, max(old.confidence, new_confidence), failure_count),
            failure_count=failure_count,
            last_score=observed,
            last_updated=_now_iso(),
        )
        if passed and merged.mastery >= 0.8:
            # 通过 + 掌握度够 → 视为 mastered
            pass  # 状态标记由外层(路径完成)决定
        self.concept_mastery[concept_id] = merged
        self.last_updated = merged.last_updated
        return merged

    def update_after_practice(
        self,
        concept_id: str,
        observed_score: float,
    ) -> ConceptMastery:
        """练习后更新(不增加 failure_count,因为不是测验)。"""
        new_confidence = SOURCE_WEIGHTS["practice"]
        old = self.concept_mastery.get(concept_id) or ConceptMastery(
            mastery=0.0, confidence=0.0, source="default"
        )
        observed = _clamp(observed_score)
        new_mastery = old.mastery * (1 - new_confidence) + observed * new_confidence
        new_mastery = _clamp(new_mastery)
        merged = ConceptMastery(
            mastery=new_mastery,
            confidence=max(old.confidence, new_confidence),
            source="merged",
            risk=_infer_risk(new_mastery, max(old.confidence, new_confidence), old.failure_count),
            failure_count=old.failure_count,
            last_score=observed,
            last_updated=_now_iso(),
        )
        self.concept_mastery[concept_id] = merged
        self.last_updated = merged.last_updated
        return merged

    def update_after_quick_check(
        self,
        concept_id: str,
        observed_score: float,
        passed: bool,
    ) -> ConceptMastery:
        """快测后更新。"""
        new_confidence = SOURCE_WEIGHTS["quick_check"]
        old = self.concept_mastery.get(concept_id) or ConceptMastery(
            mastery=0.0, confidence=0.0, source="default"
        )
        observed = _clamp(observed_score)
        new_mastery = old.mastery * (1 - new_confidence) + observed * new_confidence
        new_mastery = _clamp(new_mastery)
        failure_count = old.failure_count + (0 if passed else 1)
        merged = ConceptMastery(
            mastery=new_mastery,
            confidence=max(old.confidence, new_confidence),
            source="merged",
            risk=_infer_risk(new_mastery, max(old.confidence, new_confidence), failure_count),
            failure_count=failure_count,
            last_score=observed,
            last_updated=_now_iso(),
        )
        self.concept_mastery[concept_id] = merged
        self.last_updated = merged.last_updated
        return merged

    def mark_mastered(self, concept_id: str) -> ConceptMastery:
        """路径完成后标 mastered。"""
        old = self.concept_mastery.get(concept_id) or ConceptMastery(
            mastery=0.0, confidence=0.0, source="default"
        )
        merged = ConceptMastery(
            mastery=max(old.mastery, 0.9),
            confidence=max(old.confidence, 0.85),
            source="merged",
            risk="low",
            failure_count=old.failure_count,
            last_score=old.last_score,
            last_updated=_now_iso(),
        )
        self.concept_mastery[concept_id] = merged
        self.last_updated = merged.last_updated
        return merged

    def mark_skipped_with_risk(self, concept_id: str) -> ConceptMastery:
        """快测过但风险高,标 skipped_with_risk。"""
        old = self.concept_mastery.get(concept_id) or ConceptMastery(
            mastery=0.5, confidence=0.5, source="quick_check"
        )
        merged = ConceptMastery(
            mastery=old.mastery,
            confidence=min(old.confidence, 0.5),
            source="merged",
            risk="medium",
            failure_count=old.failure_count,
            last_score=old.last_score,
            last_updated=_now_iso(),
        )
        self.concept_mastery[concept_id] = merged
        self.last_updated = merged.last_updated
        return merged

    # ── 查询 ──────────────────────────────────────

    def is_mastered(self, concept_id: str) -> bool:
        entry = self.concept_mastery.get(concept_id)
        if not entry:
            return False
        return entry.mastery >= 0.85 and entry.confidence >= 0.7

    def get_mastery(self, concept_id: str) -> float:
        return float(self.concept_mastery.get(concept_id, ConceptMastery(0, 0, "default")).mastery)

    def get_confidence(self, concept_id: str) -> float:
        return float(self.concept_mastery.get(concept_id, ConceptMastery(0, 0, "default")).confidence)

    def get_failure_count(self, concept_id: str) -> int:
        return int(self.concept_mastery.get(concept_id, ConceptMastery(0, 0, "default")).failure_count)

    def get_risk(self, concept_id: str) -> str:
        return str(self.concept_mastery.get(concept_id, ConceptMastery(0, 0, "default")).risk)

    def get_mastered_concept_ids(self) -> set[str]:
        return {nid for nid, entry in self.concept_mastery.items() if self.is_mastered(nid)}

    def get_failed_concept_ids(self) -> set[str]:
        return {nid for nid, entry in self.concept_mastery.items() if entry.failure_count >= 1}

    def get_entry_mode(self, concept_id: str) -> str:
        """决定一个节点的 entry_mode。

        规则:
        - mastery 或 entry 不存在(冷启动) → full_learning
        - failure_count >= 2 → full_learning(多次失败,完整重学)
        - source == "self_assessment" 且 mastery < 0.7(自评不够高)
          → full_learning(仅凭自评,未经过真实学习,不可跳过完整讲解)
        - mastery < 0.4 → full_learning
        - mastery < 0.7 → short_learning
        - mastery >= 0.7 → quick_check

        注：source == "default" 不再一刀切返回 full_learning。
        默认画像（未自评）时不同节点仍有不同 mastery 值（来自 ability_mapper
        的 8 维默认分数），让 mastery 决定 entry_mode 即可。
        首节点保护由 initial_node_selector 负责（强制 full_learning），
        避免首个节点被 short_learning / quick_check 跳过完整讲解。
        """
        entry = self.concept_mastery.get(concept_id)
        if not entry:
            return "full_learning"
        if entry.failure_count >= 2:
            return "full_learning"
        if entry.source == "self_assessment" and entry.mastery < 0.7:
            return "full_learning"
        if entry.mastery < 0.4:
            return "full_learning"
        if entry.mastery < 0.7:
            return "short_learning"
        return "quick_check"

    # ── 序列化 ─────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "concept_mastery": {
                nid: entry.to_dict() for nid, entry in self.concept_mastery.items()
            },
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "StudentProfile":
        instance = cls(profile_id=str(raw.get("profile_id", "default_student")))
        instance.created_at = str(raw.get("created_at", instance.created_at))
        instance.last_updated = str(raw.get("last_updated", instance.last_updated))
        for nid, payload in (raw.get("concept_mastery") or {}).items():
            instance.concept_mastery[nid] = ConceptMastery.from_dict(payload)
        return instance

    # ── 调试 ──────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """画像摘要,用于日志 / 调试。"""
        if not self.concept_mastery:
            return {"profile_id": self.profile_id, "total": 0}
        masteries = [e.mastery for e in self.concept_mastery.values()]
        confs = [e.confidence for e in self.concept_mastery.values()]
        return {
            "profile_id": self.profile_id,
            "total": len(self.concept_mastery),
            "avg_mastery": round(sum(masteries) / len(masteries), 3),
            "avg_confidence": round(sum(confs) / len(confs), 3),
            "mastered": len(self.get_mastered_concept_ids()),
            "failed": len(self.get_failed_concept_ids()),
            "last_updated": self.last_updated,
        }


# ── 模块级工具 ─────────────────────────────────────────

def reset_all_caches() -> None:
    """测试用,清空所有缓存。"""
    _reset_ability_mapper_cache()


def make_default_profile(profile_id: str = "default_student") -> StudentProfile:
    """快速创建一个冷启动默认画像(跳过自评)。"""
    profile = StudentProfile(profile_id=profile_id)
    profile.init_from_default()
    return profile


def make_profile_from_self_assessment(
    self_scores: dict[str, int],
    profile_id: str = "default_student",
) -> StudentProfile:
    """用自评快速创建画像。"""
    profile = StudentProfile(profile_id=profile_id)
    profile.init_from_self_assessment(self_scores)
    return profile
