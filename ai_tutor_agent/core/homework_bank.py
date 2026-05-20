from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .learning_support import build_homework_items
from .text import content_to_text


def collect_relevant_node_ids(
    snapshot: dict[str, Any] | None,
    *,
    current_node_id: str = "",
    graph_anchor_id: str = "",
) -> list[str]:
    node_ids: list[str] = []
    for raw in (current_node_id, graph_anchor_id):
        value = str(raw or "").strip()
        if value and value not in node_ids:
            node_ids.append(value)

    values = dict(snapshot or {})
    for nid in list(values.get("wrong_nodes") or []):
        nid_str = str(nid).strip()
        if nid_str and nid_str not in node_ids:
            node_ids.append(nid_str)
    for nid in list(values.get("visited_nodes") or [])[::-1]:
        nid_str = str(nid).strip()
        if nid_str and nid_str not in node_ids:
            node_ids.append(nid_str)
    daily = dict(values.get("daily_learning_records") or {})
    for day_nodes in daily.values():
        for nid in list(day_nodes or []):
            nid_str = str(nid).strip()
            if nid_str and nid_str not in node_ids:
                node_ids.append(nid_str)
    return node_ids


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    text = str(values or "").strip()
    return [text] if text else []


def _question_excerpt(item: dict[str, Any], *, limit: int = 220) -> str:
    blocks = item.get("content_blocks") or []
    parts: list[str] = []
    if isinstance(blocks, list):
        for block in blocks:
            if str((block or {}).get("block_type") or "") != "text":
                continue
            text = str((block or {}).get("content") or "")
            text = re.sub(r"<[^>]+>", " ", text)
            text = " ".join(text.split())
            if not text:
                continue
            parts.append(text)
            if len(" ".join(parts)) >= limit:
                break
    excerpt = " ".join(parts).strip()
    if excerpt:
        return excerpt[:limit]
    return str(item.get("prompt") or item.get("stem") or item.get("question") or "").strip()[:limit]


def _build_node_contexts(graph_pipeline: Any, relevant_node_ids: list[str]) -> list[dict[str, Any]]:
    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    contexts: list[dict[str, Any]] = []
    for node_id in relevant_node_ids:
        raw_node = node_map.get(node_id) or {}
        title = str(raw_node.get("name") or raw_node.get("title") or node_id).strip()
        strong_terms: list[str] = []
        for value in (
            title,
            *_string_list(raw_node.get("core_concepts"))[:4],
            *_string_list(raw_node.get("key_points"))[:4],
            *_string_list(raw_node.get("formulas"))[:3],
        ):
            text = str(value or "").strip()
            if text and text not in strong_terms:
                strong_terms.append(text)
        contexts.append(
            {
                "node_id": node_id,
                "title": title,
                "terms": strong_terms,
                "blob": " ".join(strong_terms),
            }
        )
    return contexts


def _score_runtime_question(item: dict[str, Any], node_contexts: list[dict[str, Any]]) -> tuple[int, dict[str, Any] | None]:
    item_tags = _string_list(item.get("knowledge_tags"))[:6]
    item_title = str(item.get("section_title") or "").strip()
    item_text = " ".join(filter(None, [item_title, " ".join(item_tags), _question_excerpt(item)])).strip()

    best_score = -1
    best_context: dict[str, Any] | None = None
    for index, context in enumerate(node_contexts):
        score = max(0, 24 - index * 4)
        blob = context.get("blob") or ""
        title = str(context.get("title") or "")
        for tag in item_tags:
            if tag and (tag in blob or any(tag in term or term in tag for term in context.get("terms") or [])):
                score += 18
        if title and title in item_text:
            score += 14
        for term in context.get("terms") or []:
            if term and term in item_text:
                score += 6
        if score > best_score:
            best_score = score
            best_context = context
    if best_score < 0:
        return 0, None
    return best_score, best_context


def _query_terms(values: list[str] | None) -> list[str]:
    seen: list[str] = []
    for raw in values or []:
        text = " ".join(str(raw or "").split()).strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def _score_query_match(item: dict[str, Any], query_terms: list[str]) -> int:
    if not query_terms:
        return 0
    item_tags = _string_list(item.get("knowledge_tags"))[:6]
    item_title = str(item.get("section_title") or "").strip()
    item_text = " ".join(filter(None, [item_title, " ".join(item_tags), _question_excerpt(item)])).strip()
    score = 0
    for index, term in enumerate(query_terms):
        weight = max(4, 18 - index * 2)
        if term and term in item_text:
            score += weight
        for tag in item_tags:
            if term and tag and (term in tag or tag in term):
                score += weight + 4
    return score


def _llm_pick_runtime_questions(
    llm: Any,
    *,
    candidates: list[dict[str, Any]],
    node_contexts: list[dict[str, Any]],
    limit: int,
) -> list[str]:
    if llm is None or not candidates:
        return []

    context_lines = []
    for context in node_contexts[:4]:
        terms = "；".join((context.get("terms") or [])[:6])
        context_lines.append(f"- {context.get('node_id')}: {context.get('title')}；关键点：{terms}")
    candidate_lines = []
    for item in candidates:
        tags = "、".join(_string_list(item.get("knowledge_tags"))[:4]) or "无"
        candidate_lines.append(
            f"- {item.get('library_id')}: 题号 {item.get('question_id')}；"
            f"标签 {tags}；题型 {item.get('question_type') or '未知'}；"
            f"题干摘要 { _question_excerpt(item, limit=140) }"
        )

    prompt = (
        "你是一位自动控制原理助教。请从候选题库题中挑选最适合作为本轮课后作业的题目。"
        "优先选择与当前学习节点、错误节点或最近学习内容最相关的题。"
        f"只选 1 到 {limit} 道题，并只返回 JSON。\n\n"
        "当前学习节点：\n"
        + "\n".join(context_lines)
        + "\n\n候选题：\n"
        + "\n".join(candidate_lines)
        + '\n\n输出格式：{"selected_library_ids": ["id1", "id2"]}'
    )
    try:
        response = llm.invoke(
            [
                SystemMessage(content="你是严谨的题目筛选助手，只输出 JSON。"),
                HumanMessage(content=prompt),
            ]
        )
        text = content_to_text(response).strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return []
        import json

        payload = json.loads(match.group(0))
        selected = payload.get("selected_library_ids") or []
        if not isinstance(selected, list):
            return []
        seen: list[str] = []
        valid_ids = {str(item.get("library_id") or "").strip() for item in candidates}
        for raw in selected:
            value = str(raw or "").strip()
            if value and value in valid_ids and value not in seen:
                seen.append(value)
        return seen[:limit]
    except Exception:
        return []


def _normalize_options(raw: Any) -> dict[str, str]:
    if isinstance(raw, dict):
        return {
            str(key).strip().upper(): str(value).strip()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }
    if isinstance(raw, list):
        result: dict[str, str] = {}
        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for index, value in enumerate(raw):
            text = str(value or "").strip()
            if text:
                result[labels[index]] = text
        return result
    return {}


def _adapt_runtime_question_to_homework(
    item: dict[str, Any],
    *,
    matched_context: dict[str, Any] | None,
    fallback_node_id: str = "",
) -> dict[str, Any]:
    node_id = str((matched_context or {}).get("node_id") or fallback_node_id or "").strip()
    node_title = str((matched_context or {}).get("title") or item.get("section_title") or node_id or "").strip()
    options = _normalize_options(item.get("options"))
    block_images = [
        str((block or {}).get("content") or "").strip()
        for block in (item.get("content_blocks") or [])
        if str((block or {}).get("block_type") or "") == "image" and str((block or {}).get("content") or "").strip()
    ]
    media_refs = [
        *block_images,
        *[str(value).strip() for value in (item.get("image_refs") or []) if str(value).strip()],
    ]
    seen_media: list[str] = []
    dedup_media: list[str] = []
    for value in media_refs:
        if value not in seen_media:
            seen_media.append(value)
            dedup_media.append(value)

    tags = _string_list(item.get("knowledge_tags"))[:4]
    reference_answer = str(item.get("answer") or "").strip()
    homework_item = {
        "question_id": f"QB-{item.get('library_id') or item.get('question_id') or node_id or '1'}",
        "source_question_id": str(item.get("question_id") or "").strip(),
        "question_bank_library_id": str(item.get("library_id") or "").strip(),
        "node_id": node_id,
        "graph_node_id": node_id,
        "covered_node_ids": [node_id] if node_id else [],
        "node_title": node_title,
        "title": str(item.get("section_title") or node_title or item.get("question_type") or "题库作业").strip(),
        "type": "objective" if options else "subjective_review",
        "source": "processed_question_bank",
        "prompt": _question_excerpt(item, limit=260) or node_title,
        "reference_answer": reference_answer,
        "rubric": tags or _string_list((matched_context or {}).get("terms"))[:4],
        "source_refs": [str(value).strip() for value in (item.get("source_files") or []) if str(value).strip()][:3],
        "media_refs": dedup_media,
        "content_blocks": list(item.get("content_blocks") or []),
        "options": options or None,
        "option_images": list(item.get("option_images") or []) or None,
        "question_type": str(item.get("question_type") or "").strip(),
        "knowledge_tags": tags,
        "section_title": str(item.get("section_title") or "").strip(),
        "suppress_reference_answer": True,
    }
    if options:
        normalized_answer = reference_answer.upper()
        if normalized_answer in options:
            homework_item["answer_key"] = normalized_answer
    return homework_item


def select_question_bank_homework_items(
    *,
    question_bank_provider: Any,
    graph_pipeline: Any,
    relevant_node_ids: list[str],
    query_terms: list[str] | None = None,
    llm: Any = None,
    limit: int = 2,
) -> list[dict[str, Any]]:
    if question_bank_provider is None or not hasattr(question_bank_provider, "list_runtime_question_bank_items"):
        return []

    runtime_items = list(question_bank_provider.list_runtime_question_bank_items() or [])
    if not runtime_items:
        return []

    node_contexts = _build_node_contexts(graph_pipeline, relevant_node_ids)
    normalized_query_terms = _query_terms(query_terms)
    scored: list[tuple[int, dict[str, Any], dict[str, Any] | None]] = []
    for item in runtime_items:
        score, matched = _score_runtime_question(item, node_contexts)
        score += _score_query_match(item, normalized_query_terms)
        scored.append((score, item, matched))
    scored.sort(
        key=lambda entry: (
            entry[0],
            len(_string_list(entry[1].get("knowledge_tags"))),
            -len(_question_excerpt(entry[1])),
        ),
        reverse=True,
    )

    positive = [entry for entry in scored if entry[0] > 0]
    shortlist = positive[: max(limit * 3, 6)] if positive else scored[: max(limit * 2, 4)]
    candidates = [entry[1] for entry in shortlist]
    selected_ids = _llm_pick_runtime_questions(
        llm,
        candidates=candidates,
        node_contexts=node_contexts,
        limit=limit,
    )

    selected_entries: list[tuple[int, dict[str, Any], dict[str, Any] | None]] = []
    if selected_ids:
        selected_set = set(selected_ids)
        selected_entries = [entry for entry in shortlist if str(entry[1].get("library_id") or "").strip() in selected_set]
    if not selected_entries:
        selected_entries = shortlist[:limit]

    fallback_node_id = relevant_node_ids[0] if relevant_node_ids else ""
    return [
        _adapt_runtime_question_to_homework(item, matched_context=matched, fallback_node_id=fallback_node_id)
        for _score, item, matched in selected_entries[:limit]
    ]


def build_curated_homework_items(
    *,
    question_bank_provider: Any,
    graph_pipeline: Any,
    student_state_snapshot: dict[str, Any] | None,
    query_terms: list[str] | None = None,
    llm: Any = None,
    current_node_id: str = "",
    graph_anchor_id: str = "",
    limit: int = 2,
) -> list[dict[str, Any]]:
    snapshot = dict(student_state_snapshot or {})
    relevant_node_ids = collect_relevant_node_ids(
        snapshot,
        current_node_id=current_node_id,
        graph_anchor_id=graph_anchor_id,
    )

    homework_items: list[dict[str, Any]] = []
    if question_bank_provider is not None:
        homework_items = select_question_bank_homework_items(
            question_bank_provider=question_bank_provider,
            graph_pipeline=graph_pipeline,
            relevant_node_ids=relevant_node_ids,
            query_terms=query_terms,
            llm=llm,
            limit=limit,
        )
    if homework_items:
        return homework_items
    return build_homework_items(
        graph_pipeline=graph_pipeline,
        student_state_snapshot=snapshot,
        limit=limit,
    )
