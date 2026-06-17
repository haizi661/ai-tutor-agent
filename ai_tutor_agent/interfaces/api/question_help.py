from __future__ import annotations

import base64
import uuid
from dataclasses import replace
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from langchain_core.messages import HumanMessage, SystemMessage

from ...config import DEFAULT_QUESTION_HELP_MODEL, QWEN_OPENAI_COMPATIBLE_BASE
from ...core.events import make_event
from ...core.text import content_to_text
from ...infrastructure.llm import build_llms
from ...knowledge_map.student_state import StudentStateStore, now_ts
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["question_help"])

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_COUNT = 4
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}

QUESTION_HELP_MODES = {
    "quick": {
        "label": "快速解答",
        "instruction": "优先简洁直接：先给结论，再给 2-3 个关键步骤，避免长篇展开。",
    },
    "deep": {
        "label": "深度解析",
        "instruction": "适合复杂题：补足推导、关键条件、符号含义和判断边界；必要时用表格对比易混概念。",
    },
    "vision": {
        "label": "图片题专用",
        "instruction": "优先识别图片中的题干、图表、选项和符号；看不清的内容必须说明，不要猜测。",
    },
}


def _normalize_answer_mode(value: str = "", *, has_images: bool = False) -> str:
    mode = str(value or "").strip().lower()
    if mode in QUESTION_HELP_MODES:
        return mode
    return "vision" if has_images else "quick"


def _load_store(request: Request) -> StudentStateStore:
    runtime = get_runtime(request)
    store = getattr(runtime, "student_state_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Student state store not available")
    return store


async def _read_images(images: Optional[list[UploadFile]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    image_parts: list[dict[str, Any]] = []
    image_meta: list[dict[str, Any]] = []
    for index, upload in enumerate(list(images or [])[:MAX_IMAGE_COUNT], start=1):
        content_type = (upload.content_type or "").strip().lower()
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Only png, jpeg, webp, and gif images are supported")
        data = await upload.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail="Image is too large")
        data_url = f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}"
        filename = upload.filename or f"image-{index}"
        image_parts.append({"type": "image_url", "image_url": {"url": data_url}})
        image_meta.append({"filename": filename, "content_type": content_type, "size": len(data)})
    return image_parts, image_meta


def _build_node_context(node_id: str = "", node_name: str = "") -> str:
    if node_id and node_name:
        return f"\n当前你正在学习知识点：【{node_name}】（{node_id}）。如果题目涉及该知识点的概念，尽量结合该节点内容讲解。"
    if node_name:
        return f"\n当前你正在学习：{node_name}。请结合这个知识点来解答。"
    return ""


def _build_question_help_messages(
    question_text: str,
    image_parts: list[dict[str, Any]],
    *,
    node_id: str = "",
    node_name: str = "",
    answer_mode: str = "quick",
) -> list[object]:
    text = question_text.strip() or "用户上传了一道图片题，请先识别题目内容，再给出解题步骤。"
    node_context = _build_node_context(node_id, node_name)
    mode = _normalize_answer_mode(answer_mode, has_images=bool(image_parts))
    mode_meta = QUESTION_HELP_MODES[mode]
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "请解答这道自动控制或相关课程题目。要求：\n"
                f"当前解答方式：{mode_meta['label']}。{mode_meta['instruction']}\n"
                "请严格使用以下 Markdown 小节标题，不要改名：\n"
                "### 考点\n"
                "### 解题步骤\n"
                "### 最终答案\n"
                "### 易错提醒\n"
                "内容要求：\n"
                "1. 考点：先概括题目考察的概念或方法。\n"
                "2. 解题步骤：给出关键步骤、关键判断、计算步骤或代入关系，单段不要超过 90 个汉字。\n"
                "3. 最终答案：明确答案，不要只给过程；如果是选择题，必须写出选项字母和选项原文。\n"
                "4. 易错提醒：说明最容易混淆的条件、符号或概念；选择题至少解释关键干扰项为什么错。\n"
                "5. 公式必须使用 Markdown/LaTeX，行内公式用 \\(...\\)，行间公式用 $$...$$，例如 $$G(s)=\\frac{C(s)}{R(s)}$$。\n"
                "6. 如果信息不足，说明缺少什么条件，不要编造看不见的参数或图像信息。\n"
                f"题目内容：{text}"
                f"{node_context}"
            ),
        }
    ]
    content.extend(image_parts)
    return [
        SystemMessage(content="你是严谨的课程题目答疑老师，回答要面向学生、步骤清楚、不要编造看不见的条件。"),
        HumanMessage(content=content),
    ]


def _build_main_chat_llm(settings: Any):
    """使用当前主聊天配置构建 LLM（纯文本题目优先用）。"""
    tutor_llm, _, _ = build_llms(settings)
    return tutor_llm


def _invoke_question_help_llm(runtime: Any, messages: list[object]) -> str:
    """优先使用主聊天模型（文本题），有多模态需要时用 Qwen。"""
    errors: list[str] = []

    # 1. 已缓存的专有 question_help_llm
    llm = getattr(runtime, "question_help_llm", None)
    if llm is not None:
        try:
            response = llm.invoke(messages)
            answer = content_to_text(getattr(response, "content", response)).strip()
            if answer:
                return answer
        except Exception as e:
            errors.append(f"question_help_llm: {e}")

    # 2. 纯文本题走主聊天模型（非多模态，通常更稳定/有权限）
    if not _has_image_content(messages):
        try:
            llm = _build_main_chat_llm(runtime.settings)
            response = llm.invoke(messages)
            answer = content_to_text(getattr(response, "content", response)).strip()
            if answer:
                return answer
        except Exception as e:
            errors.append(f"chat LLM: {e}")

    # 3. 图片题或主模型失败 → fallback Qwen 多模态
    try:
        llm = _build_question_help_llm(runtime.settings)
        response = llm.invoke(messages)
        answer = content_to_text(getattr(response, "content", response)).strip()
        if answer:
            return answer
    except Exception as e:
        errors.append(f"Qwen 多模态模型: {e}")

    error_detail = "；".join(errors)
    return (
        f"抱歉，题目答疑生成失败，所有模型均无法返回有效解答。\n\n"
        f"错误详情：{error_detail}\n\n"
        f"常见解决方法：\n"
        f"1. 检查 API Key 是否有效（QWEN_API_KEY / OPENAI_API_KEY）\n"
        f"2. 检查模型名是否正确（如 qwen-vl-max）\n"
        f"3. 检查网络连接是否正常\n"
        f"4. 更换提问方式或稍后重试"
    )


def _has_image_content(messages: list[object]) -> bool:
    for msg in messages:
        if hasattr(msg, "content") and isinstance(msg.content, list):
            for part in msg.content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    return True
    return False


def _build_question_help_llm(settings: Any):
    qwen_api_key = getattr(settings, "qwen_api_key", None)
    if not qwen_api_key:
        raise RuntimeError("Question help requires QWEN_API_KEY because it uses Qwen multimodal models.")

    question_help_settings = replace(
        settings,
        chat_profile="qwen",
        llm_provider="openai",
        openai_api_key=qwen_api_key,
        openai_api_base=(
            getattr(settings, "question_help_openai_api_base", "")
            or QWEN_OPENAI_COMPATIBLE_BASE
        ),
        model_name=(
            getattr(settings, "question_help_model_name", "")
            or DEFAULT_QUESTION_HELP_MODEL
        ),
    )
    tutor_llm, _, _ = build_llms(question_help_settings)
    return tutor_llm


@router.get("/students/{student_id}/question-help")
async def list_question_help_records(student_id: str, request: Request, limit: int = 50):
    store = _load_store(request)
    try:
        state = store.load(student_id)
    except Exception:
        return {"items": [], "total": 0}
    records = list(getattr(state, "question_help_records", []) or [])
    records = records[-max(1, min(int(limit or 50), 80)):]
    records.reverse()
    return {"items": records, "total": len(getattr(state, "question_help_records", []) or [])}


@router.post("/students/{student_id}/question-help")
async def answer_question_help(
    student_id: str,
    request: Request,
    question_text: str = Form(""),
    images: Optional[list[UploadFile]] = File(None),
    current_node_id: str = Form(""),
    current_node_name: str = Form(""),
    answer_mode: str = Form("quick"),
):
    clean_text = str(question_text or "").strip()
    image_parts, image_meta = await _read_images(images)
    if not clean_text and not image_parts:
        raise HTTPException(status_code=400, detail="Please provide question text or at least one image")

    runtime = get_runtime(request)
    node_id = str(current_node_id or "").strip()
    node_name = str(current_node_name or "").strip()
    normalized_mode = _normalize_answer_mode(answer_mode, has_images=bool(image_parts))
    mode_label = QUESTION_HELP_MODES[normalized_mode]["label"]
    messages = _build_question_help_messages(
        clean_text,
        image_parts,
        node_id=node_id,
        node_name=node_name,
        answer_mode=normalized_mode,
    )
    try:
        answer = _invoke_question_help_llm(runtime, messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Question help generation failed: {exc}") from exc

    record = {
        "record_id": f"qh-{uuid.uuid4().hex[:12]}",
        "question_text": clean_text,
        "answer": answer,
        "images": image_meta,
        "image_count": len(image_meta),
        "created_at": now_ts(),
        "source": "question_help",
        "node_id": node_id,
        "node_name": node_name,
        "answer_mode": normalized_mode,
        "answer_mode_label": mode_label,
    }
    if node_id:
        record["node_id"] = node_id
        record["node_name"] = node_name
    store = _load_store(request)
    state = store.update(student_id, lambda s: s.qh_add_record(record))
    records = list(getattr(state, "question_help_records", []) or [])

    # 同步到事件系统，让主聊天界面也知道这次回答
    if hasattr(runtime, "event_sink") and runtime.event_sink:
        runtime.event_sink.emit(
            make_event("question_help.answered", "question_help",
                       message="题目答疑已完成。",
                       data={"record_id": record["record_id"], "node_id": node_id})
        )

    return {"record": record, "records": list(reversed(records[-50:])), "total": len(records)}
