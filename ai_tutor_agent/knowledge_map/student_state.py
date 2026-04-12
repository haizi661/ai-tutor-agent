from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


@dataclass
class StudentState:
    student_id: str
    current_node_id: str = ""
    last_question: str = ""
    mastery_scores: dict[str, float] = field(default_factory=dict)
    visited_nodes: list[str] = field(default_factory=list)
    wrong_nodes: list[str] = field(default_factory=list)
    recommended_queue: list[str] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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

        return StudentState(
            student_id=raw.get("student_id", student_id),
            current_node_id=raw.get("current_node_id", ""),
            last_question=raw.get("last_question", ""),
            mastery_scores=raw.get("mastery_scores", {}) or {},
            visited_nodes=raw.get("visited_nodes", []) or [],
            wrong_nodes=raw.get("wrong_nodes", []) or [],
            recommended_queue=raw.get("recommended_queue", []) or [],
            notes=raw.get("notes", {}) or {},
        )

    def save(self, state: StudentState) -> None:
        path = self._build_path(state.student_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)