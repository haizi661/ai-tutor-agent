from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any


def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


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
    #       "mastery_score": 0.72
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
    # 用户知识图谱：只包含已学习的节点，学了才加进去
    # 结构: {node_id: {title, status, score, attempts, wrong_questions, evidence, last_updated}}
    knowledge_graph: dict[str, dict[str, Any]] = field(default_factory=dict)

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
        entry = self.kg_register_node(node_id, title) if node_id not in self.knowledge_graph else self.knowledge_graph[node_id]
        entry["score"] = max(0, min(100, int(score)))
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
            "score": int(score),
            "detail": f"{source} {'通过' if passed else '未通过'}，得分 {score}",
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
        self.mastery_scores[node_id] = score
        record = self.ensure_node_record(node_id)
        record["mastery_score"] = score

    def add_homework(self, question_id: str) -> None:
        question_id = str(question_id).strip()
        if question_id and question_id not in self.homework:
            self.homework.append(question_id)

    def remove_homework(self, question_id: str) -> None:
        question_id = str(question_id).strip()
        if question_id in self.homework:
            self.homework.remove(question_id)



class StudentStateStore:
    def __init__(self, state_dir: str | Path = "data/student_states") -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _build_path(self, student_id: str) -> Path:
        safe_id = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in student_id)
        return self.state_dir / f"{safe_id}.json"

    def load(self, student_id: str) -> StudentState:
        path = self._build_path(student_id)
        if not path.exists():
            return StudentState(student_id=student_id)

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        state = StudentState(
            student_id=raw.get("student_id", student_id),
            current_node_id=raw.get("current_node_id", ""),
            last_question=raw.get("last_question", ""),
            mastery_scores=raw.get("mastery_scores", {}) or {},
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
        )

        # 向后兼容：如果旧数据里只有 mastery_scores，没有 node_learning_records
        for node_id, score in state.mastery_scores.items():
            record = state.ensure_node_record(node_id)
            if not record.get("mastery_score"):
                record["mastery_score"] = score

        return state

    def save(self, state: StudentState) -> None:
        path = self._build_path(state.student_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)