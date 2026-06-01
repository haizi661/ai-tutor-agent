from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


MAX_HOMEWORK_HISTORY = 100
MAX_QUESTION_ATTEMPTS = 200
MAX_DAILY_LEARNING_DAYS = 90
MAX_WRONG_BOOK = 200
MAX_QUESTION_HELP_RECORDS = 80


def clamp_score_0_100(score: Any) -> float:
    try:
        value = float(score)
    except (TypeError, ValueError):
        value = 0.0
    return max(0.0, min(100.0, value))


def _normalize_mastery_scores(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    return {
        str(node_id).strip(): clamp_score_0_100(score)
        for node_id, score in value.items()
        if str(node_id).strip()
    }


@dataclass
class StudentState:
    student_id: str
    current_node_id: str = ""
    last_question: str = ""

    # 原有字段
    mastery_scores: dict[str, float] = field(default_factory=dict)
    visited_nodes: list[str] = field(default_factory=list)
    wrong_nodes: list[str] = field(default_factory=list)
    recommended_queue: list[str] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)

    # 新增字段：节点学习记录
    # 结构示例：
    # {
    #   "KM007": {
    #       "started_at": "2026-04-22T15:30:00",
    #       "completed_at": "2026-04-22T16:00:00",
    #       "mastery_score": 72
    #   }
    # }
    node_learning_records: dict[str, dict[str, Any]] = field(default_factory=dict)

    homework: list[str] = field(default_factory=list)
    homework_assignments: list[dict[str, Any]] = field(default_factory=list)
    homework_history: list[dict[str, Any]] = field(default_factory=list)
    question_attempts: list[dict[str, Any]] = field(default_factory=list)
    evidence_events: list[dict[str, Any]] = field(default_factory=list)  # legacy: no longer written; kept for JSON backward compat
    daily_learning_records: dict[str, list[str]] = field(default_factory=dict)
    last_learning_at: str = ""
    teaching_strategy: str = ""
    difficulty_level: int = 0
    # 错题本：跨节点聚合的结构化错题集
    # 每项结构:
    #   question_id, node_id, node_name, stem, options,
    #   user_answer, correct_answer,
    #   wrong_reason, misconception, target_objective,
    #   explanation, recommended_review, wrong_option_analysis,
    #   time_wrong, time_latest, wrong_count,
    #   review_count, last_reviewed, mastered
    wrong_question_book: list[dict[str, Any]] = field(default_factory=list)
    # 题目答疑：用户临时上传文字/图片题目后的解答记录
    question_help_records: list[dict[str, Any]] = field(default_factory=list)

    # 用户知识图谱：只包含已学习的节点，学了才加进去
    # 结构: {node_id: {title, status, score, attempts, wrong_questions, evidence, last_updated}}
    knowledge_graph: dict[str, dict[str, Any]] = field(default_factory=dict)

    # 学习路径（Learning Plan v1）：多步学习计划
    learning_plan: list[dict[str, Any]] = field(default_factory=list)
    learning_plan_current_step: int = 0
    learning_plan_generated_at: str = ""
    learning_plan_source: str = ""

    # ── v2 自适应学习路径字段 ──
    # 学生画像: node_id → {mastery, confidence, source, risk, failure_count, last_score, last_updated}
    concept_mastery: dict[str, dict[str, Any]] = field(default_factory=dict)
    # v2 学习路径: LearningPlan.to_dict()
    learning_plan_v2: dict[str, Any] = field(default_factory=dict)
    # 当前第几次 session(从 0 开始)
    session_index: int = 0
    # 8 维自评原始分数(如 {A: 4, B: 3})
    self_assessment_scores: dict[str, int] = field(default_factory=dict)
    # 是否跳过自评
    skip_self_assessment: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def kg_register_node(self, node_id: str, title: str = "") -> dict[str, Any]:
        """Register a node when the user first starts learning it."""
        if node_id not in self.knowledge_graph:
            self.knowledge_graph[node_id] = {
                "title": title or node_id,
                "status": "in_progress",
                "score": 0,
                "attempts": 0,
                "wrong_questions": [],
                "evidence": [],
                "last_updated": now_ts(),
            }
        return self.knowledge_graph[node_id]

    def kg_update_score(
        self,
        node_id: str,
        score: int,
        *,
        passed: bool,
        wrong_items: list[dict[str, Any]] | None = None,
        source: str = "quiz",
        title: str = "",
    ) -> None:
        """Update score, collect wrong questions, record evidence after a quiz/homework."""
        normalized_score = int(round(clamp_score_0_100(score)))
        entry = self.kg_register_node(node_id, title) if node_id not in self.knowledge_graph else self.knowledge_graph[node_id]
        entry["score"] = normalized_score
        entry["attempts"] = int(entry.get("attempts") or 0) + 1
        entry["status"] = "mastered" if passed else "in_progress"
        entry["last_updated"] = now_ts()
        # Collect wrong questions
        if wrong_items:
            for item in wrong_items:
                entry["wrong_questions"].append({
                    "question_id": str(item.get("question_id") or item.get("id") or ""),
                    "stem": str(item.get("stem") or item.get("prompt") or "")[:200],
                    "student_answer": str(item.get("student_answer") or item.get("answer") or ""),
                    "correct_answer": str(item.get("correct_answer") or item.get("expected") or item.get("answer_key") or ""),
                    "feedback": str(item.get("feedback") or "")[:200],
                    "source": source,
                    "time": now_ts(),
                })
        # Record evidence (有理有据)
        entry["evidence"].append({
            "type": f"{source}_{'pass' if passed else 'fail'}",
            "score": normalized_score,
            "detail": f"{source} {'通过' if passed else '未通过'}，得分 {normalized_score}",
            "time": now_ts(),
        })
        # Cap wrong_questions and evidence to prevent unbounded growth
        if len(entry["wrong_questions"]) > 100:
            entry["wrong_questions"] = entry["wrong_questions"][-100:]
        if len(entry["evidence"]) > 50:
            entry["evidence"] = entry["evidence"][-50:]

    def ensure_node_record(self, node_id: str) -> dict[str, Any]:
        if node_id not in self.node_learning_records:
            self.node_learning_records[node_id] = {
                "started_at": "",
                "completed_at": "",
                "mastery_score": self.mastery_scores.get(node_id, 0.0),
            }
        return self.node_learning_records[node_id]

    def mark_node_started(self, node_id: str) -> None:
        record = self.ensure_node_record(node_id)
        if not record.get("started_at"):
            record["started_at"] = now_ts()

    def mark_node_completed(self, node_id: str) -> None:
        record = self.ensure_node_record(node_id)
        if not record.get("started_at"):
            record["started_at"] = now_ts()
        record["completed_at"] = now_ts()

    def update_mastery(self, node_id: str, score: float) -> None:
        normalized_score = clamp_score_0_100(score)
        self.mastery_scores[node_id] = normalized_score
        record = self.ensure_node_record(node_id)
        record["mastery_score"] = normalized_score

    def add_homework(self, question_id: str) -> None:
        question_id = str(question_id).strip()
        if question_id and question_id not in self.homework:
            self.homework.append(question_id)

    def remove_homework(self, question_id: str) -> None:
        question_id = str(question_id).strip()
        if question_id in self.homework:
            self.homework.remove(question_id)

    # ── 错题本操作 ──────────────────────────────────────────

    def wb_add_or_update(self, wrong_items: list[dict[str, Any]], node_id: str, node_name: str) -> None:
        """从批改结果中添加或更新错题本条目（最小结构）。"""
        now = now_ts()
        for item in wrong_items:
            qid = str(item.get("question_id") or "").strip()
            if not qid:
                continue
            # 查找已有条目
            found = False
            for entry in self.wrong_question_book:
                if entry.get("question_id") == qid:
                    entry["wrong_count"] = int(entry.get("wrong_count") or 0) + 1
                    entry["time_latest"] = now
                    entry["user_answer"] = str(item.get("user_answer") or "").strip().upper()
                    found = True
                    break
            if not found:
                self.wrong_question_book.append({
                    "question_id": qid,
                    "node_id": node_id,
                    "node_name": node_name,
                    "stem": str(item.get("stem") or "")[:200],
                    "options": dict(item.get("options") or {}),
                    "user_answer": str(item.get("user_answer") or "").strip().upper(),
                    "correct_answer": str(item.get("answer_key") or "").strip().upper(),
                    "wrong_reason": "",
                    "misconception": "",
                    "target_objective": "",
                    "explanation": "",
                    "why_user_wrong": "",
                    "why_correct": "",
                    "key_rule": "",
                    "review_action": "",
                    "recommended_review": {},
                    "wrong_option_analysis": {},
                    "time_wrong": now,
                    "time_latest": now,
                    "wrong_count": 1,
                    "review_count": 0,
                    "last_reviewed": None,
                    "mastered": False,
                })

    def wb_enrich(self, explanations: list[dict[str, Any]]) -> None:
        """从错题讲解结果中补充富字段。"""
        for exp in explanations:
            qid = str(exp.get("question_id") or "").strip()
            if not qid:
                continue
            for entry in self.wrong_question_book:
                if entry.get("question_id") == qid:
                    entry["wrong_reason"] = str(exp.get("wrong_reason") or "")
                    entry["misconception"] = str(exp.get("misconception") or "")
                    entry["target_objective"] = str(exp.get("target_objective") or "")
                    entry["explanation"] = str(exp.get("explanation") or "")
                    entry["why_user_wrong"] = str(exp.get("why_user_wrong") or "")
                    entry["why_correct"] = str(exp.get("why_correct") or "")
                    entry["key_rule"] = str(exp.get("key_rule") or "")
                    entry["review_action"] = str(exp.get("review_action") or "")
                    entry["recommended_review"] = dict(exp.get("recommended_review") or {})
                    entry["wrong_option_analysis"] = dict(exp.get("wrong_option_analysis") or {})
                    break

    def wb_mark_mastered(self, question_id: str, mastered: bool = True) -> bool:
        for entry in self.wrong_question_book:
            if entry.get("question_id") == question_id:
                entry["mastered"] = mastered
                return True
        return False

    def wb_mark_reviewed(self, question_id: str) -> bool:
        for entry in self.wrong_question_book:
            if entry.get("question_id") == question_id:
                entry["review_count"] = int(entry.get("review_count") or 0) + 1
                entry["last_reviewed"] = now_ts()
                return True
        return False

    def wb_unmastered_count(self) -> int:
        return sum(1 for e in self.wrong_question_book if not e.get("mastered"))

    # ── 题目答疑记录 ────────────────────────────────────────

    def qh_add_record(self, record: dict[str, Any]) -> dict[str, Any]:
        clean = dict(record or {})
        if not clean.get("record_id"):
            clean["record_id"] = f"qh-{len(self.question_help_records) + 1}"
        if not clean.get("created_at"):
            clean["created_at"] = now_ts()
        clean["question_text"] = str(clean.get("question_text") or "").strip()
        clean["answer"] = str(clean.get("answer") or "").strip()
        clean["images"] = [dict(item) for item in list(clean.get("images") or []) if isinstance(item, dict)]
        clean["image_count"] = len(clean["images"])
        self.question_help_records.append(clean)
        self.question_help_records = self.question_help_records[-MAX_QUESTION_HELP_RECORDS:]
        return clean


class StudentStateStore:
    def __init__(self, state_dir: str | Path = "data/student_states") -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._locks_guard = threading.RLock()
        self._locks: dict[str, threading.RLock] = {}

    def _safe_student_id(self, student_id: str) -> str:
        safe_id = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(student_id or "default_student"))
        return safe_id or "default_student"

    def _lock_for(self, student_id: str) -> threading.RLock:
        safe_id = self._safe_student_id(student_id)
        with self._locks_guard:
            lock = self._locks.get(safe_id)
            if lock is None:
                lock = threading.RLock()
                self._locks[safe_id] = lock
            return lock

    def lock_for(self, student_id: str) -> threading.RLock:
        return self._lock_for(student_id)

    def _build_path(self, student_id: str) -> Path:
        safe_id = self._safe_student_id(student_id)
        return self.state_dir / f"{safe_id}.json"

    def load(self, student_id: str) -> StudentState:
        with self._lock_for(student_id):
            return self._load_unlocked(student_id)

    def _load_unlocked(self, student_id: str) -> StudentState:
        path = self._build_path(student_id)
        if not path.exists():
            return StudentState(student_id=student_id)

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        state = StudentState(
            student_id=raw.get("student_id", student_id),
            current_node_id=raw.get("current_node_id", ""),
            last_question=raw.get("last_question", ""),
            mastery_scores=_normalize_mastery_scores(raw.get("mastery_scores", {}) or {}),
            visited_nodes=raw.get("visited_nodes", []) or [],
            wrong_nodes=raw.get("wrong_nodes", []) or [],
            recommended_queue=raw.get("recommended_queue", []) or [],
            notes=raw.get("notes", {}) or {},
            node_learning_records=raw.get("node_learning_records", {}) or {},
            homework=raw.get("homework", []) or [],
            homework_assignments=raw.get("homework_assignments", []) or [],
            homework_history=raw.get("homework_history", []) or [],
            question_attempts=raw.get("question_attempts", []) or [],
            evidence_events=raw.get("evidence_events", []) or [],
            daily_learning_records=raw.get("daily_learning_records", {}) or {},
            last_learning_at=raw.get("last_learning_at", "") or "",
            teaching_strategy=raw.get("teaching_strategy", "") or "",
            difficulty_level=int(raw.get("difficulty_level") or 0),
            knowledge_graph=raw.get("knowledge_graph", {}) or {},
            wrong_question_book=raw.get("wrong_question_book", []) or [],
            question_help_records=raw.get("question_help_records", []) or [],
            learning_plan=raw.get("learning_plan", []) or [],
            learning_plan_current_step=int(raw.get("learning_plan_current_step") or 0),
            learning_plan_generated_at=raw.get("learning_plan_generated_at", "") or "",
            learning_plan_source=raw.get("learning_plan_source", "") or "",
            # v2 字段，向后兼容：旧数据没有则取默认
            concept_mastery=raw.get("concept_mastery", {}) or {},
            learning_plan_v2=raw.get("learning_plan_v2", {}) or {},
            session_index=int(raw.get("session_index") or 0),
            self_assessment_scores=raw.get("self_assessment_scores", {}) or {},
            skip_self_assessment=bool(raw.get("skip_self_assessment", True)),
        )

        # 向后兼容：如果旧数据里只有 mastery_scores，没有 node_learning_records
        for node_id, score in state.mastery_scores.items():
            record = state.ensure_node_record(node_id)
            if not record.get("mastery_score"):
                record["mastery_score"] = score
        for record in (state.node_learning_records or {}).values():
            if isinstance(record, dict) and "mastery_score" in record:
                record["mastery_score"] = clamp_score_0_100(record.get("mastery_score"))

        return state

    def save(self, state: StudentState) -> None:
        with self._lock_for(state.student_id):
            self._save_unlocked(state)

    def update(self, student_id: str, mutator: Callable[[StudentState], Any]) -> StudentState:
        with self._lock_for(student_id):
            state = self._load_unlocked(student_id)
            result = mutator(state)
            if isinstance(result, StudentState):
                state = result
            self._save_unlocked(state)
            return state

    def _save_unlocked(self, state: StudentState) -> None:
        self._normalize_for_storage(state)
        path = self._build_path(state.student_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)

    def _normalize_for_storage(self, state: StudentState) -> None:
        state.mastery_scores = _normalize_mastery_scores(state.mastery_scores)
        for node_id, score in list(state.mastery_scores.items()):
            record = state.ensure_node_record(node_id)
            record["mastery_score"] = score
        for record in (state.node_learning_records or {}).values():
            if isinstance(record, dict) and "mastery_score" in record:
                record["mastery_score"] = clamp_score_0_100(record.get("mastery_score"))
        state.homework_history = list(state.homework_history or [])[-MAX_HOMEWORK_HISTORY:]
        state.question_attempts = list(state.question_attempts or [])[-MAX_QUESTION_ATTEMPTS:]
        state.question_help_records = list(state.question_help_records or [])[-MAX_QUESTION_HELP_RECORDS:]
        if state.daily_learning_records:
            kept_days = sorted(str(day) for day in state.daily_learning_records.keys())[-MAX_DAILY_LEARNING_DAYS:]
            state.daily_learning_records = {
                day: list(state.daily_learning_records.get(day) or [])
                for day in kept_days
            }
        # Cap wrong_question_book: sort by latest wrong time desc, keep top N
        state.wrong_question_book = sorted(
            list(state.wrong_question_book or []),
            key=lambda e: e.get("time_latest", ""),
            reverse=True,
        )[:MAX_WRONG_BOOK]

        for entry in (state.knowledge_graph or {}).values():
            entry["score"] = int(round(clamp_score_0_100(entry.get("score", 0))))
            entry["wrong_questions"] = list(entry.get("wrong_questions") or [])[-100:]
            entry["evidence"] = list(entry.get("evidence") or [])[-50:]
