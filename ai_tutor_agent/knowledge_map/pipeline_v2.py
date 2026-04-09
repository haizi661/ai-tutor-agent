from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from ai_tutor_agent.knowledge_map.builders.graph_relation_builder import GraphRelationBuilder
from ai_tutor_agent.knowledge_map.builders.graph_skeleton_builder import GraphSkeletonBuilder
from ai_tutor_agent.knowledge_map.config.course_graph_config import COURSE_GRAPH_CONFIG, RELATION_TYPES

from ai_tutor_agent.knowledge_map.builders.node_content_enricher import NodeContentEnricher
from ai_tutor_agent.knowledge_map.config.document_config import DOCUMENT_PATHS
from ai_tutor_agent.knowledge_map.builders.node_retrieval_builder import NodeRetrievalBuilder
from ai_tutor_agent.knowledge_map.builders.vector_index_builder import VectorIndexBuilder
from ai_tutor_agent.knowledge_map.builders.node_property_generator import NodePropertyGenerator


class KnowledgeMapPipelineV2:
    """
    V2 第一阶段：
    1. 从静态课程骨架生成节点
    2. 从规则生成基础关系
    3. 回填节点内部关系字段
    4. 导出 csv / json / graphml

    暂不做：
    - PDF 自动抽取
    - RAG 属性补全
    - 教师风格改写
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or COURSE_GRAPH_CONFIG


    def generate(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        skeleton_builder = GraphSkeletonBuilder(self.config)
        nodes = skeleton_builder.build_nodes()

        relation_builder = GraphRelationBuilder(RELATION_TYPES)
        edges = relation_builder.build_edges(nodes)

        nodes = self._populate_node_relation_fields(nodes, edges)

        # 新增：教材 PDF 内容增强
        enricher = NodeContentEnricher(
            textbook_pdf_path=DOCUMENT_PATHS.get("textbook_pdf")
        )
        nodes = enricher.enrich_nodes(nodes)

        retrieval_builder = NodeRetrievalBuilder(
            textbook_pdf_path=DOCUMENT_PATHS.get("textbook_pdf")
        )
        nodes = retrieval_builder.enrich_nodes(nodes)

        vector_index_builder = VectorIndexBuilder()
        index_summary = vector_index_builder.rebuild_from_nodes(nodes)

        property_generator = NodePropertyGenerator()
        nodes = property_generator.enrich_nodes(nodes)

        nodes_df = pd.DataFrame(nodes)
        edges_df = pd.DataFrame(edges)

        metadata = {
            "course_name": self.config.get("course_name", ""),
            "version": self.config.get("version", "v2"),
            "node_count": len(nodes_df),
            "edge_count": len(edges_df),
            "level1_count": int((nodes_df["level"] == 1).sum()) if not nodes_df.empty else 0,
            "level2_count": int((nodes_df["level"] == 2).sum()) if not nodes_df.empty else 0,
            "textbook_pdf": str(DOCUMENT_PATHS.get("textbook_pdf", "")),
            "textbook_pdf_exists": bool(DOCUMENT_PATHS.get("textbook_pdf") and DOCUMENT_PATHS["textbook_pdf"].exists()),
            "vector_collection_name": index_summary.get("collection_name", ""),
            "vector_document_count": index_summary.get("document_count", 0),
        }
        return nodes_df, edges_df, metadata

    def _populate_node_relation_fields(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        根据边信息，回填节点内部的关系属性字段。
        这样后面节点自身就带有 prerequisite_nodes / next_nodes 等信息。
        """
        node_map = {node["node_id"]: node for node in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            relation = edge["relation"]

            if source not in node_map or target not in node_map:
                continue

            if relation == "LEADS_TO":
                node_map[source]["next_nodes"].append(target)
                node_map[target]["prerequisite_nodes"].append(source)

            elif relation == "PRE_REQUIRES":
                # 这个关系已经由 LEADS_TO 反向自动补过，这里不重复写
                pass

            elif relation == "HAS_SUBTOPIC":
                parent_extra = node_map[source].setdefault("extra", {})
                parent_extra.setdefault("subtopic_nodes", [])
                parent_extra["subtopic_nodes"].append(target)

        return list(node_map.values())

    def finalize(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        output_dir: str,
        graph_name: str = "knowledge_map_v2",
    ) -> dict[str, str]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        nodes_df = nodes_df.copy()
        edges_df = edges_df.copy()

        if "keep" in nodes_df.columns:
            nodes_df = nodes_df[nodes_df["keep"] == True].copy()  # noqa: E712
        if "keep" in edges_df.columns:
            edges_df = edges_df[edges_df["keep"] == True].copy()  # noqa: E712

        valid_node_ids = set(nodes_df["node_id"].tolist())
        if not edges_df.empty:
            edges_df = edges_df[
                edges_df["source"].isin(valid_node_ids) & edges_df["target"].isin(valid_node_ids)
            ].copy()

        nodes_csv = str(output_path / f"{graph_name}_nodes.csv")
        edges_csv = str(output_path / f"{graph_name}_edges.csv")
        graphml_path = str(output_path / f"{graph_name}.graphml")
        json_path = str(output_path / f"{graph_name}.json")

        nodes_df.to_csv(nodes_csv, index=False, encoding="utf-8-sig")
        edges_df.to_csv(edges_csv, index=False, encoding="utf-8-sig")

        graph = nx.DiGraph(name=graph_name)

        for _, row in nodes_df.iterrows():
            node_attrs = self._sanitize_for_graphml(row.to_dict())
            node_id = node_attrs.pop("node_id")
            graph.add_node(node_id, **node_attrs)

        for _, row in edges_df.iterrows():
            edge_attrs = self._sanitize_for_graphml(row.to_dict())
            source = edge_attrs.pop("source")
            target = edge_attrs.pop("target")
            graph.add_edge(source, target, **edge_attrs)

        nx.write_graphml(graph, graphml_path)

        data = {
            "nodes": nodes_df.to_dict(orient="records"),
            "edges": edges_df.to_dict(orient="records"),
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "nodes_csv": nodes_csv,
            "edges_csv": edges_csv,
            "graphml": graphml_path,
            "json": json_path,
        }

    @staticmethod
    def _sanitize_for_graphml(record: dict[str, Any]) -> dict[str, Any]:
        """
        GraphML 不支持 list / dict / None 等复杂类型，
        所以导出前统一转成可写入的标量或字符串。
        """
        sanitized: dict[str, Any] = {}
        for key, value in record.items():
            sanitized[key] = KnowledgeMapPipelineV2._to_graphml_value(value)
        return sanitized

    @staticmethod
    def _to_graphml_value(value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, dict, tuple, set)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)