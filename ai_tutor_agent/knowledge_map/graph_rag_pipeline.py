from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.infrastructure.llm import build_llms
from ai_tutor_agent.knowledge_map.builders.graph_answer_generator_v2 import GraphAnswerGeneratorV2
from ai_tutor_agent.knowledge_map.builders.graph_context_builder import GraphContextBuilder
from ai_tutor_agent.knowledge_map.builders.graph_media_enricher import GraphMediaEnricher
from ai_tutor_agent.knowledge_map.builders.graph_query_planner_v2 import GraphQueryPlanner
from ai_tutor_agent.knowledge_map.builders.graph_traverser import GraphTraverser
from ai_tutor_agent.knowledge_map.builders.node_selector import NodeSelector
from ai_tutor_agent.knowledge_map.builders.qwen_visual_analyzer import QwenVisualAnalyzer
from ai_tutor_agent.knowledge_map.config.graph_rag_config import GraphRAGConfig


class GraphRAGPipeline:
    def __init__(
        self,
        *,
        nodes_csv_path: str = "data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
        edges_csv_path: str = "data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv",
        annotated_assets_path: str = "data/media_evidence_index/chapter03_annotated_assets.jsonl",
        enable_llm: bool = True,
        enable_visual_llm: bool = False,
        llm_profile: str | None = "qwen",
        config: GraphRAGConfig | None = None,
    ) -> None:
        self.config = config or GraphRAGConfig()
        self.nodes_csv_path = Path(nodes_csv_path)
        self.edges_csv_path = Path(edges_csv_path)
        self.nodes = self._load_nodes()
        self.edges = self._load_edges()
        self.node_map = {node["node_id"]: node for node in self.nodes}
        self.node_selector = NodeSelector()
        tutor_llm = self._build_tutor_llm(enable_llm=enable_llm, llm_profile=llm_profile)
        visual_analyzer = self._build_visual_analyzer(
            enable_llm=enable_llm and enable_visual_llm,
            llm_profile=llm_profile,
        )
        self.query_planner = GraphQueryPlanner(llm=tutor_llm, config=self.config)
        self.graph_traverser = GraphTraverser(self.edges, node_map=self.node_map, config=self.config)
        self.context_builder = GraphContextBuilder(config=self.config)
        self.media_enricher = GraphMediaEnricher(
            visual_analyzer=visual_analyzer,
            annotated_assets_path=annotated_assets_path,
        )
        self.answer_generator = GraphAnswerGeneratorV2(llm=tutor_llm)

    def ask(
        self,
        question: str,
        *,
        traversal_mode: str | None = None,
        max_depth_override: int | None = None,
    ) -> dict[str, Any]:
        plan = self.query_planner.plan(
            question,
            traversal_mode=traversal_mode,
            max_depth_override=max_depth_override,
        )
        anchor_nodes = self._select_anchor_nodes(question, plan.anchor_terms)
        traversed_nodes = self.graph_traverser.traverse(
            anchor_nodes=anchor_nodes,
            anchor_terms=plan.anchor_terms,
            question_type=plan.question_type,
            preferred_relations=plan.preferred_relations,
            max_depth=plan.max_depth,
            node_budget=plan.node_budget,
        )
        context_payload = self.context_builder.build(
            question=question,
            question_type=plan.question_type,
            traversed_nodes=traversed_nodes,
            node_map=self.node_map,
            target_attributes=plan.target_attributes,
        )
        subgraph_roles = context_payload["subgraph_roles"]
        role_map = subgraph_roles.get("node_roles", {})
        traversed_payload = [
            {
                "node_id": item.node_id,
                "hop": item.hop,
                "score": item.score,
                "via_relation": item.via_relation,
                "parent_node_id": item.parent_node_id,
                "relation_direction": item.relation_direction,
                "relation_strength": item.relation_strength,
                "edge_weight": item.edge_weight,
                "relation_note": item.relation_note,
                "edge_source_type": item.edge_source_type,
                "relation_reference": item.relation_reference,
                "name": self.node_map.get(item.node_id, {}).get("name", ""),
                "node_role": role_map.get(item.node_id, "context"),
            }
            for item in traversed_nodes
        ]
        media_items = self.media_enricher.collect_for_nodes(
            traversed_nodes=traversed_payload,
            node_map=self.node_map,
            question=question,
        )
        answer = self.answer_generator.generate(
            question=question,
            question_type=plan.question_type,
            context_text=context_payload["context_text"],
            evidence_items=context_payload["evidence_items"],
            node_summaries=context_payload["node_summaries"],
            media_items=media_items,
        )
        return {
            "question": question,
            "plan": {
                "question_type": plan.question_type,
                "anchor_terms": plan.anchor_terms,
                "target_attributes": plan.target_attributes,
                "preferred_relations": plan.preferred_relations,
                "traversal_mode": plan.traversal_mode,
                "max_depth": plan.max_depth,
                "node_budget": plan.node_budget,
                "reasoning": plan.reasoning,
                "used_llm": plan.used_llm,
            },
            "anchor_nodes": [
                {"node_id": node["node_id"], "name": node.get("name", "")}
                for node in anchor_nodes
            ],
            "traversed_nodes": traversed_payload,
            "node_summaries": context_payload["node_summaries"],
            "evidence_items": context_payload["evidence_items"],
            "subgraph_roles": subgraph_roles,
            "media_items": media_items,
            "context_text": context_payload["context_text"],
            "answer": answer,
        }

    def _build_tutor_llm(self, *, enable_llm: bool, llm_profile: str | None) -> Any | None:
        if not enable_llm:
            return None
        try:
            settings = get_settings()
            if llm_profile == "qwen" and settings.qwen_api_key:
                settings = replace(
                    settings,
                    chat_profile="qwen",
                    llm_provider="openai",
                    openai_api_key=settings.qwen_api_key,
                    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model_name="qwen-plus",
                    http_proxy=None,
                    https_proxy=None,
                )
            tutor_llm, _, _ = build_llms(settings)
            return tutor_llm
        except Exception:
            return None

    def _build_visual_analyzer(self, *, enable_llm: bool, llm_profile: str | None) -> Any | None:
        if not enable_llm:
            return None
        try:
            settings = get_settings()
            if llm_profile == "qwen" and settings.qwen_api_key:
                return QwenVisualAnalyzer(api_key=settings.qwen_api_key)
        except Exception:
            return None
        return None

    def _select_anchor_nodes(self, question: str, anchor_terms: list[str]) -> list[dict[str, Any]]:
        queries = [question] + anchor_terms
        selected: list[dict[str, Any]] = []
        for query in queries:
            node = self.node_selector.select_node(query, self.nodes)
            if node and all(existing["node_id"] != node["node_id"] for existing in selected):
                selected.append(node)
        return selected[:3]

    def _load_nodes(self) -> list[dict[str, Any]]:
        if not self.nodes_csv_path.exists():
            raise FileNotFoundError(f"节点文件不存在: {self.nodes_csv_path}")
        df = pd.read_csv(self.nodes_csv_path)
        records = df.to_dict(orient="records")
        return [self._parse_record(record) for record in records]

    def _load_edges(self) -> list[dict[str, Any]]:
        if not self.edges_csv_path.exists():
            raise FileNotFoundError(f"边文件不存在: {self.edges_csv_path}")
        df = pd.read_csv(self.edges_csv_path)
        return df.to_dict(orient="records")

    def _parse_record(self, record: dict[str, Any]) -> dict[str, Any]:
        parsed = dict(record)
        list_like_fields = [
            "tags",
            "core_concepts",
            "key_points",
            "formulas",
            "examples",
            "figures_refs",
            "page_refs",
            "definition_candidates",
            "key_point_candidates",
            "formula_candidates",
            "example_candidates",
            "prerequisite_nodes",
            "next_nodes",
            "related_nodes",
            "application_nodes",
            "recommended_next_nodes",
        ]
        for field in list_like_fields:
            parsed[field] = self._safe_parse_literal(parsed.get(field), default=[])
        parsed["extra"] = self._safe_parse_literal(parsed.get("extra"), default={})
        return parsed

    def _safe_parse_literal(self, value: Any, default: Any) -> Any:
        if isinstance(value, (list, dict)):
            return value
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        try:
            return ast.literal_eval(text)
        except Exception:
            return default
