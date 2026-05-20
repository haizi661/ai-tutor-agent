from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


class TeacherStyleGenerator:
    """
    使用 DeepSeek 生成老师讲解风格内容。
    当前先生成：
    1. explanation_teacher_style
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

    def generate_explanation(
        self,
        node_name: str,
        summary: str,
        definition_texts: list[str],
        keypoint_texts: list[str],
        formula_texts: list[str],
        example_texts: list[str],
    ) -> str:
        definition_block = "\n".join([f"- {x}" for x in definition_texts if x])
        keypoint_block = "\n".join([f"- {x}" for x in keypoint_texts if x])
        formula_block = "\n".join([f"- {x}" for x in formula_texts if x])
        example_block = "\n".join([f"- {x}" for x in example_texts if x])

        prompt = f"""
你现在是一名讲授《自动控制原理》的大学老师，请根据给定材料，用更适合学生理解的中文讲解知识点。

要求：
1. 用老师上课讲解的语气，但不要太口语化。
2. 先解释“这是什么”，再讲“为什么重要/有什么作用”，最后补充“学习时应注意什么”。
3. 尽量把 OCR 乱码自动忽略，不要原样输出明显乱码。
4. 不要照抄原文，要整合重写。
5. 输出一段 200~350 字的讲解，不要分点。

知识点名称：
{node_name}

已有 summary：
{summary}

定义候选：
{definition_block}

重点候选：
{keypoint_block}

公式候选：
{formula_block}

例子候选：
{example_block}
""".strip()

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一名自动控制原理课程教师。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        return resp.choices[0].message.content.strip()