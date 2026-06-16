import ast
import csv
import json
import os
import re
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

from ai_tutor_agent.course_assets import get_course_assets
from ai_tutor_agent.knowledge_map.builders.graph_media_enricher import GraphMediaEnricher
from ai_tutor_agent.knowledge_map.debug_graph_rag import build_learning_answer_html

from .config import (
    AI_NODES_CSV,
    AI_EDGES_CSV,
    AI_STUDENT_STATE_JSON,
    DEEPSEEK_API_URL,
    DEEPSEEK_MODEL,
)


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []

    text = str(value).strip()

    if not text or text in {"[]", "无", "None", "none", "null"}:
        return []

    try:
        data = ast.literal_eval(text)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass

    if "||" in text:
        parts = text.split("||")
    else:
        text = (
            text.replace("，", ",")
            .replace("；", ",")
            .replace("、", ",")
            .replace(";", ",")
        )
        parts = text.split(",")

    return [x.strip() for x in parts if x.strip()]


def _safe_extra(value: Any) -> Dict[str, Any]:
    if not value:
        return {}

    text = str(value).strip()

    for parser in (json.loads, ast.literal_eval):
        try:
            data = parser(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return {}


def _read_csv(path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {path}")

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _load_student_state() -> Dict[str, Any]:
    if not AI_STUDENT_STATE_JSON.exists():
        return {
            "student_id": "default_ai_student",
            "current_goal": "",
            "current_path": [],
            "current_node": "",
            "mastery_scores": {},
            "learned_nodes": {},
            "weak_nodes": {},
            "intent_history": [],
            "dialogue_sessions": {},
            "path_versions": [],
        }

    try:
        with open(AI_STUDENT_STATE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    data.setdefault("student_id", "default_ai_student")
    data.setdefault("current_goal", "")
    data.setdefault("current_path", [])
    data.setdefault("current_node", "")
    data.setdefault("mastery_scores", {})
    data.setdefault("learned_nodes", {})
    data.setdefault("weak_nodes", {})
    data.setdefault("intent_history", [])
    data.setdefault("dialogue_sessions", {})
    data.setdefault("path_versions", [])

    return data


def _save_student_state(state: Dict[str, Any]) -> None:
    AI_STUDENT_STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(AI_STUDENT_STATE_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


_COMPLETED_STATUSES = {
    "completed",
    "complete",
    "mastered",
    "passed",
    "done",
}


def _score_to_unit(value: Any) -> float:
    """Normalize 0-1 and 0-100 mastery scores to the AI path 0-1 scale."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if score < 0:
        return 0.0
    if score > 1:
        score = score / 100.0
    return max(0.0, min(score, 1.0))


def _status_completed(value: Any) -> bool:
    return str(value or "").strip().lower() in _COMPLETED_STATUSES


def _contains_node(container: Any, node_id: str) -> bool:
    if isinstance(container, dict):
        return node_id in container
    if isinstance(container, list):
        return node_id in {str(item) for item in container}
    return False


def _node_progress_from_student(
    student: Dict[str, Any],
    node_id: str,
    *,
    threshold: float = 0.75,
) -> Dict[str, Any]:
    threshold = _score_to_unit(threshold)
    learned = student.get("learned_nodes", {}) or {}
    mastery_scores = student.get("mastery_scores", {}) or {}
    knowledge_graph = student.get("knowledge_graph", {}) or {}
    node_records = student.get("node_learning_records", {}) or {}

    mastery_candidates: List[float] = []
    sources: List[str] = []
    completed = False

    learned_record = learned.get(node_id, {}) if isinstance(learned, dict) else {}
    if isinstance(learned_record, dict):
        if "mastery" in learned_record:
            mastery_candidates.append(_score_to_unit(learned_record.get("mastery")))
            sources.append("learned_nodes.mastery")
        if _status_completed(learned_record.get("status")):
            completed = True
            sources.append("learned_nodes.status")

    if isinstance(mastery_scores, dict) and node_id in mastery_scores:
        mastery_candidates.append(_score_to_unit(mastery_scores.get(node_id)))
        sources.append("mastery_scores")

    kg_record = knowledge_graph.get(node_id, {}) if isinstance(knowledge_graph, dict) else {}
    if isinstance(kg_record, dict):
        if "score" in kg_record:
            mastery_candidates.append(_score_to_unit(kg_record.get("score")))
            sources.append("knowledge_graph.score")
        if "mastery" in kg_record:
            mastery_candidates.append(_score_to_unit(kg_record.get("mastery")))
            sources.append("knowledge_graph.mastery")
        if _status_completed(kg_record.get("status")):
            completed = True
            sources.append("knowledge_graph.status")

    learning_record = node_records.get(node_id, {}) if isinstance(node_records, dict) else {}
    if isinstance(learning_record, dict):
        for key in ("mastery", "score", "best_score"):
            if key in learning_record:
                mastery_candidates.append(_score_to_unit(learning_record.get(key)))
                sources.append(f"node_learning_records.{key}")
        if _status_completed(learning_record.get("status")):
            completed = True
            sources.append("node_learning_records.status")

    visited = _contains_node(student.get("visited_nodes", []), node_id)
    weak = (
        _contains_node(student.get("weak_nodes", {}), node_id)
        or _contains_node(student.get("wrong_nodes", []), node_id)
    )

    mastery = max(mastery_candidates) if mastery_candidates else 0.0
    if completed and mastery <= 0:
        mastery = max(threshold, 0.85)

    mastered = completed or (mastery >= threshold and not weak)
    if visited:
        sources.append("visited_nodes")
    if weak:
        sources.append("weak_or_wrong_nodes")

    return {
        "mastery": mastery,
        "completed": completed,
        "visited": visited,
        "weak": weak,
        "mastered": mastered,
        "sources": sources,
    }


def _load_deepseek_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

    return api_key or ""


def _call_deepseek_json(prompt: str) -> Dict[str, Any]:
    api_key = _load_deepseek_key()

    if not api_key:
        return {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是人工智能学习路径规划助手。你必须只输出合法 JSON，不要输出 Markdown，不要解释。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.35,
        "stream": False,
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=80,
        )
        resp.raise_for_status()

        text = resp.json()["choices"][0]["message"]["content"].strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception:
        return {}


def _call_deepseek_json_with_system(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    api_key = _load_deepseek_key()

    if not api_key:
        return {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "temperature": 0.35,
        "stream": False,
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=80,
        )
        resp.raise_for_status()

        text = resp.json()["choices"][0]["message"]["content"].strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception:
        return {}


class AILearningPathService:
    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.node_by_id: Dict[str, Dict[str, Any]] = {}
        self.id_by_name: Dict[str, str] = {}
        self.prereq_in: Dict[str, List[str]] = defaultdict(list)
        self.prereq_out: Dict[str, List[str]] = defaultdict(list)
        self.related: Dict[str, List[str]] = defaultdict(list)
        self.media_enricher = self._create_media_enricher()
        self.reload()

    def _create_media_enricher(self):
        try:
            assets = get_course_assets("artificial_intelligence")
            return GraphMediaEnricher(
                mineru_cache_root=assets.mineru_cache_root,
                annotated_assets_path=assets.media_evidence_index_dir,
            )
        except Exception:
            return None

    def reload(self) -> None:
        self.nodes = _read_csv(AI_NODES_CSV)
        self.edges = _read_csv(AI_EDGES_CSV)

        self.node_by_id = {
            n.get("node_id", ""): n
            for n in self.nodes
            if n.get("node_id")
        }

        self.id_by_name = {
            n.get("name", ""): n.get("node_id", "")
            for n in self.nodes
            if n.get("name")
        }

        self.prereq_in.clear()
        self.prereq_out.clear()
        self.related.clear()

        for e in self.edges:
            source = e.get("source", "")
            target = e.get("target", "")
            relation = e.get("relation", "")

            if not source or not target:
                continue

            if relation == "prerequisite_of":
                self.prereq_in[target].append(source)
                self.prereq_out[source].append(target)
            elif relation in {"related_to", "parallel_to", "weak_related_to"}:
                self.related[source].append(target)
                self.related[target].append(source)

    def get_status(self) -> Dict[str, Any]:
        state = _load_student_state()
        return {
            "status": "success",
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "student": state,
        }
    def _llm_extract_search_terms(self, user_text: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        history_text = "\n".join(dialogue.get("intent_history", [])[-6:])
        node_names = "\n".join(
            f'{n.get("node_id", "")}: {n.get("name", "")}'
            for n in self.nodes
        )

        prompt = f"""
    你要帮助学生从自然语言中提取人工智能学习目标，并从知识图谱节点中挑选可能相关的节点。

    学生历史输入：
    {history_text}

    学生最新输入：
    {user_text}

    可选知识图谱节点：
    {node_names}

    只输出 JSON，不要 Markdown。

    输出格式：
    {{
      "search_terms": [],
      "candidate_node_ids": [],
      "is_broad_goal": true,
      "short_goal": "",
      "reason": ""
    }}

    要求：
    1. search_terms 用于检索知识图谱，例如“强化学习”“目标检测”“YOLO”“RAG”。
    2. candidate_node_ids 只能从可选节点中选，不能编造。
    3. 如果用户说“我想学强化学习”，search_terms 必须保留“强化学习”，不要拆成“强化”。
    4. 如果目标很宽泛，is_broad_goal 为 true。
    5. short_goal 用一句短语概括用户目标。
    """

        result = _call_deepseek_json(prompt)
        if not result:
            return {
                "search_terms": [self._normalize_query(user_text)],
                "candidate_node_ids": [],
                "is_broad_goal": True,
                "short_goal": user_text,
                "reason": "DeepSeek 未返回有效结果，使用规则兜底。",
            }

        valid_ids = set(self.node_by_id.keys())
        candidate_ids = [
            str(x) for x in result.get("candidate_node_ids", [])
            if str(x) in valid_ids
        ]

        terms = result.get("search_terms", [])
        if not isinstance(terms, list):
            terms = [str(terms)]

        terms = [str(x).strip() for x in terms if str(x).strip()]

        return {
            "search_terms": terms or [self._normalize_query(user_text)],
            "candidate_node_ids": candidate_ids,
            "is_broad_goal": bool(result.get("is_broad_goal", True)),
            "short_goal": str(result.get("short_goal", user_text)),
            "reason": str(result.get("reason", "")),
        }

    def _format_node(
        self,
        node_id: str,
        mastery: float = 0.0,
        status: str = "not_started",
        reason: str = "",
    ) -> Dict[str, Any]:
        n = self.node_by_id.get(node_id, {})

        return {
            "node_id": node_id,
            "name": n.get("name", node_id),
            "chapter": n.get("chapter", ""),
            "summary": n.get("summary", ""),
            "tags": _safe_list(n.get("tags", "")),
            "requirement_level": n.get("requirement_level", ""),
            "mastery_threshold": float(n.get("mastery_threshold") or 0.75),
            "importance_level": n.get("importance_level", ""),
            "assessment_focus": n.get("assessment_focus", ""),
            "explanation_raw": n.get("explanation_raw", ""),
            "explanation_teacher_style": n.get("explanation_teacher_style", ""),
            "core_concepts": _safe_list(n.get("core_concepts", "")),
            "key_points": _safe_list(n.get("key_points", "")),
            "formulas": _safe_list(n.get("formulas", "")),
            "examples": _safe_list(n.get("examples", "")),
            "figures_refs": _safe_list(n.get("figures_refs", "")),
            "page_refs": _safe_list(n.get("page_refs", "")),
            "definition_candidates": _safe_list(n.get("definition_candidates", "")),
            "key_point_candidates": _safe_list(n.get("key_point_candidates", "")),
            "formula_candidates": _safe_list(n.get("formula_candidates", "")),
            "example_candidates": _safe_list(n.get("example_candidates", "")),
            "prerequisite_nodes": _safe_list(n.get("prerequisite_nodes", "")),
            "next_nodes": _safe_list(n.get("next_nodes", "")),
            "related_nodes": _safe_list(n.get("related_nodes", "")),
            "application_nodes": _safe_list(n.get("application_nodes", "")),
            "recommended_next_nodes": _safe_list(n.get("recommended_next_nodes", "")),
            "extra": _safe_extra(n.get("extra", "")),
            "mastery": mastery,
            "status": status,
            "reason": reason,
        }

    def _build_node_lesson_with_llm(self, node: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "node_id": node.get("node_id", ""),
            "name": node.get("name", ""),
            "summary": node.get("summary", ""),
            "explanation_raw": node.get("explanation_raw", ""),
            "key_points": node.get("key_points", []),
            "formulas": node.get("formulas", []),
            "examples": node.get("examples", []),
            "figures_refs": node.get("figures_refs", []),
            "definition_candidates": node.get("definition_candidates", []),
            "key_point_candidates": node.get("key_point_candidates", []),
            "formula_candidates": node.get("formula_candidates", []),
            "example_candidates": node.get("example_candidates", []),
            "prerequisite_nodes": node.get("prerequisite_nodes", []),
            "next_nodes": node.get("next_nodes", []),
            "related_nodes": node.get("related_nodes", []),
            "application_nodes": node.get("application_nodes", []),
            "recommended_next_nodes": node.get("recommended_next_nodes", []),
        }

        system_prompt = (
            "你是一位人工智能课程讲解老师。"
            "请基于给定的知识图谱节点内容进行二次整理、补充和结构化讲解。"
            "只输出合法 JSON，不要输出 Markdown 代码块，不要解释。"
        )

        user_prompt = f"""
请根据下面的节点数据生成讲解内容。

节点数据(JSON)：
{json.dumps(payload, ensure_ascii=False)}

输出格式：
{{
  "lesson_markdown": "",
  "options": []
}}

要求：
1. lesson_markdown 用中文，允许使用 Markdown 标题和列表。
2. 讲解顺序：核心概念 -> 关键点 -> 公式与直觉 -> 典型例子 -> 易错点/边界 -> 关联与下一步。
3. 必须覆盖 explanation_raw、key_points、formulas、examples 中的关键信息。
4. 如果 figures_refs 或候选字段为空，不要编造。
5. options 给 3 到 4 个下一步按钮，例如：
   ["我懂了，进入下一个节点", "再讲简单一点", "换一个例子", "重新调整路径"]
"""

        return _call_deepseek_json_with_system(system_prompt, user_prompt)

    def _reference_section(self, node: Dict[str, Any]) -> str:
        groups = [
            ("页码", node.get("page_refs", [])),
            ("图表", node.get("figures_refs", [])),
            ("公式", node.get("formulas", [])),
        ]
        lines = []
        for label, values in groups:
            cleaned = [
                str(item).strip()
                for item in (values or [])
                if str(item).strip() and str(item).strip() not in {"无", "none", "None", "null", "[]"}
            ]
            if cleaned:
                lines.append(f"- {label}: {'；'.join(cleaned[:8])}")
        if not lines:
            return ""
        return "\n\n#### 参考资料\n" + "\n".join(lines)

    def _with_reference_section(self, content: str, node: Dict[str, Any]) -> str:
        text = (content or "").strip()
        refs = self._reference_section(node)
        if not refs:
            return text
        if "参考资料" in text:
            return text
        return text + refs

    def _formatted_node_map(self) -> Dict[str, Dict[str, Any]]:
        return {
            node_id: self._format_node(node_id)
            for node_id in self.node_by_id
        }

    def _collect_node_media_items(
        self,
        node: Dict[str, Any],
        *,
        question: str = "",
    ) -> List[Dict[str, Any]]:
        if not self.media_enricher:
            return []

        node_id = str(node.get("node_id", "") or "").strip()
        if not node_id:
            return []

        traversed = [{
            "node_id": node_id,
            "name": node.get("name", ""),
            "node_role": "primary",
            "hop": 0,
            "score": 1.0,
        }]
        try:
            media_items = self.media_enricher.collect_for_nodes(
                traversed_nodes=traversed,
                node_map=self._formatted_node_map(),
                question=question or str(node.get("name", "")),
            )
            source_doc = str(
                (node.get("extra") or {}).get("retrieval_source_pdf", "") or ""
            ).strip()
            same_doc_items = [
                item for item in media_items
                if source_doc and str(item.get("source_doc_id", "") or "") == source_doc
            ]
            return same_doc_items or media_items
        except Exception:
            return []

    def _with_primary_media_markers(
        self,
        content: str,
        media_items: List[Dict[str, Any]],
    ) -> str:
        text = (content or "").strip()
        if not text or "[[MEDIA:" in text:
            return text

        figures = [
            item for item in media_items
            if item.get("asset_type") == "figure" and item.get("is_primary")
        ] or [
            item for item in media_items
            if item.get("asset_type") == "figure"
        ]
        refs = [
            str(item.get("reference", "") or "").strip()
            for item in figures[:2]
            if str(item.get("reference", "") or "").strip()
        ]
        if not refs:
            return text

        markers = "\n".join(f"[[MEDIA:{ref}]]" for ref in refs)
        cue_re = re.compile(
            r"(\u56fe|\u56fe\u8868|\u793a\u610f|\u53d1\u5c55\u53f2|\u793a\u4f8b)"
        )
        lines = text.splitlines()
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and cue_re.search(stripped):
                lines.insert(index + 1, markers)
                return "\n".join(lines)

        return f"{text}\n\n{markers}"

    def _render_learning_message(
        self,
        *,
        content: str,
        node: Dict[str, Any],
        question: str = "",
    ) -> str:
        text = (content or "").strip()
        media_items = self._collect_node_media_items(node, question=question)
        if media_items:
            answer = self._with_primary_media_markers(text, media_items)
            html = build_learning_answer_html({
                "question": question or node.get("name", ""),
                "answer": answer,
                "media_items": media_items,
                "evidence_items": [],
            }).strip()
            if html:
                return html

        return self._with_reference_section(text, node)

    def _polish_learning_output(
        self,
        *,
        node: Dict[str, Any],
        draft: str,
        output_type: str,
        question: str = "",
    ) -> str:
        draft = (draft or "").strip()
        if not draft:
            return ""

        payload = {
            "node_id": node.get("node_id", ""),
            "name": node.get("name", ""),
            "summary": node.get("summary", ""),
            "key_points": node.get("key_points", []),
            "formulas": node.get("formulas", []),
            "examples": node.get("examples", []),
            "figures_refs": node.get("figures_refs", []),
            "page_refs": node.get("page_refs", []),
            "question": question,
            "draft": draft,
        }

        system_prompt = (
            "你是人工智能课程伴学老师，负责把已经生成的节点讲解做最后一遍自然化润色。"
            "你可以调整表达顺序、加入过渡句、换一个例子角度，让同一节点每次讲解不完全一样。"
            "不要编造节点数据中没有的页码、图表、公式和来源。"
            "只输出合法 JSON，不要输出 Markdown 代码块。"
        )
        user_prompt = f"""
请对下面的人工智能课程{output_type}做最终润色。

节点与草稿(JSON):
{json.dumps(payload, ensure_ascii=False)}

输出格式:
{{
  "content_markdown": ""
}}

要求:
1. 使用中文 Markdown。
2. 保留草稿中的核心知识，不要删掉关键定义、关键步骤、公式名和例子。
3. 语气像老师现场讲解，少一点模板感，多一点自然过渡。
4. 如果是追问回答，要直接回应学生问题，不要重新完整讲一遍节点。
5. 不要在正文里编造“来自第几页”“见图几”等不存在的来源。
6. 不要输出“参考资料”小节；参考资料会由系统根据节点字段追加。
"""
        result = _call_deepseek_json_with_system(system_prompt, user_prompt)
        polished = str(result.get("content_markdown") or "").strip() if result else ""
        return polished or draft

    def _normalize_query(self, text: str) -> str:
        text = (text or "").strip().lower()

        remove_phrases = [
            "我想学习",
            "我想要学习",
            "我希望学习",
            "我要学习",
            "我想学",
            "我想要学",
            "我希望学",
            "我要学",
            "想了解",
            "想学",
            "了解一下",
            "请问",
            "人工智能中的",
            "人工智能里面的",
            "人工智能",
            "ai",
        ]

        for phrase in remove_phrases:
            text = text.replace(phrase, " ")

        text = re.sub(r"\s+", " ", text).strip()
        return text

    def search_nodes(self, query: str, limit: int = 12) -> List[Dict[str, Any]]:
        raw_query = (query or "").strip()
        query = self._normalize_query(raw_query)
        terms = [t for t in re.split(r"[\s,，、/]+", query) if t]

        scored: List[Tuple[int, str]] = []

        for n in self.nodes:
            node_id = n.get("node_id", "")
            name = n.get("name", "")

            haystack = " ".join(
                [
                    name,
                    n.get("summary", ""),
                    n.get("tags", ""),
                    n.get("core_concepts", ""),
                    n.get("key_points", ""),
                    n.get("examples", ""),
                    n.get("application_nodes", ""),
                    n.get("recommended_next_nodes", ""),
                ]
            ).lower()

            score = 0

            if raw_query and raw_query == name:
                score += 120

            if query and query == name.lower():
                score += 100

            if query and query in name.lower():
                score += 80

            if query and query in haystack:
                score += 45

            for term in terms:
                if term in name.lower():
                    score += 35
                elif term in haystack:
                    score += 12

            if score > 0:
                scored.append((score, node_id))

        scored.sort(reverse=True)

        return [
            self._format_node(node_id, reason="与当前学习意图匹配")
            for _, node_id in scored[:limit]
            if node_id in self.node_by_id
        ]

    def _collect_prerequisites(
        self,
        target_ids: List[str],
        max_depth: int = 5,
        max_nodes: int = 50,
    ) -> Set[str]:
        result: Set[str] = set()
        queue = deque([(tid, 0) for tid in target_ids])

        while queue and len(result) < max_nodes:
            node_id, depth = queue.popleft()

            if depth >= max_depth:
                continue

            for pre in self.prereq_in.get(node_id, []):
                if pre in result or pre in target_ids:
                    continue

                result.add(pre)
                queue.append((pre, depth + 1))

        return result

    def _topological_order(
        self,
        node_ids: Set[str],
        target_ids: List[str],
    ) -> List[str]:
        selected = set(node_ids) | set(target_ids)

        indegree = {nid: 0 for nid in selected}
        graph = {nid: [] for nid in selected}

        for source in selected:
            for target in self.prereq_out.get(source, []):
                if target in selected:
                    graph[source].append(target)
                    indegree[target] += 1

        queue = deque([nid for nid, deg in indegree.items() if deg == 0])
        ordered = []

        while queue:
            nid = queue.popleft()
            ordered.append(nid)

            for nxt in graph.get(nid, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        for nid in selected:
            if nid not in ordered:
                ordered.append(nid)

        ordered = [x for x in ordered if x not in target_ids] + [
            x for x in target_ids
            if x in selected
        ]

        return ordered

    def build_plan(
        self,
        target_ids: List[str],
        skip_mastered: bool = True,
        keep_completed: bool = False,
    ) -> Dict[str, Any]:
        valid_targets = [tid for tid in target_ids if tid in self.node_by_id]

        if not valid_targets:
            return {
                "status": "error",
                "message": "没有有效目标节点",
                "path": [],
                "target_nodes": [],
            }

        student = _load_student_state()
        learned = student.get("learned_nodes", {}) or {}
        mastery_scores = student.get("mastery_scores", {}) or {}

        frozen_path = []
        frozen_ids = set()
        current_node = str(student.get("current_node") or "").strip()
        has_current_frozen = False

        if keep_completed and isinstance(learned, dict):
            learned_items = []
            for node_id, record in learned.items():
                if node_id not in self.node_by_id:
                    continue
                progress = _node_progress_from_student(
                    student,
                    node_id,
                    threshold=float(
                        self.node_by_id.get(node_id, {}).get("mastery_threshold") or 0.75
                    ),
                )
                if not progress["mastered"]:
                    continue
                finish_time = str(record.get("finish_time") or "")
                learned_items.append((finish_time, node_id))

            learned_items.sort(key=lambda item: item[0])

            for _, node_id in learned_items:
                mastery = _node_progress_from_student(
                    student,
                    node_id,
                    threshold=float(
                        self.node_by_id.get(node_id, {}).get("mastery_threshold") or 0.75
                    ),
                )["mastery"]
                frozen_path.append(
                    self._format_node(node_id, mastery, "mastered", "已完成学习")
                )
                frozen_ids.add(node_id)

        if keep_completed and current_node and current_node in self.node_by_id and current_node not in frozen_ids:
            mastery = _node_progress_from_student(
                student,
                current_node,
                threshold=float(
                    self.node_by_id.get(current_node, {}).get("mastery_threshold") or 0.75
                ),
            )["mastery"]
            frozen_path.append(
                self._format_node(current_node, mastery, "current", "当前正在学习的节点")
            )
            frozen_ids.add(current_node)
            has_current_frozen = True

        prereq_nodes = self._collect_prerequisites(valid_targets)
        ordered = self._topological_order(prereq_nodes, valid_targets)

        path = []
        skipped = []

        for node_id in ordered:
            if keep_completed and node_id in frozen_ids:
                continue
            threshold = float(
                self.node_by_id.get(node_id, {}).get("mastery_threshold") or 0.75
            )
            if threshold > 1:
                threshold = threshold / 100.0
            progress = _node_progress_from_student(student, node_id, threshold=threshold)
            mastery = progress["mastery"]

            if skip_mastered and progress["mastered"]:
                skipped.append(
                    self._format_node(
                        node_id,
                        mastery,
                        "mastered",
                        "已达到掌握阈值，本轮路径中跳过",
                    )
                )
                continue

            if node_id in valid_targets:
                status = "goal"
                reason = "这是本轮确认后的学习目标节点"
            elif not path:
                status = "current"
                reason = "建议从该前置知识开始补齐基础"
            else:
                status = "not_started"
                reason = "该节点位于目标知识的前置路径中"

            path.append(self._format_node(node_id, mastery, status, reason))

        if path:
            if not has_current_frozen:
                path[0]["status"] = "current"
                student["current_node"] = path[0]["node_id"]
        elif has_current_frozen:
            student["current_node"] = current_node
        else:
            student["current_node"] = ""

        target_names = [
            self.node_by_id[tid].get("name", tid)
            for tid in valid_targets
        ]

        student["current_goal"] = "、".join(target_names)
        student["confirmed_target_nodes"] = valid_targets
        full_path = frozen_path + skipped + path
        student["current_path"] = [n["node_id"] for n in full_path]

        student.setdefault("path_versions", []).append(
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "target_nodes": valid_targets,
                "path": student["current_path"],
                "skipped": [n["node_id"] for n in skipped],
            }
        )

        _save_student_state(student)

        user_knowledge_graph = {}

        for n in full_path:
            if n["status"] == "current":
                graph_status = "in_progress"
            elif n["status"] == "goal":
                graph_status = "goal"
            elif n["status"] == "mastered":
                graph_status = "mastered"
            else:
                graph_status = "upcoming"

            user_knowledge_graph[n["name"]] = {
                "id": n["node_id"],
                "status": graph_status,
                "mastery": n["mastery"],
            }

        return {
            "status": "success",
            "target_nodes": [self._format_node(tid) for tid in valid_targets],
            "path": full_path,
            "skipped": skipped,
            "userKnowledgeGraph": user_knowledge_graph,
            "summary": {
                "total": len(full_path),
                "skipped": len(skipped),
                "target_ids": valid_targets,
                "target_names": target_names,
            },
        }

    def _llm_refine_intent(
        self,
        user_message: str,
        dialogue: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        candidate_text = "\n".join(
            [
                f'{c["node_id"]}: {c["name"]} | {c.get("summary", "")[:120]}'
                for c in candidates[:12]
            ]
        )

        history_text = "\n".join(dialogue.get("intent_history", [])[-6:])

        prompt = f"""
你要根据学生的多轮输入，判断他真正想学习的人工智能方向，并决定下一轮是否还需要追问。

学生历史输入：
{history_text}

学生最新输入：
{user_message}

当前从知识图谱中检索到的候选节点：
{candidate_text}

请输出 JSON，不要 Markdown。

输出格式：
{{
  "understood_goal": "",
  "need_more_clarification": true,
  "clarifying_question": "",
  "recommended_options": [],
  "target_node_ids": [],
  "reason": ""
}}

要求：
1. target_node_ids 只能从候选节点中选择，不能编造。
2. 如果学生只说“目标检测”“强化学习”“大模型”等宽泛方向，need_more_clarification 应该为 true。
3. 如果学生已经明确到具体应用或学习方式，例如“自动驾驶目标检测”“YOLO工程实现”“机器人强化学习控制”，可以给出 1 到 3 个 target_node_ids。
4. recommended_options 要是下一轮可点击选项，最后必须包含“我就确定是现在的方向了”。
5. clarifying_question 要自然，不要像搜索框提示，要像老师继续追问学生。
6. 如果需要继续追问，target_node_ids 可以先给最可能的候选节点。
"""

        result = _call_deepseek_json(prompt)

        if not result:
            return {
                "understood_goal": user_message,
                "need_more_clarification": True,
                "clarifying_question": "我大致理解你的方向了。你更希望偏算法原理、工程实现，还是某个具体应用场景？",
                "recommended_options": [
                    "偏算法原理",
                    "偏工程实现",
                    "偏自动驾驶/机器人应用",
                    "我就确定是现在的方向了",
                ],
                "target_node_ids": [c["node_id"] for c in candidates[:2]],
                "reason": "DeepSeek 未返回有效结果，使用规则兜底。",
            }

        valid_ids = {c["node_id"] for c in candidates}

        target_ids = [
            str(x)
            for x in result.get("target_node_ids", [])
            if str(x) in valid_ids
        ]

        options = result.get("recommended_options", [])

        if not isinstance(options, list):
            options = []

        options = [str(x) for x in options if str(x).strip()]

        if "我就确定是现在的方向了" not in options:
            options.append("我就确定是现在的方向了")

        return {
            "understood_goal": str(result.get("understood_goal", user_message)),
            "need_more_clarification": bool(
                result.get("need_more_clarification", True)
            ),
            "clarifying_question": str(
                result.get("clarifying_question", "你希望我继续往哪个方向细化？")
            ),
            "recommended_options": options[:6],
            "target_node_ids": target_ids or [c["node_id"] for c in candidates[:2]],
            "reason": str(result.get("reason", "")),
        }

    def _get_dialogue(self, thread_id: str) -> Dict[str, Any]:
        student = _load_student_state()
        sessions = student.setdefault("dialogue_sessions", {})

        if thread_id not in sessions:
            sessions[thread_id] = {
                "stage": "intent_refining",
                "intent_history": [],
                "candidate_nodes": [],
                "selected_nodes": [],
                "understood_goal": "",
                "preference": {},
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            _save_student_state(student)

        return sessions[thread_id]

    def _save_dialogue(self, thread_id: str, dialogue: Dict[str, Any]) -> None:
        student = _load_student_state()

        student.setdefault("dialogue_sessions", {})[thread_id] = dialogue

        student.setdefault("intent_history", []).append(
            {
                "thread_id": thread_id,
                "stage": dialogue.get("stage"),
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "latest_intent": dialogue.get("intent_history", [])[-1]
                if dialogue.get("intent_history")
                else "",
            }
        )

        _save_student_state(student)

    def _dialogue_path_ids(self, dialogue: Dict[str, Any], student: Dict[str, Any]) -> List[str]:
        path = dialogue.get("current_path")
        if not isinstance(path, list) or not path:
            path = student.get("current_path", [])
        return [str(node_id) for node_id in path if str(node_id) in self.node_by_id]

    def _dialogue_current_node(self, dialogue: Dict[str, Any], student: Dict[str, Any]) -> str:
        current = str(dialogue.get("current_node") or "").strip()
        path = self._dialogue_path_ids(dialogue, student)
        if not current:
            current = str(student.get("current_node") or "").strip()
        if current not in self.node_by_id:
            current = path[0] if path else ""
        return current

    def _format_path_for_dialogue(
        self,
        path: List[str],
        current_node: str = "",
        learned: Optional[Dict[str, Any]] = None,
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        learned = learned or {}
        mastery_scores = mastery_scores or {}
        formatted = []
        for node_id in path:
            if node_id not in self.node_by_id:
                continue
            threshold = float(self.node_by_id.get(node_id, {}).get("mastery_threshold") or 0.75)
            progress = _node_progress_from_student(
                {"learned_nodes": learned, "mastery_scores": mastery_scores},
                node_id,
                threshold=threshold,
            )
            if node_id == current_node:
                status = "current"
                reason = "当前正在学习的节点"
            elif node_id in learned or progress["mastered"]:
                status = "mastered"
                reason = "已经完成学习"
            else:
                status = "not_started"
                reason = "后续待学习节点"
            formatted.append(self._format_node(node_id, progress["mastery"], status, reason))
        return formatted

    def chat(
        self,
        thread_id: str,
        message: str = "",
        choice: str = "",
    ) -> Dict[str, Any]:
        message = (message or "").strip()
        choice = (choice or "").strip()
        user_text = message or choice

        dialogue = self._get_dialogue(thread_id)

        if choice in {"restart", "restart_keep_progress"} or user_text in {"重新开始", "重新规划"}:
            dialogue = {
                "stage": "intent_refining",
                "intent_history": [],
                "candidate_nodes": [],
                "selected_nodes": [],
                "understood_goal": "",
                "preference": {},
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            if choice == "restart_keep_progress":
                dialogue["replan_keep_progress"] = True

        stage = dialogue.get("stage", "intent_refining")

        if stage in {"intent", "clarify_target", "clarify_style", "confirm"}:
            stage = "intent_refining"
            dialogue["stage"] = "intent_refining"

        if not user_text and stage == "intent_refining":
            self._save_dialogue(thread_id, dialogue)

            return {
                "status": "success",
                "type": "question",
                "message": "你想学习人工智能中的哪个方向？可以说具体应用场景，也可以说算法方向。比如：自动驾驶目标检测、机器人强化学习、大语言模型RAG、机器学习基础。",
                "options": [
                    "自动驾驶目标检测",
                    "机器人强化学习",
                    "大语言模型与RAG",
                    "机器学习基础",
                ],
            }

        if stage == "intent_refining":
            if user_text:
                dialogue.setdefault("intent_history", []).append(user_text)

            confirm_now = user_text == "我就确定是现在的方向了"

            if confirm_now:
                selected_nodes = dialogue.get("selected_nodes", [])

                if not selected_nodes:
                    return {
                        "status": "success",
                        "type": "question",
                        "message": "现在还没有足够明确的目标节点。你再补充一下你想学的具体方向或应用场景。",
                        "options": [
                            "自动驾驶目标检测",
                            "YOLO工程实现",
                            "强化学习控制",
                            "RAG系统",
                        ],
                    }

                plan = self.build_plan(
                    selected_nodes,
                    skip_mastered=True,
                    keep_completed=bool(dialogue.get("replan_keep_progress")),
                )
                dialogue["stage"] = "planned"
                dialogue["latest_plan"] = plan.get("summary", {})
                dialogue["latest_path"] = plan.get("path", [])
                dialogue["current_path"] = [
                    node.get("node_id")
                    for node in plan.get("path", [])
                    if isinstance(node, dict) and node.get("node_id")
                ]
                dialogue["current_node"] = (
                    next(
                        (
                            node.get("node_id")
                            for node in plan.get("path", [])
                            if isinstance(node, dict) and node.get("status") == "current"
                        ),
                        "",
                    )
                    or (dialogue["current_path"][0] if dialogue["current_path"] else "")
                )
                dialogue["replan_keep_progress"] = False
                self._save_dialogue(thread_id, dialogue)

                return {
                    "status": "success",
                    "type": "plan",
                    "message": f"好的，我已经按“{dialogue.get('understood_goal', '当前方向')}”生成学习路径。路径会根据你的 AI 学生状态跳过已掌握节点，并保留薄弱和目标相关节点。",
                    **plan,
                }

            combined_query = " ".join(dialogue.get("intent_history", [])[-5:])

            extract = self._llm_extract_search_terms(combined_query, dialogue)

            candidate_map = {}

            for term in extract.get("search_terms", []):
                for item in self.search_nodes(term, limit=12):
                    candidate_map[item["node_id"]] = item

            for node_id in extract.get("candidate_node_ids", []):
                if node_id in self.node_by_id:
                    candidate_map[node_id] = self._format_node(node_id, reason="由 DeepSeek 从全图节点中判断为相关目标")

            candidates = list(candidate_map.values())[:12]

            if not candidates:
                self._save_dialogue(thread_id, dialogue)

                return {
                    "status": "success",
                    "type": "question",
                    "message": "我暂时没有匹配到足够明确的图谱节点。你可以换成更具体的说法，比如“目标检测”“YOLO”“强化学习控制”“RAG系统”。",
                    "options": [
                        "目标检测",
                        "YOLO工程应用",
                        "强化学习控制",
                        "RAG系统",
                    ],
                }

            refine = self._llm_refine_intent(user_text, dialogue, candidates)

            dialogue["candidate_nodes"] = [c["node_id"] for c in candidates]
            dialogue["selected_nodes"] = refine["target_node_ids"]
            dialogue["understood_goal"] = refine["understood_goal"]
            dialogue["last_reason"] = refine["reason"]
            dialogue["stage"] = "intent_refining"

            self._save_dialogue(thread_id, dialogue)

            selected_names = [
                self.node_by_id[nid]["name"]
                for nid in dialogue.get("selected_nodes", [])
                if nid in self.node_by_id
            ]

            prefix = ""

            if selected_names:
                prefix = f"我现在暂时把你的目标理解为：{'、'.join(selected_names)}。\n\n"

            return {
                "status": "success",
                "type": "question",
                "message": prefix + refine["clarifying_question"],
                "options": refine["recommended_options"],
                "candidates": candidates[:6],
                "selected_nodes": [
                    self._format_node(nid)
                    for nid in dialogue.get("selected_nodes", [])
                    if nid in self.node_by_id
                ],
            }

        if stage in {"planned", "learning"}:
            if user_text and any(k in user_text for k in ["调整", "重新规划", "不对", "换方向", "更偏"]):
                dialogue["stage"] = "intent_refining"
                dialogue.setdefault("intent_history", []).append(user_text)
                self._save_dialogue(thread_id, dialogue)

                return {
                    "status": "success",
                    "type": "question",
                    "message": "可以调整。你希望这条路径更偏基础、工程实现、算法原理，还是换一个具体应用方向？",
                    "options": [
                        "更偏基础",
                        "更偏工程实现",
                        "更偏算法原理",
                        "换一个应用方向",
                        "我就确定是现在的方向了",
                    ],
                }

            if user_text:
                return self.answer_current_node_question(thread_id, user_text)

            return {
                "status": "success",
                "type": "question",
                "message": "当前路径已经生成。你可以点击“开始学习当前节点”，也可以直接问我当前节点里的任何问题。",
                "options": [
                    "开始学习当前节点",
                    "调整路径",
                    "重新规划",
                ],
            }

        dialogue["stage"] = "intent_refining"
        self._save_dialogue(thread_id, dialogue)
        return self.chat(thread_id, user_text, choice)

    def get_node(self, node_id: str) -> Dict[str, Any]:
        if node_id not in self.node_by_id:
            return {"status": "error", "message": "节点不存在"}

        return {
            "status": "success",
            "node": self._format_node(node_id),
        }
    def teach_current_node(self, thread_id: str) -> Dict[str, Any]:
        student = _load_student_state()

        dialogue = self._get_dialogue(thread_id)
        dialogue["stage"] = "learning"
        self._save_dialogue(thread_id, dialogue)

        path = self._dialogue_path_ids(dialogue, student)
        current_node_id = self._dialogue_current_node(dialogue, student)

        if not current_node_id or current_node_id not in self.node_by_id:
            return {
                "status": "error",
                "message": "当前还没有可讲解的 AI 路径节点，请先生成学习路径。",
            }

        node = self._format_node(current_node_id)

        llm_result = self._build_node_lesson_with_llm(node)
        content = (llm_result or {}).get("lesson_markdown", "").strip()

        if not content:
            key_points = node.get("key_points", [])[:5]
            examples = node.get("examples", [])[:3]

            key_points_text = "\n".join([f"- {x}" for x in key_points]) if key_points else "- 暂无"
            examples_text = "\n".join([f"- {x}" for x in examples]) if examples else "- 暂无"

            content = f"""
    ### {node["name"]}

    {node.get("explanation_teacher_style", "")}

    #### 这个节点你需要重点掌握：

    {key_points_text}

    #### 典型例子：

    {examples_text}
    """

        content = self._polish_learning_output(
            node=node,
            draft=content,
            output_type="节点讲解",
        )
        content = self._render_learning_message(
            content=content,
            node=node,
            question=str(node.get("name", "")),
        )

        return {
            "status": "success",
            "type": "lesson",
            "node": node,
            "current_node": current_node_id,
            "path": self._format_path_for_dialogue(
                path,
                current_node_id,
                student.get("learned_nodes", {}) or {},
                student.get("mastery_scores", {}) or {},
            ),
            "message": content,
            "options": [
                *((llm_result or {}).get("options") or [
                    "我懂了，进入下一个节点",
                    "再讲简单一点",
                    "换一个例子",
                    "重新调整路径",
                ])
            ],
        }
    
    def answer_current_node_question(self, thread_id: str, question: str) -> Dict[str, Any]:
        student = _load_student_state()
        dialogue = self._get_dialogue(thread_id)
        path = self._dialogue_path_ids(dialogue, student)
        current_node_id = self._dialogue_current_node(dialogue, student)

        if not current_node_id or current_node_id not in self.node_by_id:
            return {
                "status": "error",
                "message": "当前还没有正在学习的 AI 节点，请先生成路径并开始学习。",
            }

        node = self._format_node(current_node_id)

        prompt = f"""
你是人工智能课程伴学老师。请基于当前知识点回答学生追问。

当前节点：
{node["name"]}

节点讲解：
{node.get("explanation_teacher_style", "")}

学习要点：
{node.get("key_points", [])}

典型例子：
{node.get("examples", [])}

学生问题：
{question}

要求：
1. 用中文回答。
2. 不要泛泛而谈，要围绕当前节点。
3. 如果学生问“再详细区分”“再讲简单点”“换个例子”，要直接响应。
4. 回答控制在 300 到 600 字。
5. 结尾给出一个自然的下一步建议。
"""

        result = _call_deepseek_json(f"""
请输出 JSON，不要 Markdown。

JSON 格式：
{{
  "answer": "",
  "options": []
}}

根据下面任务生成：
{prompt}

options 给 3 到 4 个下一步按钮，例如：
["我懂了，进入下一个节点", "再讲简单一点", "换一个例子", "重新调整路径"]
""")

        if result and result.get("answer"):
            answer = self._polish_learning_output(
                node=node,
                draft=str(result.get("answer", "")),
                output_type="追问回答",
                question=question,
            )
            answer = self._render_learning_message(
                content=answer,
                node=node,
                question=question,
            )
            return {
                "status": "success",
                "type": "lesson_qa",
                "message": answer,
                "options": result.get("options") or [
                    "我懂了，进入下一个节点",
                    "再讲简单一点",
                    "换一个例子",
                    "重新调整路径",
                ],
            }

        fallback_answer = (
            f"围绕“{node['name']}”来看，你这个问题可以从它的定义、作用和应用场景三方面理解。"
            f"{node.get('explanation_teacher_style', '')}"
        )
        fallback_answer = self._polish_learning_output(
            node=node,
            draft=fallback_answer,
            output_type="追问回答",
            question=question,
        )
        fallback_answer = self._render_learning_message(
            content=fallback_answer,
            node=node,
            question=question,
        )

        return {
            "status": "success",
            "type": "lesson_qa",
            "message": fallback_answer,
            "options": [
                "我懂了，进入下一个节点",
                "再讲简单一点",
                "换一个例子",
                "重新调整路径",
            ],
        }

    def advance_to_next_node(self, thread_id: str) -> Dict[str, Any]:
        student = _load_student_state()

        dialogue = self._get_dialogue(thread_id)
        path = self._dialogue_path_ids(dialogue, student)
        current = self._dialogue_current_node(dialogue, student)

        if not path or current not in path:
            return {
                "status": "error",
                "message": "当前没有可推进的学习路径。",
            }

        learned = student.setdefault("learned_nodes", {})
        mastery_scores = student.setdefault("mastery_scores", {})

        learned[current] = {
            "mastery": 0.85,
            "status": "completed",
            "finish_time": datetime.now().isoformat(timespec="seconds"),
        }
        mastery_scores[current] = 0.85

        idx = path.index(current)
        next_idx = idx + 1
        auto_skipped = []

        while next_idx < len(path):
            candidate_node = path[next_idx]
            if candidate_node not in self.node_by_id:
                next_idx += 1
                continue
            threshold = float(
                self.node_by_id.get(candidate_node, {}).get("mastery_threshold") or 0.75
            )
            progress = _node_progress_from_student(student, candidate_node, threshold=threshold)
            if not progress["mastered"]:
                break
            auto_skipped.append(
                self._format_node(
                    candidate_node,
                    progress["mastery"],
                    "mastered",
                    "auto skipped because the node is already mastered",
                )
            )
            next_idx += 1

        if next_idx >= len(path):
            student["current_node"] = ""
            dialogue["current_node"] = ""
            dialogue["latest_path"] = self._format_path_for_dialogue(
                path,
                "",
                learned,
                mastery_scores,
            )
            _save_student_state(student)
            self._save_dialogue(thread_id, dialogue)

            return {
                "status": "success",
                "type": "complete",
                "message": "这条学习路径已经完成。你可以重新规划新的人工智能学习方向。",
                "path": [
                    self._format_node(node_id, mastery_scores.get(node_id, 0.0), "mastered", "已完成")
                    for node_id in path
                    if node_id in self.node_by_id
                ],
                "options": ["重新规划", "调整路径"],
            }

        next_node = path[next_idx]
        student["current_node"] = next_node
        dialogue["current_node"] = next_node
        dialogue["current_path"] = path
        _save_student_state(student)
        self._save_dialogue(thread_id, dialogue)

        lesson = self.teach_current_node(thread_id)

        lesson["path"] = []
        for node_id in path:
            progress = _node_progress_from_student(
                student,
                node_id,
                threshold=float(
                    self.node_by_id.get(node_id, {}).get("mastery_threshold") or 0.75
                ),
            )
            mastery = progress["mastery"]

            if node_id == next_node:
                status = "current"
                reason = "当前正在学习的节点"
            elif node_id in learned or progress["mastered"]:
                status = "mastered"
                reason = "已经完成学习"
            else:
                status = "not_started"
                reason = "后续待学习节点"

            lesson["path"].append(
                self._format_node(node_id, mastery, status, reason)
            )

        lesson["current_node"] = next_node
        dialogue["latest_path"] = lesson["path"]
        self._save_dialogue(thread_id, dialogue)
        lesson["skipped"] = auto_skipped
        return lesson

_service = None


def get_ai_path_service() -> AILearningPathService:
    global _service

    if _service is None:
        _service = AILearningPathService()

    return _service
