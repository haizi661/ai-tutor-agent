from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

from openai import OpenAI


class QwenVisualAnalyzer:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-vl-max-latest",
        timeout: float = 20.0,
    ) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def describe_image(
        self,
        image_path: str | Path,
        *,
        node_name: str = "",
        caption: str = "",
        question: str = "",
    ) -> str:
        result = self.analyze_figure(
            image_path,
            node_name=node_name,
            caption=caption,
            question=question,
        )
        return str(result.get("visual_summary", "") or "").strip()

    def analyze_figure(
        self,
        image_path: str | Path,
        *,
        node_name: str = "",
        caption: str = "",
        question: str = "",
    ) -> dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            return {}

        try:
            image_data_url = self._build_data_url(path)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是自动控制原理课程的图像标注助手。"
                            "请只根据图中可见内容生成结构化中文标注，不要臆测看不清的细节。"
                            "重点提取可用于教学引用的结构、趋势、坐标含义、参数变化和控制流程信息。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "请输出一个 JSON 对象，不要输出解释文字。\n"
                                    "字段要求：\n"
                                    "- visual_summary: 1-2 句，概括这张图最值得在教学中引用的视觉信息\n"
                                    "- visual_key_elements: 数组，列出图中的关键对象/曲线/坐标/模块，最多 6 项\n"
                                    "- visual_relations: 数组，列出图中直接可读出的关系或趋势，最多 4 项\n"
                                    "- teaching_focus: 数组，列出教师讲解时最值得强调的点，最多 4 项\n"
                                    "- confidence: 0 到 1 之间的小数\n\n"
                                    f"当前节点：{node_name or '未知节点'}\n"
                                    f"图注：{caption or '无'}\n"
                                    f"用户问题：{question or '无'}"
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data_url},
                            },
                        ],
                    },
                ],
            )
        except Exception:
            return {}

        payload = self._extract_message_text(response)
        parsed = self._parse_json_payload(payload)
        if not parsed:
            fallback_summary = self._normalize_text(payload)
            if not fallback_summary:
                return {}
            return {
                "visual_summary": fallback_summary,
                "visual_key_elements": [],
                "visual_relations": [],
                "teaching_focus": [],
                "confidence": 0.35,
                "vision_model": self.model,
            }

        return {
            "visual_summary": self._normalize_text(parsed.get("visual_summary", "")),
            "visual_key_elements": self._normalize_list(parsed.get("visual_key_elements", []), limit=6),
            "visual_relations": self._normalize_list(parsed.get("visual_relations", []), limit=4),
            "teaching_focus": self._normalize_list(parsed.get("teaching_focus", []), limit=4),
            "confidence": self._normalize_confidence(parsed.get("confidence")),
            "vision_model": self.model,
        }

    def _extract_message_text(self, response: Any) -> str:
        message = response.choices[0].message.content if getattr(response, "choices", None) else ""
        if isinstance(message, str):
            return message.strip()
        if isinstance(message, list):
            parts = [part.get("text", "").strip() for part in message if isinstance(part, dict)]
            return " ".join(part for part in parts if part).strip()
        return ""

    def _parse_json_payload(self, payload: str) -> dict[str, Any]:
        text = str(payload or "").strip()
        if not text:
            return {}
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            text = fenced.group(1).strip()
        else:
            bracketed = re.search(r"(\{.*\})", text, flags=re.DOTALL)
            if bracketed:
                text = bracketed.group(1).strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _normalize_text(self, value: Any) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:240]

    def _normalize_list(self, values: Any, *, limit: int) -> list[str]:
        if isinstance(values, str):
            raw_items = re.split(r"[；;。,\n]", values)
        elif isinstance(values, list):
            raw_items = [str(item or "") for item in values]
        else:
            raw_items = []
        results: list[str] = []
        for item in raw_items:
            cleaned = self._normalize_text(item)
            if not cleaned or cleaned in results:
                continue
            results.append(cleaned)
            if len(results) >= limit:
                break
        return results

    def _normalize_confidence(self, value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(confidence, 1.0))

    def _build_data_url(self, image_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(str(image_path))
        mime_type = mime_type or "image/png"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"
