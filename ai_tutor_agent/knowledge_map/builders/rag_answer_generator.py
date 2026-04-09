from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


class RagAnswerGenerator:
    """
    基于检索证据生成最终问答答案。
    """

    def __init__(self) -> None:
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise ValueError("未读取到 DEEPSEEK_API_KEY，请检查 .env 配置。")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self.model_name = "deepseek-chat"

    def generate_answer(
        self,
        question: str,
        node_name: str,
        contexts: list[str],
    ) -> str:
        context_block = "\n".join([f"- {x}" for x in contexts if x])

        prompt = f"""
你是一名《自动控制原理》课程教师，请根据给定检索证据回答学生问题。

要求：
1. 只围绕证据回答，不要乱编。
2. 语言要像老师讲解，清楚、自然。
3. 先直接回答问题，再补充必要解释。
4. 如果证据里有明显 OCR 乱码，请忽略，不要原样输出。
5. 输出 200~350 字。

当前知识点：
{node_name}

学生问题：
{question}

检索证据：
{context_block}
""".strip()

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一名自动控制原理课程教师。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return resp.choices[0].message.content.strip()