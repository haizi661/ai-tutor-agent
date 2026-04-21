from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from ai_tutor_agent.knowledge_map.builders.graph_relation_builder import GraphRelationBuilder
from ai_tutor_agent.knowledge_map.builders.graph_skeleton_builder import GraphSkeletonBuilder
from ai_tutor_agent.knowledge_map.builders.learning_path_builder import LearningPathBuilder
from ai_tutor_agent.knowledge_map.config.course_graph_config import COURSE_GRAPH_CONFIG, RELATION_TYPES

from ai_tutor_agent.knowledge_map.builders.node_content_enricher import NodeContentEnricher
from ai_tutor_agent.knowledge_map.config.document_config import DOCUMENT_PATHS
from ai_tutor_agent.knowledge_map.builders.node_retrieval_builder import NodeRetrievalBuilder
from ai_tutor_agent.knowledge_map.builders.vector_index_builder import VectorIndexBuilder
from ai_tutor_agent.knowledge_map.builders.node_property_generator import NodePropertyGenerator


class KnowledgeMapPipelineV2:
    """
    V2 第二阶段：
    1. 从静态课程骨架生成节点
    2. 从规则生成基础关系
    3. 回填节点内部关系字段
    4. 生成学习路径推荐
    5. 教材内容增强
    6. 候选池构建
    7. 向量索引构建
    8. 节点属性生成
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or COURSE_GRAPH_CONFIG

    def generate(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        skeleton_builder = GraphSkeletonBuilder(self.config)
        nodes = skeleton_builder.build_nodes()

        relation_builder = GraphRelationBuilder(RELATION_TYPES)
        edges = relation_builder.build_edges(nodes)

        nodes = self._populate_node_relation_fields(nodes, edges)

        learning_path_builder = LearningPathBuilder()
        nodes = learning_path_builder.build_learning_paths(nodes, edges)

        # 教材 PDF 内容增强
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

        has_source_type = (not nodes_df.empty) and ("source_type" in nodes_df.columns)
        metadata = {
            "course_name": self.config.get("course_name", ""),
            "version": self.config.get("version", "v2"),
            "node_count": len(nodes_df),
            "edge_count": len(edges_df),
            "chapter_anchor_count": int((nodes_df["source_type"] == "skeleton_chapter_anchor").sum()) if has_source_type else 0,
            "topic_count": int((nodes_df["source_type"] == "skeleton_topic").sum()) if has_source_type else 0,
            "textbook_pdf": str(DOCUMENT_PATHS.get("textbook_pdf", "")),
            "textbook_pdf_exists": bool(
                DOCUMENT_PATHS.get("textbook_pdf") and DOCUMENT_PATHS["textbook_pdf"].exists()
            ),
            "outline_pdf": str(DOCUMENT_PATHS.get("outline_pdf", "")),
            "outline_pdf_exists": bool(
                DOCUMENT_PATHS.get("outline_pdf") and DOCUMENT_PATHS["outline_pdf"].exists()
            ),
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
        根据统一边关系回填节点内部的兼容字段。
        说明：
        1. 新版图谱以边为主，不再依赖 level / part_of / HAS_SUBTOPIC。
        2. 为兼容后续 learning_path / companion / QA 逻辑，继续回填
           prerequisite_nodes / next_nodes / related_nodes / recommended_next_nodes。
        """
        node_map = {node["node_id"]: node for node in nodes}

        def _append_unique(node_id: str, field: str, value: str) -> None:
            if node_id not in node_map:
                return
            node = node_map[node_id]
            node.setdefault(field, [])
            if value not in node[field]:
                node[field].append(value)

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            relation_type = edge.get("relation_type", edge.get("relation", ""))
            direction_type = edge.get("direction_type", "undirected")

            if source not in node_map or target not in node_map:
                continue

            if relation_type == "prerequisite_of":
                _append_unique(target, "prerequisite_nodes", source)
                _append_unique(source, "next_nodes", target)
                _append_unique(source, "recommended_next_nodes", target)

            elif relation_type in {"related_to", "parallel_to", "extends_to", "easy_to_confuse_with", "weak_related_to"}:
                _append_unique(source, "related_nodes", target)
                _append_unique(source, "recommended_next_nodes", target)
                if direction_type == "undirected":
                    _append_unique(target, "related_nodes", source)
                    _append_unique(target, "recommended_next_nodes", source)
                elif relation_type == "extends_to":
                    _append_unique(source, "next_nodes", target)

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