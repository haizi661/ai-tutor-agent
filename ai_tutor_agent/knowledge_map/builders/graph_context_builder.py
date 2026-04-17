from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.builders.graph_traverser import TraversedNode


class GraphContextBuilder:
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
                }
            )
            for attribute in target_attributes:
                evidence_items.extend(
                    self._collect_attribute_evidence(
                        node=node,
                        attribute=attribute,
                        node_map=node_map,
                    )
                )

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

        return [
            {
                "node_id": node_id,
                "node_name": name,
                "attribute": attribute,
                "reference": f"{node_id}.{attribute}",
                "text": self._normalize_text(str(value).strip()),
            }
        ]

    def _format_attribute_item(
        self,
        attribute: str,
        item: Any,
        node_map: dict[str, dict[str, Any]],
    ) -> str:
        text = str(item).strip()
        if attribute in {"prerequisite_nodes", "next_nodes", "recommended_next_nodes"}:
            target = node_map.get(text)
            if target:
                return f"{text} | {target.get('name', '')}"
        return self._normalize_text(text)

    def _normalize_text(self, text: str, max_len: int = 180) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_len:
            return compact
        return compact[: max_len - 1].rstrip() + "..."

    def _attribute_priority(self, attribute: str) -> int:
        priority = {
            "summary": 0,
            "prerequisite_nodes": 1,
            "next_nodes": 1,
            "recommended_next_nodes": 1,
            "key_points": 2,
            "formulas": 3,
            "examples": 4,
        }
        return priority.get(attribute, 9)

    def _render_context_text(
        self,
        node_summaries: list[dict[str, Any]],
        evidence_items: list[dict[str, Any]],
    ) -> str:
        lines = ["[Subgraph Nodes]"]
        for item in node_summaries:
            lines.append(
                f"- {item['node_id']} | {item['name']} | hop={item['hop']} | "
                f"score={item['score']} | via={item['via_relation']}"
            )

        lines.append("")
        lines.append("[Node Evidence]")
        for item in evidence_items[:12]:
            lines.append(f"- [{item['reference']}] {item['text']}")

        return "\n".join(lines).strip()
