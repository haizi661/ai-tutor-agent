from __future__ import annotations

import re
from typing import Any


DOMAIN_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("反馈控制", "反馈控制系统", "负反馈控制", "闭环控制", "按偏差控制"),
    ("开环控制", "开环系统"),
    ("复合控制", "复合校正"),
    ("扰动", "干扰"),
    ("根轨迹", "根轨迹法", "广义根轨迹"),
    ("频域", "频率域", "频域分析"),
    ("时域", "时域分析", "时间响应"),
    ("频率特性", "频率响应"),
    ("奈奎斯特", "奈奎斯特曲线", "奈奎斯特图", "nyquist", "nyquist图", "nyquist判据"),
    ("波特图", "bode", "bode图"),
    ("传递函数", "脉冲传递函数"),
    ("状态空间", "状态空间模型", "状态空间表达式", "状态方程"),
    ("稳态误差", "静差", "误差系数"),
    ("稳定性", "稳定判据", "劳斯判据", "劳斯", "routh"),
    ("校正", "校正方法", "串联校正", "反馈校正"),
    ("可控性", "可观性"),
)

QUESTION_SCAFFOLD_PHRASES: tuple[str, ...] = (
    "请问",
    "想问",
    "解释一下",
    "解释",
    "说明一下",
    "说明",
    "为什么",
    "为啥",
    "如何",
    "怎么",
    "怎样",
    "能否",
    "能够",
    "可以",
    "是否",
    "什么是",
    "是什么意思",
    "有什么作用",
    "有什么用",
    "有何作用",
    "有何意义",
    "有什么关系",
    "有何关系",
    "之间有什么关系",
    "之间的关系",
    "它的作用",
    "其作用",
    "这个作用",
)

CHINESE_JOINERS_PATTERN = re.compile(r"[和与及或并且以及、/]")


class NodeSelector:
    """
    基于图谱 2.1 的教学字段做问题到节点的粗召回。

    当前版本会综合以下信息：
    - name / core_concepts / tags
    - assessment_focus / explanation_teacher_style
    - extra.retrieval_keywords / resolved_* / node_role
    - 控制理论常见中英术语别名，例如 Nyquist <-> 奈奎斯特
    """

    def detect_question_type(self, question: str) -> str:
        q = (question or "").strip()

        learning_path_keywords = [
            "接下来学什么",
            "下一步学什么",
            "后面学什么",
            "推荐学什么",
            "学习路径",
            "学完",
            "之后学什么",
        ]
        requirement_keywords = [
            "要求是什么",
            "课程要求",
            "掌握到什么程度",
            "是了解还是掌握",
            "掌握还是了解",
            "过关标准",
            "掌握门槛",
        ]
        prerequisite_keywords = [
            "前置知识",
            "先修知识",
            "学习这个之前要学什么",
            "之前要学什么",
            "之前要先学什么",
            "先学什么",
            "先学哪些",
            "学这个前要学什么",
        ]

        if any(k in q for k in prerequisite_keywords):
            return "prerequisite_query"
        if any(k in q for k in learning_path_keywords):
            return "learning_path"
        if any(k in q for k in requirement_keywords):
            return "requirement_query"
        return "knowledge_qa"

    def select_node(
        self,
        question: str,
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not question or not nodes:
            return None

        best_node: dict[str, Any] | None = None
        best_score = -1.0
        for node in nodes:
            score = self._score_node(question, node)
            if score > best_score:
                best_score = score
                best_node = node
        return best_node

    def select_best_node(
        self,
        query: str,
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        return self.select_node(query, nodes)

    def _score_node(self, query: str, node: dict[str, Any]) -> float:
        query = (query or "").strip()
        if not query:
            return 0.0

        name = str(node.get("name", "") or "").strip()
        chapter = str(node.get("chapter", "") or "").strip()
        summary = str(node.get("summary", "") or "").strip()
        assessment_focus = str(node.get("assessment_focus", "") or "").strip()
        explanation_teacher_style = str(node.get("explanation_teacher_style", "") or "").strip()
        tags = [str(tag).strip() for tag in (node.get("tags", []) or []) if str(tag).strip()]
        core_concepts = [
            str(item).strip()
            for item in (node.get("core_concepts", []) or [])
            if str(item).strip()
        ]
        extra = node.get("extra", {}) or {}

        query_terms = self._extract_query_tokens(query)
        query_text_norm = self._normalize_text(query)

        score = 0.0
        node_terms: list[tuple[str, float]] = []

        node_terms.append((name, 8.0))
        node_terms.extend((kw, 4.5) for kw in self._extract_name_keywords(name))
        node_terms.extend((tag, 3.2) for tag in tags)
        node_terms.extend((concept, 4.0) for concept in core_concepts)
        node_terms.extend((keyword, 3.6) for keyword in self._collect_extra_keywords(extra))
        node_terms.extend((keyword, 0.8) for keyword in self._split_keywords(summary))
        node_terms.extend((keyword, 0.3) for keyword in self._split_keywords(explanation_teacher_style)[:12])

        if chapter and chapter in query:
            score += 1.5
        if assessment_focus and assessment_focus in query:
            score += 2.6

        strongest_term_match = 0.0
        overlap_count = 0
        expanded_evidence_terms: list[str] = []

        for term, weight in node_terms:
            match_strength = self._match_strength(query_text_norm, query_terms, term)
            if match_strength <= 0:
                continue
            strongest_term_match = max(strongest_term_match, match_strength)
            score += weight * match_strength
            if match_strength >= 0.7:
                overlap_count += 1
            expanded_evidence_terms.extend(self._expand_alias_terms(term))

        if overlap_count:
            score += min(overlap_count * 0.55, 3.0)
        if name and any(self._normalize_text(term) in self._normalize_text(name) for term in query_terms):
            score += 1.2
        if any(
            self._normalize_text(term) in self._normalize_text(concept)
            for term in query_terms
            for concept in core_concepts
        ):
            score += 1.0

        if self._query_is_specific(query_terms) and strongest_term_match < 0.7:
            score -= 1.8

        semantic_overlap = 0
        expanded_evidence_norm = [self._normalize_text(term) for term in expanded_evidence_terms if term]
        for token in query_terms:
            token_norm = self._normalize_text(token)
            if any(token_norm and token_norm in evidence for evidence in expanded_evidence_norm):
                semantic_overlap += 1
        if semantic_overlap:
            score += min(semantic_overlap * 0.4, 2.4)

        score += self._importance_bonus(node)
        score += self._role_bonus(extra, strongest_term_match=strongest_term_match)
        score += min(len(name) / 20.0, 1.0)
        return score

    def _collect_extra_keywords(self, extra: dict[str, Any]) -> list[str]:
        if not isinstance(extra, dict):
            return []

        keys_to_collect = [
            "retrieval_keywords",
            "resolved_prerequisite_names",
            "resolved_related_names",
            "resolved_weak_related_names",
            "matched_block_title",
            "retrieval_matched_block_title",
        ]
        results: list[str] = []

        for key in keys_to_collect:
            value = extra.get(key)
            if isinstance(value, list):
                for item in value:
                    text = str(item).strip()
                    if text and text not in results:
                        results.append(text)
            else:
                text = str(value or "").strip()
                if text and text not in results:
                    results.append(text)

        node_role = str(extra.get("node_role", "") or "").strip()
        if node_role and node_role not in results:
            results.append(node_role)
        return results

    def _importance_bonus(self, node: dict[str, Any]) -> float:
        importance = str(node.get("importance_level", "") or "").strip()
        bonuses = {
            "核心": 0.9,
            "重要": 0.55,
            "一般": 0.15,
        }
        return bonuses.get(importance, 0.0)

    def _role_bonus(self, extra: dict[str, Any], *, strongest_term_match: float) -> float:
        if not isinstance(extra, dict):
            return 0.0
        role = str(extra.get("node_role", "") or "").strip()
        if role == "chapter_anchor":
            return 0.35 if strongest_term_match >= 0.8 else -0.2
        if role == "topic":
            return 0.4
        if role:
            return 0.1
        return 0.0

    def _extract_name_keywords(self, name: str) -> list[str]:
        results: list[str] = []
        name = name.strip()
        if not name:
            return results

        results.append(name)

        if "的" in name:
            tail = name.split("的", 1)[-1].strip()
            if len(tail) >= 2:
                results.append(tail)

        common_parts = [
            "根轨迹法",
            "根轨迹",
            "频域分析",
            "时域分析",
            "数学模型",
            "自动控制系统",
            "自动控制",
            "反馈控制",
            "稳态误差",
            "稳定性",
            "状态空间",
            "离散系统",
            "校正方法",
            "频率特性",
            "结构图与信号流图",
            "奈奎斯特",
            "传递函数",
        ]
        for part in common_parts:
            if part in name and part not in results:
                results.append(part)

        deduped: list[str] = []
        for item in results:
            if item not in deduped:
                deduped.append(item)
        return deduped

    def _split_keywords(self, text: str) -> list[str]:
        normalized = self._normalize_query_surface(text)
        parts = [item.strip() for item in normalized.split() if item.strip()]
        results: list[str] = []
        for part in parts:
            if len(part) < 2:
                continue
            if part not in results:
                results.append(part)
            for term in self._extract_known_terms(part):
                if term not in results:
                    results.append(term)
        return results

    def _extract_query_tokens(self, text: str) -> list[str]:
        normalized = self._normalize_query_surface(text)
        raw_parts = re.findall(r"[A-Za-z][A-Za-z0-9_%-]*|[\u4e00-\u9fff]{2,}|[0-9]+(?:\.[0-9]+)?", normalized)
        stop_words = {"什么", "关系", "如何", "为什么", "请问", "一个", "系统", "作用", "意义"}
        results: list[str] = []

        for part in raw_parts:
            token = part.strip()
            if len(token) < 2:
                continue
            lowered = token.lower()
            if token in stop_words or lowered in stop_words:
                continue
            if token not in results:
                results.append(token)
            for term in self._extract_known_terms(token):
                if term not in results:
                    results.append(term)
            for alias in self._expand_alias_terms(token):
                if alias not in results:
                    results.append(alias)
        return results[:18]

    def _normalize_query_surface(self, text: str) -> str:
        normalized = str(text or "").strip()
        normalized = normalized.replace("（", " ").replace("）", " ")
        normalized = normalized.replace("(", " ").replace(")", " ")
        normalized = normalized.replace("？", " ").replace("?", " ")
        normalized = normalized.replace("，", " ").replace(",", " ")
        normalized = normalized.replace("。", " ").replace("；", " ").replace("：", " ")
        normalized = normalized.replace("“", " ").replace("”", " ")
        normalized = CHINESE_JOINERS_PATTERN.sub(" ", normalized)
        for phrase in QUESTION_SCAFFOLD_PHRASES:
            normalized = normalized.replace(phrase, " ")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def _extract_known_terms(self, text: str) -> list[str]:
        chunk = str(text or "").strip()
        if len(chunk) < 2:
            return []

        results: list[str] = []
        for aliases in DOMAIN_ALIAS_GROUPS:
            for alias in aliases:
                if len(alias) < 2:
                    continue
                alias_norm = self._normalize_text(alias)
                chunk_norm = self._normalize_text(chunk)
                if alias_norm and alias_norm in chunk_norm and alias not in results:
                    results.append(alias)
        if len(chunk) >= 4 and chunk not in results:
            results.append(chunk)
        return results

    def _expand_alias_terms(self, text: str) -> list[str]:
        term = str(text or "").strip()
        if len(term) < 2:
            return []

        term_norm = self._normalize_text(term)
        results = [term]
        for aliases in DOMAIN_ALIAS_GROUPS:
            alias_norms = [self._normalize_text(alias) for alias in aliases]
            if any(alias_norm and (alias_norm == term_norm or alias_norm in term_norm or term_norm in alias_norm) for alias_norm in alias_norms):
                for alias in aliases:
                    if alias not in results:
                        results.append(alias)
        return results

    def _match_strength(self, query_text_norm: str, query_terms: list[str], term: str) -> float:
        term_variants = self._expand_alias_terms(term)
        query_variants: list[str] = []
        for token in query_terms:
            query_variants.extend(self._expand_alias_terms(token))

        term_norms = [self._normalize_text(item) for item in term_variants if self._normalize_text(item)]
        query_norms = [self._normalize_text(item) for item in query_variants if self._normalize_text(item)]

        for term_norm in term_norms:
            if term_norm and term_norm in query_text_norm:
                return 1.0 if len(term_norm) >= 4 else 0.85

        for query_norm in query_norms:
            if any(query_norm and query_norm in term_norm for term_norm in term_norms):
                if len(query_norm) >= 4:
                    return 0.9
                return 0.72

        for term_norm in term_norms:
            if any(term_norm and term_norm in query_norm for query_norm in query_norms):
                return 0.65

        return 0.0

    def _query_is_specific(self, query_terms: list[str]) -> bool:
        strong_terms = [term for term in query_terms if len(self._normalize_text(term)) >= 4]
        return bool(strong_terms)

    def _normalize_text(self, text: str) -> str:
        normalized = str(text or "").strip().lower()
        normalized = re.sub(r"\s+", "", normalized)
        return normalized
