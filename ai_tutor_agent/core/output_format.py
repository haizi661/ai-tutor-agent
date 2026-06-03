from __future__ import annotations

import json
import re
from typing import Any, Optional

from .events import make_event


def strip_code_fences(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def parse_json_object(text: str) -> dict[str, Any] | None:
    cleaned = strip_code_fences(text)
    if not cleaned:
        return None

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def collapse_blank_lines(text: str) -> str:
    lines = [line.rstrip() for line in (text or "").replace("\r\n", "\n").split("\n")]
    output: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if blank:
                continue
            blank = True
            output.append("")
            continue
        blank = False
        output.append(line.strip())
    return "\n".join(output).strip()


def split_sentences(text: str) -> list[str]:
    cleaned = collapse_blank_lines(text)
    if not cleaned:
        return []

    pieces = re.split(r"(?<=[。！？!?])\s*", cleaned)
    sentences = []
    for piece in pieces:
        normalized = piece.strip().strip("-").strip()
        if normalized:
            sentences.append(normalized)
    return sentences


def stream_text_chunks(
    event_sink,
    source: str,
    text: str,
    *,
    chunk_size: int = 120,
    kind: Optional[str] = None,
) -> None:
    """Stream text chunks as ``node.stream`` events.

    ``kind`` lets callers tag the payload (e.g. ``"graph_rag_answer"``) so the
    frontend can route the chunks to the matching renderer. Omitting ``kind``
    preserves the legacy behaviour where the frontend falls back to
    ``turnRoleForSource(source)``.
    """
    payload = text or ""
    for start in range(0, len(payload), chunk_size):
        chunk = payload[start:start + chunk_size]
        data: dict = {"text": chunk}
        if kind is not None:
            data["kind"] = kind
        event_sink.emit(make_event("node.stream", source, data=data))
