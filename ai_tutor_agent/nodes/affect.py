"""学生情绪信号检测模块。

对每轮用户消息做关键词匹配，识别四类情绪信号：
  frustrated — 受挫、卡住
  confident  — 有信心、已理解
  curious    — 好奇、想深入
  passive    — 敷衍、意愿低
"""
from __future__ import annotations

import re

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
}

# 预编译成正则，每类一个
_AFFECT_REGEXES: dict[str, re.Pattern] = {
    affect: re.compile("|".join(re.escape(k) for k in keywords))
    for affect, keywords in _AFFECT_PATTERNS.items()
}


def detect_affect(text: str) -> dict[str, float]:
    """
    对输入文本进行情绪关键词匹配，返回检测到的信号及置信度 (0–1)。

    返回示例: {"frustrated": 0.8, "curious": 0.4}
    如果没有匹配到任何信号，返回空 dict。
    """
    text = str(text or "").strip()
    if not text:
        return {}

    signals: dict[str, float] = {}
    text_len = max(len(text), 1)

    for affect, pattern in _AFFECT_REGEXES.items():
        matches = pattern.findall(text)
        if matches:
            # 匹配越多 / 文本越短 → 信号越强
            hit_chars = sum(len(m) for m in matches)
            confidence = min(0.4 + (hit_chars / text_len) * 1.5, 1.0)
            signals[affect] = round(confidence, 2)

    return signals


def primary_affect(signals: dict[str, float]) -> str:
    """返回置信度最高的一个情绪标签，如果没有则返回空字符串。"""
    if not signals:
        return ""
    return max(signals, key=signals.get)  # type: ignore[arg-type]
