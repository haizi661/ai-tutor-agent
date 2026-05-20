from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.builders.graph_traverser import TraversedNode
from ai_tutor_agent.knowledge_map.config.graph_rag_config import GraphRAGConfig


class GraphContextBuilder:
    def __init__(self, config: GraphRAGConfig | None = None) -> None:
        self.config = config or GraphRAGConfig()

    def build(
        self,
        *,
        question: str,
        question_type: str,
        traversed_nodes: list[TraversedNode],
        node_map: dict[str, dict[str, Any]],
        target_attributes: list[str],
    ) -> dict[str, Any]:
        evidence_items: list[dict[str, Any]] = []
        node_summaries: list[dict[str, Any]] = []
        traversed_meta: dict[str, dict[str, Any]] = {}
        seen_references: set[str] = set()

        subgraph_roles = self._build_subgraph_roles(
            question=question,
            question_type=question_type,
            traversed_nodes=traversed_nodes,
            node_map=node_map,
        )
        role_map = subgraph_roles["node_roles"]

        for traversed in traversed_nodes:
            node = node_map.get(traversed.node_id)
            if not node:
                continue

            traversed_meta[traversed.node_id] = {
                "hop": traversed.hop,
                "score": traversed.score,
                "role_rank": self._role_rank(role_map.get(traversed.node_id, "context")),
            }
            node_summaries.append(
                {
                    "node_id": traversed.node_id,
                    "name": node.get("name", ""),
                    "hop": traversed.hop,
                    "score": traversed.score,
                    "via_relation": traversed.via_relation,
                    "parent_node_id": traversed.parent_node_id,
                    "relation_direction": traversed.relation_direction,
                    "importance_level": node.get("importance_level", ""),
                    "assessment_focus": node.get("assessment_focus", ""),
                    "relation_reference": traversed.relation_reference,
                    "relation_note": traversed.relation_note,
                    "node_role": role_map.get(traversed.node_id, "context"),
                }
            )

            for item in self._collect_relation_evidence(traversed=traversed, node_map=node_map):
                if item["reference"] in seen_references:
                    continue
                seen_references.add(item["reference"])
                evidence_items.append(item)

            for attribute in target_attributes:
                for item in self._collect_attribute_evidence(
                    node=node,
                    attribute=attribute,
                    node_map=node_map,
                ):
                    if item["reference"] in seen_references:
                        continue
                    seen_references.add(item["reference"])
                    evidence_items.append(item)

        evidence_intent = self._detect_evidence_intent(question, question_type)
        scored_items = [
            (
                self._score_evidence_item(
                    item,
                    traversed_meta=traversed_meta,
                    role_map=role_map,
                    evidence_intent=evidence_intent,
                    question=question,
                ),
                item,
            )
            for item in evidence_items
        ]
        scored_items.sort(key=lambda pair: (-pair[0], pair[1]["reference"]))
        ordered_evidence = [item for _, item in scored_items]

        return {
            "node_summaries": node_summaries,
            "evidence_items": ordered_evidence,
            "context_text": self._render_context_text(
                node_summaries=node_summaries,
                evidence_items=ordered_evidence,
                subgraph_roles=subgraph_roles,
            ),
            "subgraph_roles": subgraph_roles,
        }

    def _build_subgraph_roles(
        self,
        *,
        question: str,
        question_type: str,
        traversed_nodes: list[TraversedNode],
        node_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        del question
        node_roles: dict[str, str] = {}
        primary_nodes: list[dict[str, Any]] = []
        supporting_nodes: list[dict[str, Any]] = []
        prerequisite_nodes: list[dict[str, Any]] = []
        comparison_nodes: list[dict[str, Any]] = []
        key_paths: list[dict[str, Any]] = []

        if traversed_nodes:
            anchor = traversed_nodes[0]
            node_roles[anchor.node_id] = "primary"
            primary_nodes.append(self._node_brief(anchor, node_map, reason="anchor node selected for this query"))

        for traversed in traversed_nodes[1:]:
            role = "supporting"
            if traversed.via_relation == "prerequisite_of" and traversed.relation_direction == "reverse":
                role = "prerequisite"
                prerequisite_nodes.append(
                    self._node_brief(
                        traversed,
                        node_map,
                        reason=traversed.relation_note or "reverse prerequisite path",
                    )
                )
            elif question_type in {"comparative_query", "relation_query"} and traversed.via_relation in {
                "parallel_to",
                "weak_related_to",
            }:
                role = "comparison"
                comparison_nodes.append(
                    self._node_brief(
                        traversed,
                        node_map,
                        reason=traversed.relation_note or "comparison-supporting path",
                    )
                )
            else:
                supporting_nodes.append(
                    self._node_brief(
                        traversed,
                        node_map,
                        reason=traversed.relation_note or "supporting semantic neighbor",
                    )
                )

            node_roles[traversed.node_id] = role
            if traversed.relation_reference:
                key_paths.append(
                    {
                        "reference": traversed.relation_reference,
                        "relation": traversed.via_relation,
                        "direction": traversed.relation_direction,
                        "from_node_id": traversed.parent_node_id,
                        "from_name": traversed.parent_name
                        or node_map.get(traversed.parent_node_id or "", {}).get("name", ""),
                        "to_node_id": traversed.node_id,
                        "to_name": node_map.get(traversed.node_id, {}).get("name", ""),
                        "relation_strength": traversed.relation_strength,
                        "weight": traversed.edge_weight,
                        "note": traversed.relation_note,
                    }
                )

        return {
            "node_roles": node_roles,
            "primary_nodes": primary_nodes[:2],
            "supporting_nodes": supporting_nodes[:4],
            "prerequisite_nodes": prerequisite_nodes[:4],
            "comparison_nodes": comparison_nodes[:4],
            "key_paths": key_paths[:6],
        }

    def _node_brief(
        self,
        traversed: TraversedNode,
        node_map: dict[str, dict[str, Any]],
        *,
        reason: str,
    ) -> dict[str, Any]:
        node = node_map.get(traversed.node_id, {})
        return {
            "node_id": traversed.node_id,
            "name": node.get("name", ""),
            "hop": traversed.hop,
            "score": traversed.score,
            "via_relation": traversed.via_relation,
            "reason": reason,
        }

    def _collect_relation_evidence(
        self,
        *,
        traversed: TraversedNode,
        node_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if traversed.hop == 0 or traversed.via_relation == "ANCHOR":
            return []

        node_name = str(node_map.get(traversed.node_id, {}).get("name", "") or "").strip()
        parent_name = traversed.parent_name or str(
            node_map.get(traversed.parent_node_id or "", {}).get("name", "") or ""
        ).strip()
        direction_cn = "正向扩展" if traversed.relation_direction == "forward" else "逆向追溯"
        relation_text = (
            f"{parent_name or traversed.parent_node_id} --[{traversed.via_relation}]--> "
            f"{node_name or traversed.node_id}；方向：{direction_cn}；"
            f"关系强度={traversed.relation_strength:.2f}；边权重={traversed.edge_weight:.2f}"
        )
        if traversed.relation_note:
            relation_text += f"；说明：{traversed.relation_note}"
        if traversed.relation_evidence:
            relation_text += f"；证据：{self._normalize_text(traversed.relation_evidence, max_len=120)}"

        reference = traversed.relation_reference or (
            f"{traversed.parent_node_id or 'ROOT'}->{traversed.node_id}.{traversed.via_relation}"
        )
        return [
            {
                "node_id": traversed.node_id,
                "node_name": node_name,
                "attribute": "relation_path",
                "reference": reference,
                "text": relation_text,
            }
        ]

    def _collect_attribute_evidence(
        self,
        *,
        node: dict[str, Any],
        attribute: str,
        node_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        value = node.get(attribute)
        node_id = str(node.get("node_id", ""))
        name = str(node.get("name", ""))

        if value is None or value == "" or value == []:
            return []

        if isinstance(value, list):
            results = []
            for idx, item in enumerate(value[:4], start=1):
                text = self._format_attribute_item(attribute, item, node_map)
                if not text:
                    continue
                results.append(
                    {
                        "node_id": node_id,
                        "node_name": name,
                        "attribute": attribute,
                        "reference": f"{node_id}.{attribute}[{idx}]",
                        "text": text,
                    }
                )
            return results

        text = self._format_scalar_attribute(attribute, value)
        if not text:
            return []
        return [
            {
                "node_id": node_id,
                "node_name": name,
                "attribute": attribute,
                "reference": f"{node_id}.{attribute}",
                "text": text,
            }
        ]

    def _format_attribute_item(
        self,
        attribute: str,
        item: Any,
        node_map: dict[str, dict[str, Any]],
    ) -> str:
        text = str(item).strip()
        if not text:
            return ""
        if attribute in {
            "prerequisite_nodes",
            "next_nodes",
            "recommended_next_nodes",
            "related_nodes",
            "application_nodes",
        }:
            target = node_map.get(text)
            if target:
                return f"{text} | {target.get('name', '')}"
        return self._normalize_text(text, max_len=220)

    def _format_scalar_attribute(self, attribute: str, value: Any) -> str:
        if attribute == "mastery_threshold":
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                return self._normalize_text(str(value).strip(), max_len=220)
        return self._normalize_text(str(value).strip(), max_len=220)

    def _detect_evidence_intent(self, question: str, question_type: str) -> str:
        q = (question or "").strip()
        if question_type == "prerequisite_query":
            return "prerequisite"
        if question_type in {"comparative_query", "relation_query"}:
            return "comparison"
        if any(token in q for token in ["公式", "关系", "变化", "怎么", "为什么", "阻尼比", "超调量", "峰值"]):
            return "quantitative"
        return "general"

    def _score_evidence_item(
        self,
        item: dict[str, Any],
        *,
        traversed_meta: dict[str, dict[str, Any]],
        role_map: dict[str, str],
        evidence_intent: str,
        question: str,
    ) -> float:
        attribute = item["attribute"]
        node_meta = traversed_meta.get(item["node_id"], {})
        hop = node_meta.get("hop", 99)
        score = 20.0 - hop * 2.0
        score += node_meta.get("score", 0.0)
        score += 2.5 - self._attribute_priority(attribute)
        score += self._role_rank(role_map.get(item["node_id"], "context")) * 0.8
        score += self._question_overlap_score(question, item["text"])

        if evidence_intent == "quantitative":
            if attribute == "formulas":
                score += 5.5
            elif attribute == "relation_path":
                score += 2.5
            elif attribute == "key_points":
                score += 3.0
            elif attribute == "core_concepts":
                score -= 2.0
        elif evidence_intent == "prerequisite":
            if attribute == "relation_path":
                score += 5.5
            elif attribute == "prerequisite_nodes":
                score += 2.5
            elif attribute == "core_concepts":
                score -= 2.0
        elif evidence_intent == "comparison":
            if attribute in {"key_points", "summary", "relation_path"}:
                score += 3.0
            elif attribute == "core_concepts":
                score -= 1.2

        return score

    def _question_overlap_score(self, question: str, text: str) -> float:
        tokens = self._extract_query_tokens(question)
        if not tokens:
            return 0.0
        overlap = 0
        for token in tokens:
            if token in text:
                overlap += 1
        return overlap * 0.8

    def _extract_query_tokens(self, question: str) -> list[str]:
        text = " ".join((question or "").split())
        stop_words = {
            "什么",
            "关系",
            "如何",
            "为什么",
            "请问",
            "一个",
            "有关",
            "系统",
        }
        tokens: list[str] = []
        current = []
        for ch in text:
            if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff"):
                current.append(ch)
            else:
                if current:
                    token = "".join(current)
                    if len(token) >= 2 and token not in stop_words and token not in tokens:
                        tokens.append(token)
                    current = []
        if current:
            token = "".join(current)
            if len(token) >= 2 and token not in stop_words and token not in tokens:
                tokens.append(token)
        return tokens[:8]

    def _role_rank(self, role: str) -> int:
        order = {
            "primary": 4,
            "prerequisite": 3,
            "supporting": 2,
            "comparison": 2,
            "context": 1,
        }
        return order.get(role, 1)

    def _normalize_text(self, text: str, max_len: int = 180) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_len:
            return compact
        return compact[: max_len - 1].rstrip() + "..."

    def _attribute_priority(self, attribute: str) -> int:
        if attribute == "relation_path":
            return 1
        return self.config.evidence_attribute_priority.get(attribute, 9)

    def _render_context_text(
        self,
        *,
        node_summaries: list[dict[str, Any]],
        evidence_items: list[dict[str, Any]],
        subgraph_roles: dict[str, Any],
    ) -> str:
        lines = ["[Subgraph Roles]"]
        for label in ["primary_nodes", "prerequisite_nodes", "supporting_nodes", "comparison_nodes"]:
            items = subgraph_roles.get(label, []) or []
            if not items:
                continue
            lines.append(f"- {label}:")
            for item in items[:4]:
                lines.append(
                    f"  - {item['node_id']} | {item['name']} | hop={item['hop']} | "
                    f"score={item['score']} | reason={item['reason']}"
                )

        lines.append("")
        lines.append("[Subgraph Nodes]")
        for item in node_summaries:
            extras = []
            role = str(item.get("node_role", "") or "").strip()
            importance = str(item.get("importance_level", "") or "").strip()
            focus = str(item.get("assessment_focus", "") or "").strip()
            if role:
                extras.append(f"role={role}")
            if importance:
                extras.append(f"importance={importance}")
            if focus:
                extras.append(f"assessment_focus={focus}")
            extras_blob = f" | {' | '.join(extras)}" if extras else ""
            lines.append(
                f"- {item['node_id']} | {item['name']} | hop={item['hop']} | "
                f"score={item['score']} | via={item['via_relation']}{extras_blob}"
            )

        lines.append("")
        lines.append("[Node Evidence]")
        for item in evidence_items[:16]:
            lines.append(f"- [{item['reference']}] {item['text']}")

        return "\n".join(lines).strip()
