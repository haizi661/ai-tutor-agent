from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DepthProfile:
    name: str
    max_depth: int
    node_budget: int
    description: str


@dataclass(frozen=True)
class GraphRAGConfig:
    default_mode: str = "balanced"
    relation_aliases: dict[str, str] = field(
        default_factory=lambda: {
            "HAS_SUBTOPIC": "parallel_to",
            "PRE_REQUIRES": "prerequisite_of",
            "LEADS_TO": "prerequisite_of",
            "RECOMMENDED_NEXT": "prerequisite_of",
            "RELATED_TO": "related_to",
            "APPLIED_IN": "related_to",
            "TESTED_TOGETHER": "parallel_to",
            "COMPARES_WITH": "parallel_to",
            "EASILY_CONFUSED_WITH": "weak_related_to",
        }
    )
    relation_weights: dict[str, float] = field(
        default_factory=lambda: {
            "prerequisite_of": 1.25,
            "parallel_to": 1.0,
            "related_to": 0.85,
            "weak_related_to": 0.55,
            "extends_to": 1.05,
            "easy_to_confuse_with": 0.95,
            "tested_together": 1.0,
        }
    )
    hop_penalties: dict[int, float] = field(
        default_factory=lambda: {
            0: 0.0,
            1: 0.0,
            2: 0.35,
            3: 0.8,
            4: 1.3,
        }
    )
    question_type_defaults: dict[str, str] = field(
        default_factory=lambda: {
            "knowledge_qa": "balanced",
            "prerequisite_query": "balanced",
            "learning_path": "exploratory",
            "requirement_query": "focused",
            "comparative_query": "exploratory",
            "relation_query": "exploratory",
            "assessment_generation": "balanced",
        }
    )
    relation_preferences: dict[str, list[str]] = field(
        default_factory=lambda: {
            "knowledge_qa": ["prerequisite_of", "parallel_to", "related_to"],
            "prerequisite_query": ["prerequisite_of", "parallel_to", "related_to"],
            "learning_path": ["prerequisite_of", "parallel_to", "related_to"],
            "requirement_query": ["prerequisite_of", "parallel_to"],
            "comparative_query": ["parallel_to", "related_to", "weak_related_to", "prerequisite_of"],
            "relation_query": ["related_to", "parallel_to", "prerequisite_of", "weak_related_to"],
            "assessment_generation": ["parallel_to", "related_to", "prerequisite_of", "weak_related_to"],
        }
    )
    answer_attribute_defaults: dict[str, list[str]] = field(
        default_factory=lambda: {
            "knowledge_qa": [
                "summary",
                "core_concepts",
                "key_points",
                "examples",
                "formulas",
                "explanation_teacher_style",
            ],
            "prerequisite_query": [
                "summary",
                "prerequisite_nodes",
                "core_concepts",
                "key_points",
                "importance_level",
            ],
            "learning_path": [
                "summary",
                "recommended_next_nodes",
                "next_nodes",
                "assessment_focus",
                "importance_level",
            ],
            "requirement_query": [
                "requirement_level",
                "mastery_threshold",
                "importance_level",
                "assessment_focus",
                "core_concepts",
            ],
            "comparative_query": [
                "summary",
                "core_concepts",
                "key_points",
                "formulas",
                "examples",
                "assessment_focus",
            ],
            "relation_query": [
                "summary",
                "core_concepts",
                "key_points",
                "prerequisite_nodes",
                "next_nodes",
                "related_nodes",
            ],
            "assessment_generation": [
                "summary",
                "key_points",
                "formulas",
                "examples",
                "assessment_focus",
                "importance_level",
                "core_concepts",
            ],
        }
    )
    relation_direction_preferences: dict[str, dict[str, list[str]]] = field(
        default_factory=lambda: {
            "knowledge_qa": {
                "prerequisite_of": ["forward", "reverse"],
                "parallel_to": ["forward", "reverse"],
                "related_to": ["forward", "reverse"],
                "weak_related_to": ["forward", "reverse"],
            },
            "prerequisite_query": {
                "prerequisite_of": ["reverse"],
                "parallel_to": ["reverse", "forward"],
                "related_to": ["reverse", "forward"],
            },
            "learning_path": {
                "prerequisite_of": ["forward"],
                "parallel_to": ["forward", "reverse"],
                "related_to": ["forward"],
            },
            "requirement_query": {
                "prerequisite_of": ["reverse", "forward"],
                "parallel_to": ["forward", "reverse"],
            },
            "comparative_query": {
                "parallel_to": ["forward", "reverse"],
                "related_to": ["forward", "reverse"],
                "weak_related_to": ["forward", "reverse"],
                "prerequisite_of": ["forward", "reverse"],
            },
            "relation_query": {
                "related_to": ["forward", "reverse"],
                "parallel_to": ["forward", "reverse"],
                "weak_related_to": ["forward", "reverse"],
                "prerequisite_of": ["forward", "reverse"],
            },
            "assessment_generation": {
                "parallel_to": ["forward", "reverse"],
                "related_to": ["forward", "reverse"],
                "weak_related_to": ["forward", "reverse"],
                "prerequisite_of": ["reverse", "forward"],
            },
        }
    )
    important_node_bonus: dict[str, float] = field(
        default_factory=lambda: {
            "核心": 0.35,
            "重要": 0.2,
            "一般": 0.05,
        }
    )
    evidence_attribute_priority: dict[str, int] = field(
        default_factory=lambda: {
            "summary": 0,
            "core_concepts": 1,
            "assessment_focus": 1,
            "prerequisite_nodes": 2,
            "next_nodes": 2,
            "recommended_next_nodes": 2,
            "related_nodes": 2,
            "application_nodes": 2,
            "key_points": 3,
            "explanation_teacher_style": 4,
            "formulas": 5,
            "examples": 6,
            "requirement_level": 7,
            "mastery_threshold": 7,
            "importance_level": 7,
        }
    )

    def normalize_relation(self, relation: str) -> str:
        text = str(relation or "").strip()
        if not text:
            return ""
        return self.relation_aliases.get(text, text)


DEPTH_PROFILES: dict[str, DepthProfile] = {
    "focused": DepthProfile(
        name="focused",
        max_depth=1,
        node_budget=5,
        description="只取锚点及其直接语义邻域，适合定义、概念和局部解释。",
    ),
    "balanced": DepthProfile(
        name="balanced",
        max_depth=2,
        node_budget=10,
        description="一跳核心证据加二跳支撑证据，适合大多数问答。",
    ),
    "exploratory": DepthProfile(
        name="exploratory",
        max_depth=3,
        node_budget=15,
        description="允许跨章节和路径延展，适合关系探索和学习路径问题。",
    ),
}
