from __future__ import annotations

import itertools
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import networkx as nx
import pandas as pd
from pyvis.network import Network

try:
    import jieba.analyse as jieba_analyse
except Exception:  # pragma: no cover
    jieba_analyse = None


CHAPTER_PATTERNS = [
    re.compile(r"^\s*(第[一二三四五六七八九十百千0-9]+[章节篇][^\n]{0,40})\s*$"),
    re.compile(r"^\s*(chapter\s+\d+[^\n]{0,40})\s*$", re.IGNORECASE),
]

COMMON_STOPWORDS = {
    "我们",
    "你们",
    "他们",
    "这个",
    "那个",
    "这些",
    "那些",
    "进行",
    "通过",
    "以及",
    "如果",
    "因此",
    "可以",
    "需要",
    "具有",
    "一个",
    "一种",
    "方法",
    "系统",
    "模型",
    "问题",
    "分析",
    "研究",
    "理论",
    "课程",
}

GENERIC_LOW_VALUE_TERMS = {
    "输入",
    "输出",
    "状态",
    "响应",
    "函数",
    "系统",
    "模型",
    "方法",
    "理论",
    "分析",
    "问题",
    "参数",
    "过程",
    "信号",
    "变量",
    "结构",
    "特性",
    "结果",
    "条件",
}

DOMAIN_SUFFIX_PATTERNS = (
    "控制",
    "控制器",
    "控制系统",
    "传递函数",
    "状态空间",
    "状态方程",
    "微分方程",
    "差分方程",
    "根轨迹",
    "稳定性",
    "可控性",
    "可观性",
    "校正",
    "补偿",
    "频率特性",
    "频域",
    "时域",
    "鲁棒性",
    "最优控制",
)

DOMAIN_TERM_REGEX = re.compile(
    r"([\u4e00-\u9fffA-Za-z0-9]{2,16}"
    r"(?:控制器|控制系统|传递函数|状态空间|状态方程|微分方程|差分方程|根轨迹|稳定性|可控性|可观性|校正|补偿|频率特性|最优控制|鲁棒控制|闭环系统|开环系统))"
)

ACTION_PREFIXES = (
    "用",
    "将",
    "把",
    "由",
    "令",
    "取",
    "求",
    "设",
    "试",
    "根据",
    "利用",
    "为了",
    "通过",
)

ACTION_TOKENS = (
    "进行",
    "实现",
    "代入",
    "推导",
    "计算",
    "确定",
    "验证",
    "得到",
    "可得",
    "作为",
    "选取",
)

FOUNDATION_HINTS = (
    "基本概念",
    "原理",
    "基础",
    "模型",
    "方程",
    "传递函数",
    "状态空间",
    "稳定性",
    "可控性",
    "可观性",
)

ADVANCED_HINTS = (
    "校正",
    "补偿",
    "最优控制",
    "鲁棒",
    "综合",
    "离散",
    "非线性",
    "数字控制",
)

METHOD_HINTS = (
    "方法",
    "根轨迹",
    "校正",
    "补偿",
    "设计",
    "控制器",
    "算法",
)

OBJECTIVE_HINTS = (
    "稳定性",
    "性能",
    "控制系统",
    "最优控制",
    "状态空间",
    "传递函数",
    "可控性",
    "可观性",
)

DOMAIN_ANCHORS = (
    "控制",
    "系统",
    "状态",
    "传递",
    "校正",
    "根轨迹",
    "稳定",
    "离散",
    "非线性",
    "最优",
)

NOISY_EXACT_TERMS = {
    "自动控制原理",
    "目录",
    "本书",
    "主编",
    "作者",
    "rank",
    "chapter",
    "figure",
    "table",
}

OUTLINE_WEIGHT_KEYWORDS = [
    ("熟练掌握", 0.20),
    ("重点掌握", 0.18),
    ("掌握", 0.14),
    ("理解与掌握", 0.12),
    ("理解和掌握", 0.12),
    ("理解并掌握", 0.12),
    ("理解", 0.10),
    ("了解", 0.06),
]

GENERIC_MATCH_FRAGMENTS = {
    "控制系统",
    "传递函数",
    "闭环传递",
    "开环传递",
    "控制器",
    "根轨迹",
    "状态空间",
}

NOISY_TERM_REGEX = [
    re.compile(r"^第[一二三四五六七八九十百千0-9]+[章节篇].*"),
    re.compile(r"^图\s*\d+[-－]\d+.*"),
    re.compile(r"^表\s*\d+[-－]\d+.*"),
    re.compile(r".*(普通高等教育|国家级规划教材).*"),
    re.compile(r"^(设|试|求|已知|根据|利用|令|取|若|当|请|由|证明).{0,20}$"),
    re.compile(r".*(将此|代入|由此|可得|其中|使得|试确定|试求|求得|作为|为最小|下式|如下|记为).*"),
]

SENTENCE_NOISE_TOKENS = {
    "将此",
    "代入",
    "由此",
    "可得",
    "其中",
    "使得",
    "试确定",
    "试求",
    "求得",
    "作为",
    "为最小",
    "记为",
    "下式",
    "如下",
}


@dataclass
class PageChunk:
    page: int
    chapter: str
    text: str


class PDFKnowledgeGraphBuilder:
    def __init__(
        self,
        min_nodes: int = 50,
        max_nodes: int = 100,
        top_terms_per_chapter: int = 28,
    ) -> None:
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.top_terms_per_chapter = top_terms_per_chapter

    def generate(self, pdf_path: str) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        page_texts = self._read_pdf(pdf_path)
        chapter_map = self._detect_chapters(page_texts)
        chunks = self._build_chunks(page_texts, chapter_map)

        concept_pool = self._extract_concepts(chunks)
        target_nodes = self._choose_node_count(len(concept_pool))
        selected = sorted(concept_pool.items(), key=lambda x: x[1]["score"], reverse=True)[:target_nodes]

        nodes_df = self._build_nodes_df(selected)
        edges_df = self._build_edges_df(selected)

        metadata = {
            "pdf_path": pdf_path,
            "pages": len(page_texts),
            "chapters": len(set(ch.chapter for ch in chunks)),
            "candidate_concepts": len(concept_pool),
            "selected_nodes": len(nodes_df),
            "selected_edges": len(edges_df),
            "jieba_enabled": bool(jieba_analyse),
        }
        return nodes_df, edges_df, metadata

    def finalize(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        output_dir: str,
        graph_name: str = "knowledge_graph",
    ) -> dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)

        if "keep" in nodes_df.columns:
            nodes_df = nodes_df[nodes_df["keep"] == True].copy()  # noqa: E712
        if "keep" in edges_df.columns:
            edges_df = edges_df[edges_df["keep"] == True].copy()  # noqa: E712

        valid_node_ids = set(nodes_df["node_id"].tolist())
        edges_df = edges_df[
            edges_df["source"].isin(valid_node_ids) & edges_df["target"].isin(valid_node_ids)
        ].copy()

        graph = nx.MultiDiGraph(name=graph_name)
        for _, row in nodes_df.iterrows():
            node_attrs = {
                "label": row["label"],
                "chapters": row["chapters"],
                "pages": row["pages"],
                "confidence": float(row["confidence"]),
                "evidence": row.get("evidence", ""),
            }
            for optional_col in ("weight", "weight_bonus", "weight_reason", "outline_hits", "outline_keywords"):
                if optional_col in row and pd.notna(row.get(optional_col)):
                    node_attrs[optional_col] = row.get(optional_col)

            graph.add_node(
                row["node_id"],
                **node_attrs,
            )

        for _, row in edges_df.iterrows():
            graph.add_edge(
                row["source"],
                row["target"],
                relation=row["relation"],
                weight=float(row["weight"]),
                confidence=float(row["confidence"]),
                chapter=row.get("chapter", ""),
                evidence=row.get("evidence", ""),
            )

        nodes_csv = os.path.join(output_dir, f"{graph_name}_nodes.csv")
        edges_csv = os.path.join(output_dir, f"{graph_name}_edges.csv")
        graphml_path = os.path.join(output_dir, f"{graph_name}.graphml")
        json_path = os.path.join(output_dir, f"{graph_name}.json")
        html_path = os.path.join(output_dir, f"{graph_name}.html")

        nodes_df.to_csv(nodes_csv, index=False, encoding="utf-8-sig")
        edges_df.to_csv(edges_csv, index=False, encoding="utf-8-sig")
        nx.write_graphml(graph, graphml_path)

        data = {
            "nodes": [
                {"id": n, **attrs}
                for n, attrs in graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **attrs}
                for u, v, attrs in graph.edges(data=True)
            ],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._render_html(graph, html_path)

        return {
            "nodes_csv": nodes_csv,
            "edges_csv": edges_csv,
            "graphml": graphml_path,
            "json": json_path,
            "html": html_path,
        }

    def annotate_node_weights_from_outline(
        self,
        nodes_df: pd.DataFrame,
        outline_pdf_path: str,
        *,
        base_weight_col: str = "confidence",
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        if nodes_df.empty:
            return nodes_df.copy(), {
                "outline_pdf": outline_pdf_path,
                "total_nodes": 0,
                "boosted_nodes": 0,
                "mentioned_nodes": 0,
                "unchanged_nodes": 0,
                "avg_bonus": 0.0,
            }

        if not os.path.exists(outline_pdf_path):
            raise FileNotFoundError(f"Outline PDF not found: {outline_pdf_path}")

        outline_pages = self._read_pdf(outline_pdf_path)
        outline_text = "\n".join(outline_pages)
        outline_sentences = self._split_sentences(outline_text)
        keyword_hits_by_sentence = [
            self._keywords_in_text(sentence)
            for sentence in outline_sentences
        ]

        weighted = nodes_df.copy()
        if base_weight_col not in weighted.columns:
            weighted[base_weight_col] = 0.5

        weight_values: list[float] = []
        bonus_values: list[float] = []
        boosted_count = 0
        mentioned_count = 0

        for idx, row in weighted.iterrows():
            label = str(row.get("label", "")).strip()
            base_weight = self._clamp01(row.get(base_weight_col, 0.5))

            aliases = self._build_label_aliases(label)
            hit_indexes = [
                sent_idx
                for sent_idx, sentence in enumerate(outline_sentences)
                if self._text_matches_aliases(sentence, aliases)
            ]
            hits = [outline_sentences[sent_idx] for sent_idx in hit_indexes]
            matched_keywords: set[str] = set()
            best_delta = 0.0

            for sent_idx in hit_indexes:
                window_start = max(0, sent_idx - 1)
                window_end = min(len(outline_sentences), sent_idx + 2)
                for nearby_idx in range(window_start, window_end):
                    for keyword in keyword_hits_by_sentence[nearby_idx]:
                        matched_keywords.add(keyword)

            for keyword, delta in OUTLINE_WEIGHT_KEYWORDS:
                if keyword in matched_keywords:
                    best_delta = max(best_delta, delta)

            if hits:
                mentioned_count += 1

            mention_bonus = 0.0
            if best_delta > 0:
                # 同一知识点在大纲中多次被提及时，给予小幅累积增益。
                mention_bonus = min(0.06, 0.02 * max(0, len(hits) - 1))

            total_bonus = best_delta + mention_bonus
            new_weight = self._clamp01(base_weight + total_bonus)

            if total_bonus > 0:
                boosted_count += 1
                reason = (
                    f"base={base_weight:.3f}; +keyword={best_delta:.3f}; "
                    f"+mention={mention_bonus:.3f}; hits={len(hits)}; "
                    f"keywords={','.join(sorted(matched_keywords))}"
                )
            elif hits:
                reason = f"base={base_weight:.3f}; outline_mentioned_without_weight_keyword; hits={len(hits)}"
            else:
                reason = f"base={base_weight:.3f}; not_mentioned_in_outline"

            weighted.at[idx, "weight"] = round(new_weight, 4)
            weighted.at[idx, "weight_bonus"] = round(total_bonus, 4)
            weighted.at[idx, "outline_hits"] = int(len(hits))
            weighted.at[idx, "outline_keywords"] = ",".join(sorted(matched_keywords))
            weighted.at[idx, "weight_reason"] = reason

            weight_values.append(new_weight)
            bonus_values.append(total_bonus)

        unchanged_nodes = int(len(weighted) - boosted_count)
        summary = {
            "outline_pdf": outline_pdf_path,
            "total_nodes": int(len(weighted)),
            "boosted_nodes": int(boosted_count),
            "mentioned_nodes": int(mentioned_count),
            "unchanged_nodes": unchanged_nodes,
            "avg_weight": round(sum(weight_values) / max(1, len(weight_values)), 4),
            "avg_bonus": round(sum(bonus_values) / max(1, len(bonus_values)), 4),
            "base_weight_col": base_weight_col,
        }
        return weighted, summary

    def _read_pdf(self, pdf_path: str) -> list[str]:
        page_texts: list[str] = []
        with fitz.open(pdf_path) as doc:
            for i in range(len(doc)):
                page = doc[i]
                text = page.get_text("text") or ""
                normalized = self._normalize_text(text)
                page_texts.append(normalized)
        return page_texts

    def _detect_chapters(self, page_texts: list[str]) -> dict[int, str]:
        chapter_map: dict[int, str] = {}
        current = "未分章"

        for i, text in enumerate(page_texts, start=1):
            head_lines = [line.strip() for line in text.splitlines()[:12] if line.strip()]
            found = None
            for line in head_lines:
                for pattern in CHAPTER_PATTERNS:
                    m = pattern.match(line)
                    if m:
                        found = m.group(1).strip()
                        break
                if found:
                    break
            if found:
                current = found
            chapter_map[i] = current

        if len(set(chapter_map.values())) <= 1 and len(page_texts) > 20:
            # Fallback: split pages into pseudo chapters when headings are not detectable.
            chunk_size = max(8, len(page_texts) // 8)
            for i in range(1, len(page_texts) + 1):
                idx = ((i - 1) // chunk_size) + 1
                chapter_map[i] = f"分段章节 {idx}"

        return chapter_map

    def _build_chunks(self, page_texts: list[str], chapter_map: dict[int, str]) -> list[PageChunk]:
        chunks: list[PageChunk] = []
        for i, text in enumerate(page_texts, start=1):
            if not text.strip():
                continue
            chunks.append(PageChunk(page=i, chapter=chapter_map.get(i, "未分章"), text=text))
        return chunks

    def _extract_concepts(self, chunks: list[PageChunk]) -> dict[str, dict[str, Any]]:
        concept_pool: dict[str, dict[str, Any]] = {}

        chapter_text: dict[str, list[str]] = defaultdict(list)
        chapter_pages: dict[str, set[int]] = defaultdict(set)
        for ch in chunks:
            chapter_text[ch.chapter].append(ch.text)
            chapter_pages[ch.chapter].add(ch.page)

        for chapter, parts in chapter_text.items():
            text = "\n".join(parts)
            terms = self._extract_terms(text, top_k=self.top_terms_per_chapter)
            evidence_sentences = self._split_sentences(text)

            for rank, (term, score) in enumerate(terms, start=1):
                if term not in concept_pool:
                    concept_pool[term] = {
                        "score": 0.0,
                        "chapters": set(),
                        "pages": set(),
                        "evidence": "",
                    }

                concept_pool[term]["score"] += float(score) + (0.02 * (self.top_terms_per_chapter - rank))
                concept_pool[term]["chapters"].add(chapter)
                concept_pool[term]["pages"].update(chapter_pages[chapter])

                if not concept_pool[term]["evidence"]:
                    concept_pool[term]["evidence"] = self._find_evidence(term, evidence_sentences)

        total_chapters = max(1, len(chapter_text))
        return self._refine_concept_pool(concept_pool, total_chapters)

    def _refine_concept_pool(
        self,
        concept_pool: dict[str, dict[str, Any]],
        total_chapters: int,
    ) -> dict[str, dict[str, Any]]:
        cleaned: list[tuple[str, dict[str, Any]]] = []
        for term, payload in concept_pool.items():
            if not self._is_effective_concept(term, payload, total_chapters):
                continue
            cleaned.append((term, payload))

        cleaned.sort(key=lambda x: (x[1]["score"], len(x[0])), reverse=True)

        # Prefer longer technical terms and suppress overly short substrings.
        kept: list[tuple[str, dict[str, Any]]] = []
        for term, payload in cleaned:
            term_len = len(term)
            shadowed = False
            for kept_term, _ in kept:
                if term == kept_term:
                    shadowed = True
                    break
                if term in kept_term and term_len <= 3:
                    shadowed = True
                    break
                if term in kept_term and payload["score"] <= 0.85 * concept_pool[kept_term]["score"]:
                    shadowed = True
                    break
            if not shadowed:
                kept.append((term, payload))

        return {term: payload for term, payload in kept}

    def _build_nodes_df(self, selected: list[tuple[str, dict[str, Any]]]) -> pd.DataFrame:
        rows = []
        max_score = max((item[1]["score"] for item in selected), default=1.0)

        for i, (term, payload) in enumerate(selected, start=1):
            node_id = f"K{i:03d}"
            confidence = round(min(1.0, payload["score"] / max_score), 4)
            rows.append(
                {
                    "keep": True,
                    "node_id": node_id,
                    "label": term,
                    "chapters": " | ".join(sorted(payload["chapters"])),
                    "pages": ",".join(str(p) for p in sorted(payload["pages"])),
                    "confidence": confidence,
                    "evidence": payload["evidence"],
                }
            )

        return pd.DataFrame(rows)

    def _build_edges_df(self, selected: list[tuple[str, dict[str, Any]]]) -> pd.DataFrame:
        filtered_selected = [
            (term, payload) for term, payload in selected if not self._is_action_phrase(term)
        ]

        node_map = {term: f"K{i:03d}" for i, (term, _) in enumerate(filtered_selected, start=1)}
        edge_weights: dict[tuple[str, str, str, str], float] = defaultdict(float)
        score_map = {term: float(payload.get("score", 0.0)) for term, payload in filtered_selected}

        # same_chapter relation
        chapter_terms: dict[str, list[str]] = defaultdict(list)
        for term, payload in filtered_selected:
            for ch in payload["chapters"]:
                chapter_terms[ch].append(term)

        for chapter, terms in chapter_terms.items():
            terms = sorted(set(terms), key=lambda t: score_map.get(t, 0.0), reverse=True)
            if len(terms) < 2:
                continue

            # Reduce dense clique: connect each term to its top related neighbors only.
            focus_terms = terms[:24]
            for i, a in enumerate(focus_terms):
                candidates: list[tuple[float, str]] = []
                for b in focus_terms[i + 1 :]:
                    rel_score = self._term_relatedness(a, b)
                    if rel_score <= 0.0:
                        continue
                    candidates.append((rel_score, b))

                candidates.sort(key=lambda x: x[0], reverse=True)
                for rel_score, b in candidates[:4]:
                    key = (a, b, "same_chapter", chapter)
                    edge_weights[key] += round(rel_score, 3)

        # lexical parent-child relation (simple but robust heuristic)
        selected_terms = [term for term, _ in filtered_selected]
        for a, b in itertools.combinations(selected_terms, 2):
            if len(a) >= 4 and a in b:
                edge_weights[(b, a, "subtopic_of", "lexical")] += 1.0
            elif len(b) >= 4 and b in a:
                edge_weights[(a, b, "subtopic_of", "lexical")] += 1.0

        # richer pedagogical relations
        payload_map = {term: payload for term, payload in filtered_selected}
        for a, b in itertools.combinations(selected_terms, 2):
            pa = payload_map[a]
            pb = payload_map[b]

            chapter_a = self._chapter_order_key(pa.get("chapters", set()))
            chapter_b = self._chapter_order_key(pb.get("chapters", set()))

            # prerequisite_of: foundational concept tends to precede advanced concept.
            if self._is_foundation_term(a) and self._is_advanced_term(b) and self._share_domain(a, b):
                if chapter_a < chapter_b:
                    edge_weights[(a, b, "prerequisite_of", f"{chapter_a}->{chapter_b}")] += 1.0
            if self._is_foundation_term(b) and self._is_advanced_term(a) and self._share_domain(a, b):
                if chapter_b < chapter_a:
                    edge_weights[(b, a, "prerequisite_of", f"{chapter_b}->{chapter_a}")] += 1.0

            # method_for: method term serves objective term in overlapping chapter context.
            shared_ch = pa.get("chapters", set()) & pb.get("chapters", set())
            if shared_ch:
                shared_chapter = sorted(shared_ch)[0]
                if self._is_method_term(a) and self._is_objective_term(b) and a != b:
                    edge_weights[(a, b, "method_for", shared_chapter)] += 1.0
                if self._is_method_term(b) and self._is_objective_term(a) and a != b:
                    edge_weights[(b, a, "method_for", shared_chapter)] += 1.0

            # part_of: component relation commonly seen in control courses.
            if "控制器" in a and "控制系统" in b:
                edge_weights[(a, b, "part_of", "component")] += 1.0
            if "控制器" in b and "控制系统" in a:
                edge_weights[(b, a, "part_of", "component")] += 1.0

            # contrasts_with: common conceptual contrasts in learning.
            if self._is_contrast_pair(a, b):
                left, right = (a, b) if a <= b else (b, a)
                edge_weights[(left, right, "contrasts_with", "concept_pair")] += 1.0

        rows = []
        for (src_term, dst_term, relation, chapter), weight in edge_weights.items():
            if src_term == dst_term:
                continue
            src = node_map[src_term]
            dst = node_map[dst_term]
            confidence_map = {
                "same_chapter": 0.88,
                "subtopic_of": 0.76,
                "prerequisite_of": 0.74,
                "method_for": 0.72,
                "part_of": 0.80,
                "contrasts_with": 0.78,
            }
            confidence = confidence_map.get(relation, 0.70)
            rows.append(
                {
                    "keep": True,
                    "source": src,
                    "target": dst,
                    "source_label": src_term,
                    "target_label": dst_term,
                    "relation": relation,
                    "chapter": chapter,
                    "weight": round(weight, 3),
                    "confidence": confidence,
                    "evidence": f"{relation}:{chapter}",
                }
            )

        edges_df = pd.DataFrame(rows)
        if edges_df.empty:
            return pd.DataFrame(
                columns=[
                    "keep",
                    "source",
                    "target",
                    "source_label",
                    "target_label",
                    "relation",
                    "chapter",
                    "weight",
                    "confidence",
                    "evidence",
                ]
            )

        edges_df = self._balance_edges(edges_df)
        edges_df = edges_df.sort_values(by=["relation", "weight"], ascending=[True, False]).reset_index(drop=True)
        return edges_df

    def _balance_edges(self, edges_df: pd.DataFrame) -> pd.DataFrame:
        # Keep learning-logic relations denser than chapter-cooccurrence relations.
        relation_cap = {
            "same_chapter": 6,
            "method_for": 8,
            "prerequisite_of": 8,
            "part_of": 6,
            "contrasts_with": 6,
            "subtopic_of": 5,
        }

        keep_idx: list[int] = []
        grouped = edges_df.sort_values(by=["confidence", "weight"], ascending=[False, False]).groupby(
            ["source", "relation"], sort=False
        )
        for (_, relation), group in grouped:
            cap = relation_cap.get(relation, 5)
            keep_idx.extend(group.head(cap).index.tolist())

        out = edges_df.loc[sorted(set(keep_idx))].copy()

        # Global cap for same_chapter to avoid swamping pedagogical relations.
        non_same = out[out["relation"] != "same_chapter"]
        same = out[out["relation"] == "same_chapter"].sort_values(by=["weight", "confidence"], ascending=False)
        max_same = max(80, int(len(non_same) * 0.9))
        same = same.head(max_same)

        return pd.concat([non_same, same], ignore_index=True)

    @staticmethod
    def _has_any(term: str, hints: tuple[str, ...]) -> bool:
        return any(h in term for h in hints)

    def _is_foundation_term(self, term: str) -> bool:
        return self._has_any(term, FOUNDATION_HINTS)

    def _is_advanced_term(self, term: str) -> bool:
        return self._has_any(term, ADVANCED_HINTS)

    def _is_method_term(self, term: str) -> bool:
        return self._has_any(term, METHOD_HINTS)

    def _is_objective_term(self, term: str) -> bool:
        return self._has_any(term, OBJECTIVE_HINTS)

    def _share_domain(self, a: str, b: str) -> bool:
        return any(anchor in a and anchor in b for anchor in DOMAIN_ANCHORS)

    def _term_relatedness(self, a: str, b: str) -> float:
        if a == b:
            return 0.0

        score = 0.0
        if self._share_domain(a, b):
            score += 0.8

        token_a = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}", a))
        token_b = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}", b))
        if token_a and token_b:
            jaccard = len(token_a & token_b) / max(1, len(token_a | token_b))
            score += 0.9 * jaccard

        if ("传递函数" in a and "传递函数" in b) or ("状态空间" in a and "状态空间" in b):
            score += 0.4

        # keep only meaningful chapter edges
        if score < 0.35:
            return 0.0
        return min(1.8, score)

    @staticmethod
    def _is_contrast_pair(a: str, b: str) -> bool:
        def contains_concept(term: str, concept: str) -> bool:
            if concept == "线性":
                return ("线性" in term) and ("非线性" not in term)
            if concept == "稳定":
                return ("稳定" in term) and ("不稳定" not in term)
            return concept in term

        pairs = [
            ("开环", "闭环"),
            ("连续", "离散"),
            ("线性", "非线性"),
            ("稳定", "不稳定"),
        ]
        for left, right in pairs:
            if (contains_concept(a, left) and contains_concept(b, right)) or (
                contains_concept(a, right) and contains_concept(b, left)
            ):
                return True
        return False

    @staticmethod
    def _chapter_order_key(chapters: set[str]) -> int:
        if not chapters:
            return 999
        nums: list[int] = []
        for ch in chapters:
            text = str(ch)
            m = re.search(r"分段章节\s*(\d+)", text)
            if m:
                nums.append(int(m.group(1)))
                continue
            m = re.search(r"第\s*(\d+)\s*章", text)
            if m:
                nums.append(int(m.group(1)))
                continue
        if nums:
            return min(nums)
        return 999

    def _extract_terms(self, text: str, top_k: int) -> list[tuple[str, float]]:
        scored_terms: dict[str, float] = defaultdict(float)

        if jieba_analyse is not None:
            textrank_terms = jieba_analyse.textrank(text, topK=top_k * 6, withWeight=True)
            for term, score in textrank_terms:
                t = self._normalize_term_candidate(term)
                if self._valid_term(t):
                    scored_terms[t] += float(score) * 1.0

            tfidf_terms = jieba_analyse.extract_tags(text, topK=top_k * 6, withWeight=True)
            for term, score in tfidf_terms:
                t = self._normalize_term_candidate(term)
                if self._valid_term(t):
                    scored_terms[t] += float(score) * 0.55

        for term in DOMAIN_TERM_REGEX.findall(text):
            t = self._normalize_term_candidate(term)
            if self._valid_term(t):
                scored_terms[t] += 1.2

        # Fallback/augmentation without jieba: regex-based frequent terms.
        candidates = re.findall(r"[\u4e00-\u9fffA-Za-z]{3,24}", text)
        for c in candidates:
            t = self._normalize_term_candidate(c)
            if self._valid_term(t):
                scored_terms[t] += 0.08

        ranked = sorted(
            ((term, score * self._term_quality_boost(term)) for term, score in scored_terms.items()),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:top_k]

    def _term_quality_boost(self, term: str) -> float:
        term_len = len(term)
        boost = 1.0

        if term_len <= 2:
            boost *= 0.22
        elif term_len == 3:
            boost *= 0.72
        elif 4 <= term_len <= 12:
            boost *= 1.35
        elif term_len > 18:
            boost *= 0.85

        if term in GENERIC_LOW_VALUE_TERMS:
            boost *= 0.15

        if any(suffix in term for suffix in DOMAIN_SUFFIX_PATTERNS):
            boost *= 1.45

        if re.search(r"[A-Za-z]{4,}", term):
            boost *= 0.92

        return boost

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.replace("\u3000", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[。！？.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _find_evidence(term: str, sentences: list[str]) -> str:
        for sent in sentences:
            if term in sent:
                return sent[:180]
        return ""

    def _valid_term(self, term: str) -> bool:
        term = term.strip()
        if len(term) < 2 or len(term) > 20:
            return False
        if term.lower() in NOISY_EXACT_TERMS:
            return False
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,20}", term):
            return False
        if term in NOISY_EXACT_TERMS:
            return False
        for pattern in NOISY_TERM_REGEX:
            if pattern.match(term):
                return False
        if term.lower() in COMMON_STOPWORDS:
            return False
        if re.fullmatch(r"[0-9\.\-]+", term):
            return False
        if re.search(r"[0-9]", term) and len(re.sub(r"[^0-9]", "", term)) >= 4:
            return False
        if term in COMMON_STOPWORDS:
            return False
        if len(term) >= 14 and not any(suffix in term for suffix in DOMAIN_SUFFIX_PATTERNS):
            return False
        if len(term) >= 6 and any(token in term for token in SENTENCE_NOISE_TOKENS):
            return False
        if term.startswith(("设", "试", "求", "已知", "根据", "利用", "若", "当", "请", "由")) and not any(
            suffix in term for suffix in DOMAIN_SUFFIX_PATTERNS
        ):
            return False
        if re.search(r"[\u4e00-\u9fff]", term) and len(term) == 2 and term in GENERIC_LOW_VALUE_TERMS:
            return False
        if re.fullmatch(r"[A-Za-z]{1,3}", term):
            return False
        return True

    @staticmethod
    def _normalize_term_candidate(term: str) -> str:
        t = (term or "").strip()
        t = re.sub(r"^[\-·•\s]+|[\-·•\s]+$", "", t)
        t = re.sub(r"[\n\r\t]+", " ", t)
        t = re.sub(r"\s+", " ", t)
        return t

    def _is_effective_concept(self, term: str, payload: dict[str, Any], total_chapters: int) -> bool:
        term_len = len(term)
        chapters = payload.get("chapters", set())
        chapter_coverage = len(chapters) / max(1, total_chapters)

        if self._is_action_phrase(term):
            return False

        if term in GENERIC_LOW_VALUE_TERMS and term_len <= 3:
            return False

        if term_len <= 2:
            return False

        if term_len <= 3 and chapter_coverage >= 0.75 and not any(suffix in term for suffix in DOMAIN_SUFFIX_PATTERNS):
            return False

        if re.fullmatch(r"[\u4e00-\u9fff]{2,3}", term) and payload.get("score", 0.0) < 0.45:
            return False

        # Prefer noun-like technical terms: require common technical suffix when term is long.
        if term_len >= 10 and not any(suffix in term for suffix in DOMAIN_SUFFIX_PATTERNS):
            return False

        return True

    def _is_action_phrase(self, term: str) -> bool:
        t = (term or "").strip()
        if not t:
            return True

        if any(t.startswith(prefix) for prefix in ACTION_PREFIXES):
            return True

        if any(token in t for token in ACTION_TOKENS):
            return True

        # Phrases ending with particles are typically sentence fragments, not concepts.
        if t.endswith(("的", "了", "着", "吗", "呢", "吧")):
            return True

        return False

    def _choose_node_count(self, candidate_count: int) -> int:
        if candidate_count <= 0:
            return 0
        if candidate_count < self.min_nodes:
            return candidate_count
        return min(self.max_nodes, max(self.min_nodes, candidate_count // 2))

    @staticmethod
    def _render_html(graph: nx.MultiDiGraph, html_path: str) -> None:
        net = Network(height="820px", width="100%", directed=True, bgcolor="#ffffff", font_color="#222222")
        net.force_atlas_2based(gravity=-40, central_gravity=0.015, spring_length=170, spring_strength=0.04)

        for node_id, attrs in graph.nodes(data=True):
            title = (
                f"知识点: {attrs.get('label', '')}<br>"
                f"章节: {attrs.get('chapters', '')}<br>"
                f"页码: {attrs.get('pages', '')}<br>"
                f"置信度: {attrs.get('confidence', '')}<br>"
                f"课程大纲权重: {attrs.get('weight', '')}<br>"
                f"权重增量: {attrs.get('weight_bonus', '')}<br>"
                f"证据: {attrs.get('evidence', '')}"
            )
            net.add_node(node_id, label=attrs.get("label", node_id), title=title)

        for source, target, attrs in graph.edges(data=True):
            title = (
                f"关系: {attrs.get('relation', '')}<br>"
                f"章节: {attrs.get('chapter', '')}<br>"
                f"权重: {attrs.get('weight', '')}<br>"
                f"置信度: {attrs.get('confidence', '')}<br>"
                f"证据: {attrs.get('evidence', '')}"
            )
            net.add_edge(source, target, label=attrs.get("relation", ""), title=title, value=attrs.get("weight", 1.0))

        Path(html_path).parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(html_path)

    @staticmethod
    def _clamp01(value: Any, default: float = 0.5) -> float:
        try:
            numeric = float(value)
        except Exception:
            numeric = default
        return max(0.0, min(1.0, numeric))

    @staticmethod
    def _keywords_in_text(text: str) -> set[str]:
        return {keyword for keyword, _ in OUTLINE_WEIGHT_KEYWORDS if keyword in text}

    @staticmethod
    def _normalize_match_text(text: str) -> str:
        normalized = re.sub(r"[\s\u3000]+", "", text or "")
        normalized = re.sub(r"[：:，,。；;、（）()【】\[\]《》<>\-—]+", "", normalized)
        return normalized

    def _build_label_aliases(self, label: str) -> list[str]:
        raw = (label or "").strip()
        if not raw:
            return []

        aliases: set[str] = {raw}
        base = raw.replace("系统的", "").replace("的", "")
        aliases.add(base)

        normalized_aliases = {
            self._normalize_match_text(item)
            for item in aliases
            if len(self._normalize_match_text(item)) >= 2
        }
        # 避免 2 字过短词导致误匹配，保留长度 >=3 的优先匹配别名。
        return sorted(normalized_aliases, key=len, reverse=True)

    def _text_matches_aliases(self, text: str, aliases: list[str]) -> bool:
        if not aliases:
            return False
        normalized_text = self._normalize_match_text(text)
        if not normalized_text:
            return False

        for alias in aliases:
            if len(alias) >= 3 and alias in normalized_text:
                return True

        # 兜底: 对较长知识点允许共享连续子串命中，缓解表述差异。
        for alias in aliases:
            if len(alias) < 6:
                continue
            for i in range(0, len(alias) - 4):
                frag = alias[i : i + 5]
                if frag in GENERIC_MATCH_FRAGMENTS:
                    continue
                if frag in normalized_text:
                    return True

        return False
