from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

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
        path = Path(image_path)
        if not path.exists():
            return ""

        try:
            image_data_url = self._build_data_url(path)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一名自动控制课程助教。"
                            "请用中文简洁描述图中的关键结构、曲线趋势、坐标含义或可用于教学分析的要点。"
                            "不要臆造看不清的细节，控制在两句话内。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"当前节点：{node_name or '未知节点'}\n"
                                    f"图注：{caption or '无'}\n"
                                    f"用户问题：{question or '无'}\n"
                                    "请提炼这张图最值得在答案中结合分析的视觉信息。"
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
            return ""

        message = response.choices[0].message.content if response.choices else ""
        if isinstance(message, str):
            return message.strip()
        if isinstance(message, list):
            parts = [part.get("text", "").strip() for part in message if isinstance(part, dict)]
            return " ".join(part for part in parts if part).strip()
        return ""

    def _build_data_url(self, image_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(str(image_path))
        mime_type = mime_type or "image/png"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"
