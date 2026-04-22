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
        traversed_nodes: list[TraversedNode],
        node_map: dict[str, dict[str, Any]],
        target_attributes: list[str],
    ) -> dict[str, Any]:
        evidence_items: list[dict[str, Any]] = []
        node_summaries: list[dict[str, Any]] = []
        traversed_meta: dict[str, dict[str, Any]] = {}
        seen_references: set[str] = set()

        for traversed in traversed_nodes:
            node = node_map.get(traversed.node_id)
            if not node:
                continue

            traversed_meta[traversed.node_id] = {
                "hop": traversed.hop,
                "score": traversed.score,
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

        evidence_items.sort(
            key=lambda item: (
                traversed_meta.get(item["node_id"], {}).get("hop", 99),
                self._attribute_priority(item["attribute"]),
                -traversed_meta.get(item["node_id"], {}).get("score", 0.0),
                item["reference"],
            )
        )
        return {
            "node_summaries": node_summaries,
            "evidence_items": evidence_items,
            "context_text": self._render_context_text(node_summaries, evidence_items),
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
        node_summaries: list[dict[str, Any]],
        evidence_items: list[dict[str, Any]],
    ) -> str:
        lines = ["[Subgraph Nodes]"]
        for item in node_summaries:
            focus = str(item.get("assessment_focus", "") or "").strip()
            importance = str(item.get("importance_level", "") or "").strip()
            extras = []
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
        for item in evidence_items[:18]:
            lines.append(f"- [{item['reference']}] {item['text']}")

        return "\n".join(lines).strip()
