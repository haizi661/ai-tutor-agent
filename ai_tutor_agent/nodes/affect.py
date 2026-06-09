"""学生情绪信号检测模块。

对每轮用户消息做关键词匹配，识别六类情绪信号：
  frustrated — 受挫、卡住
  confident  — 有信心、已理解
  curious    — 好奇、想深入
  passive    — 敷衍、意愿低
  confused   — 困惑、混乱
  anxious    — 焦虑、着急

当 LLM 可用时，优先使用 LLM 结构化输出做分类，输出统一 labels：
confused / anxious / confident / neutral。
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field


class AffectResult(BaseModel):
    """LLM 对学生情绪的分类结果，输出 0-1 置信度。"""
    confused: float = Field(default=0.0, description="困惑/混乱/不理解")
    anxious: float = Field(default=0.0, description="焦虑/受挫/着急")
    confident: float = Field(default=0.0, description="自信/已理解/轻松")
    neutral: float = Field(default=0.0, description="中性/无明显情绪")


_AFFECT_PATTERNS: dict[str, list[str]] = {
    "frustrated": [
        "看不懂", "不理解", "搞不清", "太难了", "完全不会", "放弃",
        "头大", "崩溃", "晕了", "蒙了", "迷了", "绕晕", "不知道怎么",
        "什么鬼", "不明白", "没搞清", "还是不懂", "怎么也想不通",
    ],
    "confident": [
        "我懂了", "明白了", "搞定了", "没问题", "清楚了", "会了",
        "原来如此", "豁然开朗", "我知道了", "理解了", "学到了",
    ],
    "curious": [
        "为什么", "能不能深入", "再讲讲", "怎么做到", "底层原理",
        "有意思", "想了解", "好奇", "展开说说", "还有吗",
    ],
    "passive": [
        "随便", "都行", "无所谓", "算了", "跳过", "下一个",
        "嗯", "哦", "好吧", "行吧",
    ],
    "confused": [
        "困惑", "不太明白", "有点乱", "搞混了", "矛盾", "不确定",
        "看不明白", "混淆", "乱套了", "糊涂",
    ],
    "anxious": [
        "焦虑", "着急", "担心", "紧张", "来不及", "怎么办",
        "做不完", "跟不上了", "受挫",
    ],
}

# 预编译成正则
_AFFECT_REGEXES: dict[str, re.Pattern] = {
    affect: re.compile("|".join(re.escape(k) for k in keywords))
    for affect, keywords in _AFFECT_PATTERNS.items()
}

# 关键词 label → 教学 prompt 统一 label
_LABEL_MAP: dict[str, str] = {
    "frustrated": "anxious",
    "confident": "confident",
    "curious": "neutral",
    "passive": "neutral",
    "confused": "confused",
    "anxious": "anxious",
}


def _keyword_detect(text: str) -> dict[str, float]:
    """纯关键词情绪检测，返回原始 label 空间。"""
    signals: dict[str, float] = {}
    text_len = max(len(text), 1)
    for affect, pattern in _AFFECT_REGEXES.items():
        matches = pattern.findall(text)
        if matches:
            hit_chars = sum(len(m) for m in matches)
            confidence = min(0.4 + (hit_chars / text_len) * 1.5, 1.0)
            signals[affect] = round(confidence, 2)
    return signals


def detect_affect(text: str, llm=None) -> dict[str, float]:
    """检测学生消息中的情绪信号。

    当 llm 可用且支持 structured output 时优先 LLM 分类，
    失败或不可用时回退到关键词检测。

    返回统一的 label 空间：confused / anxious / confident / neutral。
    空文本返回 {}。
    """
    text = str(text or "").strip()
    if not text:
        return {}

    # ── LLM 优先路径 ──
    if llm is not None and hasattr(llm, "with_structured_output"):
        try:
            structured_llm = llm.with_structured_output(AffectResult)
            prompt = (
                "分析以下学生学习消息中表现出的情绪，对每个类别给出 0-1 之间的置信度：\n"
                "confused: 困惑、混乱、不理解\n"
                "anxious: 焦虑、受挫、着急\n"
                "confident: 自信、已理解、轻松\n"
                "neutral: 中性，无明显情绪\n\n"
                f'学生消息："{text}"\n\n'
                "只输出数值，无需解释。"
            )
            result: AffectResult = structured_llm.invoke(prompt)
            signals: dict[str, float] = {}
            if result.confused > 0.1:
                signals["confused"] = round(result.confused, 2)
            if result.anxious > 0.1:
                signals["anxious"] = round(result.anxious, 2)
            if result.confident > 0.1:
                signals["confident"] = round(result.confident, 2)
            if not signals:
                signals["neutral"] = round(min(1.0, max(result.neutral, 0.5)), 2)
            return signals
        except Exception:
            pass  # fall through to keyword

    # ── 关键词回退路径 ──
    raw = _keyword_detect(text)
    signals = {}
    for old_label, conf in raw.items():
        new_label = _LABEL_MAP.get(old_label, old_label)
        signals[new_label] = max(signals.get(new_label, 0.0), conf)
    return signals


def primary_affect(signals: dict[str, float]) -> str:
    """返回置信度最高的一个情绪标签，如果没有则返回空字符串。"""
    if not signals:
        return ""
    return max(signals, key=signals.get)  # type: ignore[arg-type]
