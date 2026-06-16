from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .platform_paths import resolve_project_path


@dataclass(frozen=True)
class CourseAssetConfig:
    course_id: str
    display_name: str
    topic_name: str
    nodes_csv_path: str
    edges_csv_path: str
    source_materials_dir: str
    mineru_cache_root: str
    media_evidence_index_dir: str
    student_state_path: str
    prompt_subject: str

    def resolve(self, field_name: str) -> Path:
        value = getattr(self, field_name)
        return resolve_project_path(value)


AUTO_CONTROL_COURSE = CourseAssetConfig(
    course_id="auto_control",
    display_name="自动控制原理",
    topic_name="自动控制原理",
    nodes_csv_path="data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
    edges_csv_path="data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv",
    source_materials_dir="data/course_materials/auto_control",
    mineru_cache_root="data/mineru_cache",
    media_evidence_index_dir="data/media_evidence_index_vision_pilot",
    student_state_path="data/student_states/default.json",
    prompt_subject="自动控制原理课程",
)

ARTIFICIAL_INTELLIGENCE_COURSE = CourseAssetConfig(
    course_id="artificial_intelligence",
    display_name="人工智能",
    topic_name="人工智能",
    nodes_csv_path="data/knowledge_map_outputs/artificial_intelligence/ai_nodes.csv",
    edges_csv_path="data/knowledge_map_outputs/artificial_intelligence/ai_edges.csv",
    source_materials_dir="data/course_materials/artificial_intelligence",
    mineru_cache_root="data/mineru_cache/artificial_intelligence",
    media_evidence_index_dir="data/media_evidence_index/artificial_intelligence",
    student_state_path="data/student_states/artificial_intelligence/student_state.json",
    prompt_subject="人工智能课程",
)

COURSE_ASSETS: dict[str, CourseAssetConfig] = {
    AUTO_CONTROL_COURSE.course_id: AUTO_CONTROL_COURSE,
    ARTIFICIAL_INTELLIGENCE_COURSE.course_id: ARTIFICIAL_INTELLIGENCE_COURSE,
}

COURSE_ALIASES: dict[str, str] = {
    "a2-control-theory": AUTO_CONTROL_COURSE.course_id,
    "control": AUTO_CONTROL_COURSE.course_id,
    "auto-control": AUTO_CONTROL_COURSE.course_id,
    "auto_control": AUTO_CONTROL_COURSE.course_id,
    "automatic_control": AUTO_CONTROL_COURSE.course_id,
    "ai": ARTIFICIAL_INTELLIGENCE_COURSE.course_id,
    "artificial-intelligence": ARTIFICIAL_INTELLIGENCE_COURSE.course_id,
    "artificial_intelligence": ARTIFICIAL_INTELLIGENCE_COURSE.course_id,
}


def normalize_course_id(course_id: str | None) -> str:
    raw = (course_id or AUTO_CONTROL_COURSE.course_id).strip()
    return COURSE_ALIASES.get(raw, raw)


def get_course_assets(course_id: str | None = None) -> CourseAssetConfig:
    normalized = normalize_course_id(course_id)
    try:
        return COURSE_ASSETS[normalized]
    except KeyError as exc:
        known = ", ".join(sorted(COURSE_ASSETS))
        raise ValueError(f"Unknown course_id {course_id!r}. Known courses: {known}") from exc
