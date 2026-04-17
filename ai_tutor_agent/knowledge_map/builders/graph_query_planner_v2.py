from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ai_tutor_agent.core.text import content_to_text
from ai_tutor_agent.knowledge_map.builders.node_selector import NodeSelector
from ai_tutor_agent.knowledge_map.config.graph_rag_config import (
    DEPTH_PROFILES,
    GraphRAGConfig,
)


@dataclass
class GraphQueryPlan:
    question: str
    question_type: str
    anchor_terms: list[str]
    target_attributes: list[str]
    preferred_relations: list[str]
    traversal_mode: str
    max_depth: int
    node_budget: int
    reasoning: str
    used_llm: bool = False


class GraphQueryPlanner:
    def __init__(self, llm: Any | None = None, config: GraphRAGConfig | None = None) -> None:
        self.llm = llm
        self.config = config or GraphRAGConfig()
        self.selector = NodeSelector()

    def plan(
        self,
        question: str,
        *,
        traversal_mode: str | None = None,
        max_depth_override: int | None = None,
    ) -> GraphQueryPlan:
        question_type = self._detect_question_type(question)
        selected_mode = self._resolve_mode(question_type, traversal_mode)
        profile = DEPTH_PROFILES[selected_mode]
        max_depth = max_depth_override if max_depth_override is not None else profile.max_depth
        node_budget = profile.node_budget

        llm_payload = self._invoke_llm_plan(question, question_type, selected_mode)
        anchor_terms = self._clean_terms(llm_payload.get("anchor_terms")) or self._heuristic_anchor_terms(question)
        target_attributes = self._filter_known_values(
            llm_payload.get("target_attributes"),
            self.config.answer_attribute_defaults.get(question_type, []),
        )
        if not target_attributes:
            target_attributes = list(self.config.answer_attribute_defaults.get(question_type, ["summary"]))

        preferred_relations = self._filter_known_values(
            llm_payload.get("preferred_relations"),
            self.config.relation_preferences.get(question_type, []),
        )
        if not preferred_relations:
            preferred_relations = list(self.config.relation_preferences.get(question_type, ["HAS_SUBTOPIC"]))

        reasoning = str(llm_payload.get("reasoning", "") or "").strip()
        if not reasoning:
            reasoning = self._default_reasoning(question_type, selected_mode)

        return GraphQueryPlan(
            question=question,
            question_type=question_type,
            anchor_terms=anchor_terms,
            target_attributes=target_attributes,
            preferred_relations=preferred_relations,
            traversal_mode=selected_mode,
            max_depth=max(1, int(max_depth)),
            node_budget=max(1, int(node_budget)),
            reasoning=reasoning,
            used_llm=bool(llm_payload.get("_used_llm", False)),
        )

    def _invoke_llm_plan(self, question: str, question_type: str, traversal_mode: str) -> dict[str, Any]:
        if self.llm is None:
            return {}

        system_msg = SystemMessage(
            content=(
                "You are a knowledge-graph retrieval planner. "
                "Return JSON only. "
                "Fields: anchor_terms, target_attributes, preferred_relations, reasoning."
            )
        )
        human_msg = HumanMessage(
            content=(
                f"Question: {question}\n"
                f"Question type: {question_type}\n"
                f"Traversal mode: {traversal_mode}\n"
                "target_attributes must be chosen from: "
                "summary, key_points, formulas, examples, prerequisite_nodes, next_nodes, "
                "recommended_next_nodes, requirement_level, mastery_threshold, importance_level, assessment_focus.\n"
                "preferred_relations must be chosen from: "
                "HAS_SUBTOPIC, PRE_REQUIRES, LEADS_TO, RECOMMENDED_NEXT, RELATED_TO, APPLIED_IN."
            )
        )
        try:
            response = self.llm.invoke([system_msg, human_msg])
            payload = json.loads(content_to_text(response.content))
            payload["_used_llm"] = True
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _detect_question_type(self, question: str) -> str:
        normalized = (question or "").strip()
        if any(token in normalized for token in ["区别", "联系", "比较", "对比"]):
            return "comparative_query"
        if any(token in normalized for token in ["关系", "关联", "为什么相关"]):
            return "relation_query"
        return self.selector.detect_question_type(question)

    def _resolve_mode(self, question_type: str, traversal_mode: str | None) -> str:
        requested_mode = (traversal_mode or "").strip().lower()
        if requested_mode in DEPTH_PROFILES:
            return requested_mode
        default_mode = self.config.question_type_defaults.get(question_type, self.config.default_mode)
        if default_mode in DEPTH_PROFILES:
            return default_mode
        return self.config.default_mode

    def _heuristic_anchor_terms(self, question: str) -> list[str]:
        normalized = question.strip()
        if self._detect_question_type(question) == "comparative_query":
            comparison_text = normalized
            for marker in ["区别", "联系", "比较", "对比", "不同", "是什么"]:
                comparison_text = comparison_text.replace(marker, "")
            parts = self._split_comparison_terms(comparison_text)
            if parts:
                return parts

        for marker in [
            "学习",
            "请问",
            "请解释",
            "什么是",
            "如何",
            "怎么",
            "之前要先学什么",
            "之前学什么",
            "之前要学什么",
            "之前需要学什么",
            "之前",
            "要先学什么",
            "先学什么",
            "学什么",
            "？",
            "?",
        ]:
            normalized = normalized.replace(marker, "")
        normalized = normalized.strip("，。？！；：、 ")

        tokens = [item.strip("，。？！；：、 ") for item in normalized.split() if item.strip()]
        if tokens:
            return tokens[:4]
        return [normalized] if normalized else []

    def _split_comparison_terms(self, text: str) -> list[str]:
        normalized = text
        for sep in ["和", "与", "及", "以及", "跟"]:
            normalized = normalized.replace(sep, "|")
        parts = [item.strip("，。？！；：、| ") for item in normalized.split("|") if item.strip("，。？！；：、| ")]
        results: list[str] = []
        for item in parts:
            if item and item not in results:
                results.append(item)
        return results[:3]

    def _filter_known_values(self, value: Any, defaults: list[str]) -> list[str]:
        allowed = set(defaults) | {
            "summary",
            "key_points",
            "formulas",
            "examples",
            "prerequisite_nodes",
            "next_nodes",
            "recommended_next_nodes",
            "requirement_level",
            "mastery_threshold",
            "importance_level",
            "assessment_focus",
            "HAS_SUBTOPIC",
            "PRE_REQUIRES",
            "LEADS_TO",
            "RECOMMENDED_NEXT",
            "RELATED_TO",
            "APPLIED_IN",
        }
        results: list[str] = []
        for item in self._clean_terms(value):
            if item in allowed and item not in results:
                results.append(item)
        return results

    def _clean_terms(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        results: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text and text not in results:
                results.append(text)
        return results

    def _default_reasoning(self, question_type: str, traversal_mode: str) -> str:
        return (
            f"Use the {traversal_mode} semantic-neighborhood profile, "
            f"expand along relations favored by {question_type}, and decay distant nodes."
        )
