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
    relation_weights: dict[str, float] = field(
        default_factory=lambda: {
            "HAS_SUBTOPIC": 1.0,
            "PRE_REQUIRES": 1.2,
            "LEADS_TO": 1.1,
            "RECOMMENDED_NEXT": 1.1,
            "RELATED_TO": 0.8,
            "APPLIED_IN": 0.7,
        }
    )
    hop_penalties: dict[int, float] = field(
        default_factory=lambda: {
            0: 0.0,
            1: 0.0,
            2: 0.4,
            3: 0.9,
            4: 1.5,
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
        }
    )
    relation_preferences: dict[str, list[str]] = field(
        default_factory=lambda: {
            "knowledge_qa": ["HAS_SUBTOPIC", "RELATED_TO", "APPLIED_IN"],
            "prerequisite_query": ["PRE_REQUIRES", "HAS_SUBTOPIC", "RELATED_TO"],
            "learning_path": ["LEADS_TO", "RECOMMENDED_NEXT", "HAS_SUBTOPIC"],
            "requirement_query": ["HAS_SUBTOPIC", "PRE_REQUIRES"],
            "comparative_query": ["RELATED_TO", "HAS_SUBTOPIC", "PRE_REQUIRES", "LEADS_TO"],
            "relation_query": ["RELATED_TO", "PRE_REQUIRES", "LEADS_TO"],
        }
    )
    answer_attribute_defaults: dict[str, list[str]] = field(
        default_factory=lambda: {
            "knowledge_qa": ["summary", "key_points", "examples", "formulas"],
            "prerequisite_query": ["summary", "prerequisite_nodes", "key_points"],
            "learning_path": ["summary", "recommended_next_nodes", "next_nodes", "assessment_focus"],
            "requirement_query": ["requirement_level", "mastery_threshold", "importance_level", "assessment_focus"],
            "comparative_query": ["summary", "key_points", "formulas", "examples"],
            "relation_query": ["summary", "key_points", "prerequisite_nodes", "next_nodes"],
        }
    )
    relation_direction_preferences: dict[str, dict[str, list[str]]] = field(
        default_factory=lambda: {
            "knowledge_qa": {
                "HAS_SUBTOPIC": ["forward", "reverse"],
                "RELATED_TO": ["forward", "reverse"],
                "APPLIED_IN": ["forward", "reverse"],
            },
            "prerequisite_query": {
                "PRE_REQUIRES": ["forward"],
                "HAS_SUBTOPIC": ["forward"],
                "RELATED_TO": ["forward", "reverse"],
            },
            "learning_path": {
                "LEADS_TO": ["forward"],
                "RECOMMENDED_NEXT": ["forward"],
                "HAS_SUBTOPIC": ["forward"],
            },
            "requirement_query": {
                "HAS_SUBTOPIC": ["forward", "reverse"],
                "PRE_REQUIRES": ["forward"],
            },
            "comparative_query": {
                "RELATED_TO": ["forward", "reverse"],
                "HAS_SUBTOPIC": ["forward", "reverse"],
                "PRE_REQUIRES": ["forward", "reverse"],
                "LEADS_TO": ["forward", "reverse"],
            },
            "relation_query": {
                "RELATED_TO": ["forward", "reverse"],
                "PRE_REQUIRES": ["forward", "reverse"],
                "LEADS_TO": ["forward", "reverse"],
            },
        }
    )


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
