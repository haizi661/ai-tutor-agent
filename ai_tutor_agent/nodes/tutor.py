from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.output_format import (
    collapse_blank_lines,
    parse_json_object,
    split_sentences,
    stream_text_chunks,
)
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text

# ─────────────────────────────────────────────────────
# 教学策略选择：根据失败次数自动切换教学方法
# ─────────────────────────────────────────────────────
_STRATEGY_MAP = {
    0: "explain",       # 首次：标准讲解
    1: "analogy",       # 第2次：生活类比法
    2: "stepbystep",    # 第3次：逐步拆解法
    3: "socratic",      # 第4次+：苏格拉底引导法
}


def _select_strategy(attempt_count: int) -> str:
    key = min(attempt_count, max(_STRATEGY_MAP.keys()))
    return _STRATEGY_MAP[key]


# ─────────────────────────────────────────────────────
# 难度级别描述：决定讲解深度和风格
# ─────────────────────────────────────────────────────
_DIFFICULTY_DESCRIPTORS = {
    1: {
        "persona": "耐心的启蒙老师",
        "depth": "完全零基础入门",
        "style": "绝对不用数学公式，只用生活打比方和故事，用最简单直白的语言",
        "length": "约200字，短而有趣，绝不超长",
    },
    2: {
        "persona": "友善的入门导师",
        "depth": "初学者友好",
        "style": "用生活类比引入，介绍核心术语并即时解释，不用复杂推导",
        "length": "约300字",
    },
    3: {
        "persona": "经验丰富的大学讲师",
        "depth": "中等程度，理论与实践并重",
        "style": "标准教材式讲解，结合具体应用场景，适度使用专业术语",
        "length": "约400字",
    },
    4: {
        "persona": "严谨的研究生导师",
        "depth": "进阶深度，包含原理推导",
        "style": "理论推导加进阶应用，可假设学生已熟悉基础，聚焦难点和边界情况",
        "length": "约500字，可含公式",
    },
    5: {
        "persona": "领域专家",
        "depth": "专家级，聚焦核心难点",
        "style": "直接讨论深度问题、边界条件和高阶应用，跳过铺垫，精准点到为止",
        "length": "约400字，高密度信息",
    },
}


def _get_diff(level: int) -> dict:
    return _DIFFICULTY_DESCRIPTORS.get(level, _DIFFICULTY_DESCRIPTORS[3])


# ─────────────────────────────────────────────────────
# 从雷达画像提取薄弱维度，生成教学提示
# ─────────────────────────────────────────────────────
def _weak_areas_hint(radar: dict) -> str:
    if not radar:
        return ""
    breakdown = radar.get("breakdown", [])
    if not breakdown:
        labels = radar.get("labels", [])
        obj_scores = radar.get("objective_scores", [])
        if labels and obj_scores:
            weak = [d for d, s in sorted(zip(labels, obj_scores), key=lambda x: x[1]) if s < 50][:2]
            if weak:
                return f"\n【画像提示】学生在「{'」「'.join(weak)}」维度较薄弱，请重点照顾这些方面。"
        return ""
    weak_dims = [item["dimension"] for item in breakdown if item.get("objective_score", 50) < 45]
    overconfident = [item["dimension"] for item in breakdown if item.get("gap", 0) > 30]
    parts = []
    if weak_dims:
        parts.append(f"客观薄弱：「{'」「'.join(weak_dims)}」")
    if overconfident:
        parts.append(f"过度自信（自评高于实测30分+）：「{'」「'.join(overconfident)}」，请特别纠正这些误区")
    if parts:
        return f"\n【画像提示】{'; '.join(parts)}。请在讲解中针对性补强，纠正常见误解。"
    return ""


# ─────────────────────────────────────────────────────
# 根据策略构建差异化教学指令
# ─────────────────────────────────────────────────────
def _strategy_instruction(strategy: str, feedback: str, attempt_count: int) -> str:
    if strategy == "analogy":
        return f"""
【本轮策略：纯类比教学法（第{attempt_count + 1}轮，上次错因：{feedback}）】
- 用 2~3 个生动的生活/工程类比解释核心概念，禁止使用公式
- 每个类比后用一句话点明与概念的对应关系
- 结尾设置一个"自测类比"：让学生用自己的话类比解释，为下轮考核热身"""

    if strategy == "stepbystep":
        return f"""
【本轮策略：逐步拆解法（第{attempt_count + 1}轮，上次错因：{feedback}）】
- 把整个概念拆解为 4~6 个微步骤，每步用「✓ 步骤 N：」标记
- 每步结尾配一个自验问题（"你能用一句话说出这步的意义吗？"）
- 最后用一句话整合：说明各步骤合力产生的完整效果"""

    if strategy == "socratic":
        return f"""
【本轮策略：苏格拉底引导法（第{attempt_count + 1}轮，上次错因：{feedback}）】
- 不直接给答案，而是通过 3 个循序渐进的问题引导学生自己推导
- 每个问题基于前一个的预期回答，逐步接近核心概念
- 在关键转折点给出"假如你这样理解……"的提示，但保留最终结论让学生自己说出
- 格式：先抛3个引导问题 → 给提示线 → 最后总结"核心洞见"一句话"""

    # default: explain
    if feedback:
        return f"""
【本轮策略：针对性重讲（上次错因：{feedback}）】
- 识别上次错因的根本原因，从一个全新角度切入讲解
- 特别强调上次遗漏或混淆的细节
- 禁止重复上次讲解路径，必须换一个例子"""
    return "请进行标准深度讲解，逻辑严密，给出一个具体实际应用场景作为收尾。"


def _build_citation_markdown(citations: list[dict]) -> tuple[str, list[dict]]:
    if not citations:
        return "", []

    seen_keys = set()
    concise = []
    for item in citations:
        filename = str(item.get("filename", "")).strip() or "未命名资料"
        page = item.get("page")
        key = (filename, page)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        concise.append(
            {
                "filename": filename,
                "page": int(page) if isinstance(page, int) else None,
                "chunk_index": item.get("chunk_index"),
                "snippet": item.get("snippet", ""),
            }
        )
        if len(concise) >= 4:
            break

    if not concise:
        return "", []

    lines = ["\n\n---", "参考来源："]
    for source in concise:
        page_text = f" 第 {source['page']} 页" if source.get("page") else ""
        lines.append(f"- [{source['filename']}] {page_text}".rstrip())

    return "\n".join(lines) + "\n", concise


def _normalize_phrase(text: str) -> str:
    cleaned = re.sub(r"^[#>\-\d\.\)\s]+", "", (text or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip("：: ")


def _build_tutor_sections_from_text(raw_text: str, topic: str) -> dict:
    cleaned = collapse_blank_lines(raw_text)
    paragraphs = [segment.strip() for segment in cleaned.split("\n\n") if segment.strip()]
    sentences = split_sentences(cleaned)

    main_line = _normalize_phrase(paragraphs[0] if paragraphs else (sentences[0] if sentences else f"这一轮先抓住【{topic}】最关键的主线。"))

    example = ""
    for paragraph in paragraphs:
        if any(token in paragraph for token in ["例如", "比如", "想象", "举个例子", "可以把它看成"]):
            example = _normalize_phrase(paragraph)
            break

    body_paragraphs = [paragraph for paragraph in paragraphs[1:] if _normalize_phrase(paragraph)]
    if not example and body_paragraphs:
        example = _normalize_phrase(body_paragraphs[-1])
        body_paragraphs = body_paragraphs[:-1]
    if not example:
        example = f"可以把【{topic}】放进一个具体场景里再看一遍，这样更容易抓住它到底在判断什么。"

    steps: list[str] = []
    for paragraph in body_paragraphs:
        if "核心要点" in paragraph:
            continue
        for sentence in split_sentences(paragraph):
            normalized = _normalize_phrase(sentence)
            if normalized and normalized not in steps:
                steps.append(normalized)
            if len(steps) >= 4:
                break
        if len(steps) >= 4:
            break

    if not steps:
        fallback_sentences = [_normalize_phrase(item) for item in sentences[1:5] if _normalize_phrase(item)]
        steps = fallback_sentences[:4]

    if not steps:
        steps = [
            f"先明确【{topic}】到底在判断什么。",
            "再分清它和容易混淆的概念边界。",
            "最后把判断标准放回题目或场景里验证一次。",
        ]

    key_points: list[str] = []
    keypoint_match = re.search(r"核心要点[:：]\s*(.+)", cleaned, flags=re.DOTALL)
    if keypoint_match:
        for line in keypoint_match.group(1).splitlines():
            normalized = _normalize_phrase(line)
            if normalized:
                key_points.append(normalized)

    if not key_points:
        key_points = steps[:2]

    self_check = ""
    for sentence in sentences:
        if any(token in sentence for token in ["你现在可以先试着想", "你可以先想", "想一想", "自测", "自己试着"]):
            self_check = _normalize_phrase(sentence)
            break

    return {
        "main_line": main_line,
        "steps": steps[:4],
        "example": example,
        "key_points": key_points[:2],
        "self_check": self_check,
    }


def _format_tutor_markdown(payload: dict, topic: str) -> str:
    main_line = _normalize_phrase(payload.get("main_line", "")) or f"这一轮先抓住【{topic}】最关键的主线。"
    steps = [
        _normalize_phrase(item)
        for item in payload.get("steps", [])
        if _normalize_phrase(item)
    ]
    if not steps:
        steps = _build_tutor_sections_from_text(main_line, topic)["steps"]

    example = _normalize_phrase(payload.get("example", "")) or f"你可以把【{topic}】放回一个具体场景里再看，这样更容易抓住它到底在判断什么。"
    key_points = [
        _normalize_phrase(item)
        for item in payload.get("key_points", [])
        if _normalize_phrase(item)
    ] or steps[:2]
    self_check = _normalize_phrase(payload.get("self_check", ""))

    lines = [
        "### 先抓主线",
        main_line,
        "",
        "### 再拆台阶",
    ]
    lines.extend([f"{index}. {item}" for index, item in enumerate(steps[:4], start=1)])
    lines.extend(
        [
            "",
            "### 代入一个例子",
            example,
            "",
            "### 💡 本次核心要点",
        ]
    )
    lines.extend([f"- {item}" for item in key_points[:2]])
    if self_check:
        lines.extend(["", f"你现在可以先试着想：{self_check}"])
    return collapse_blank_lines("\n".join(lines))


# ─────────────────────────────────────────────────────
# 主节点构建函数
# ─────────────────────────────────────────────────────
def build_tutor_node(tutor_llm, runtime: RuntimeContext):
    def tutor_node(state: AgentState):
        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider

        topic = state["current_topic"]
        difficulty_level = state.get("difficulty_level", 3)
        attempt_count = state.get("attempt_count", 0)
        feedback = state.get("feedback", "")
        radar = state.get("assessment_radar", {})
        strategy = _select_strategy(attempt_count)
        diff = _get_diff(difficulty_level)
        weak_hint = _weak_areas_hint(radar)

        event_sink.emit(
            make_event(
                "node.start",
                "tutor",
                message=f"正在为【{topic}】定制讲解方案（难度 Lv.{difficulty_level} · 策略: {strategy} · 第{attempt_count + 1}轮）",
                data={"topic": topic, "difficulty": difficulty_level, "attempt": attempt_count, "strategy": strategy},
            )
        )

        # RAG: 检索相关知识
        citations = []
        if hasattr(knowledge_provider, "query_with_sources"):
            retrieval = knowledge_provider.query_with_sources(topic)
            context = retrieval.get("context", "")
            citations = retrieval.get("citations", [])
        else:
            context = knowledge_provider.query(topic)
        knowledge_prompt = ""
        if context:
            knowledge_prompt = f"\n\n【参考资料】请优先结合以下知识进行讲解：\n{context}\n"

        system_content = build_teacher_voice(
            f"""你现在负责正式讲解环节，要把一个知识点讲得既有方向感，又让学生愿意继续跟着你走。

当前学生档案：
- 知识水平：{diff["depth"]}
- 你的角色定位：{diff["persona"]}
- 讲解风格：{diff["style"]}
- 字数控制：{diff["length"]}{weak_hint}

讲解要求：
1. 开头先用一句话点出“这一步最该抓住什么”
2. 正文按 2~4 个台阶推进，每次只解释一个关键点
3. 如果适合，给一个贴近日常直觉的类比、判断口诀或观察角度
4. 如果学生容易混淆两个概念，要直接点破“不要把 A 和 B 混在一起”
5. 如果有参考资料，优先参考，但必须用自己的话讲，不要照搬原文
6. 结尾必须有「💡 本次核心要点：」总结 1~2 句最值得记住的话
7. 如果这一轮适合自检，可以在最后再补一句「你现在可以先试着想：...」，但只允许一句"""
        )

        strategy_inst = _strategy_instruction(strategy, feedback, attempt_count)
        human_content = f"""请讲解主题：【{topic}】

{strategy_inst}{knowledge_prompt}

输出格式要求：
- 必须严格输出 JSON，不要输出 Markdown 代码块，不要输出 JSON 以外的解释
- 字段 schema：
{{
  "main_line": "一句话先点出这一步最该抓住什么",
  "steps": ["步骤1", "步骤2", "步骤3"],
  "example": "一个贴近直觉的例子或场景",
  "key_points": ["关键记忆点1", "关键记忆点2"],
  "self_check": "可选，一句让学生自检的话；如果不需要则给空字符串"
}}
- `steps` 保持 2~4 条，每条只说一个动作或判断点
- 不要写空话，不要写“好的”“当然”等开场白"""

        system_msg = SystemMessage(content=system_content)
        human_msg = HumanMessage(content=human_content)

        raw_response = ""
        for chunk in tutor_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            raw_response += chunk_text

        structured = parse_json_object(raw_response)
        if structured is None:
            structured = _build_tutor_sections_from_text(raw_response, topic)

        full_response = _format_tutor_markdown(structured, topic)
        stream_text_chunks(event_sink, "tutor", full_response)

        citation_markdown, concise_sources = _build_citation_markdown(citations)
        if citation_markdown:
            full_response += citation_markdown
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tutor",
                    data={"text": citation_markdown},
                )
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "tutor",
                message="讲解完毕，正在准备考核题目…",
                data={"content_length": len(full_response), "strategy": strategy, "citations": concise_sources},
            )
        )
        return {"tutor_content": full_response, "teaching_strategy": strategy, "tutor_citations": concise_sources}

    return tutor_node
