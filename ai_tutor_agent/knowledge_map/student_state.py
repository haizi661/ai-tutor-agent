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

    # 新增字段：当前布置给学生的作业题目ID
    # 例如：["1-1", "1-2", "2-1"]
    homework: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

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