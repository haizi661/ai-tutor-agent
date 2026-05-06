from __future__ import annotations

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ai_tutor_agent.knowledge_map.debug_graph_rag import build_learning_answer_html

from ..core.events import make_event
from ..core.graph_service import GraphQueryService
from ..core.learning_support import (
    trim_message_history,
    build_graph_citation_plan,
    build_graph_context_from_result,
    build_graph_guidance_from_result,
    mark_student_node_started,
    normalize_graph_answer,
)
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
from ..infrastructure.retriever import RetrievalRewriteRequest
from .affect import detect_affect, primary_affect

logger = logging.getLogger(__name__)

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
# 教学标记提取：从 LLM 输出中解析图谱驱动标记
# ─────────────────────────────────────────────────────
_TEACHING_MARKER_RE = re.compile(
    r'\[MASTERY_ACHIEVED:\s*([^\]]+)\]'
    r'|\[SKIPPED:\s*([^\]]+)\]'
    r'|\[→ 下一概念[:：]\s*([^\]|]+?)(?:\s*\|\s*([^\]]+))?\]'
)


def _extract_teaching_markers(text: str) -> tuple[str, list[dict[str, str]]]:
    """
    提取教学标记，返回 (clean_text, [{type, ...}, ...])。
    """
    markers: list[dict[str, str]] = []
    for m in re.finditer(r'\[MASTERY_ACHIEVED:\s*([^\]]+)\]', text):
        markers.append({"type": "mastered", "value": m.group(1).strip()})
    for m in re.finditer(r'\[SKIPPED:\s*([^\]]+)\]', text):
        markers.append({"type": "skipped", "value": m.group(1).strip()})
    for m in re.finditer(r'\[→ 下一概念[:：]\s*([^\]|]+?)(?:\s*\|\s*([^\]]+))?\]', text):
        markers.append(
            {
                "type": "next_node",
                "title": m.group(1).strip(),
                "id": str(m.group(2) or "").strip(),
            }
        )
    clean = _TEACHING_MARKER_RE.sub('', text).strip()
    return clean, markers


# ─────────────────────────────────────────────────────
# 掌握度标记门控校验
# ─────────────────────────────────────────────────────
_MASTERY_MIN_TURNS: dict[str, int] = {
    "識別層": 1,
    "理解層": 3,
    "應用層": 5,
    "分析層": 7,
}


def _validate_mastery_claim(user_kg: dict, node_title: str, target_mastery: str = "") -> bool:
    """
    验证 LLM 的 MASTERY_ACHIEVED 标记是否合理。
    需满足最低互动轮次要求，否则降为 in_progress。
    """
    entry = user_kg.get(node_title, {})
    if not isinstance(entry, dict):
        entry = {}
    turn_count = int(entry.get("turn_count") or 0)
    mastery = target_mastery or str(entry.get("target_mastery") or "理解層")
    min_t = _MASTERY_MIN_TURNS.get(mastery, 3)
    return turn_count >= min_t


# ─────────────────────────────────────────────────────
# 知识图谱状态辅助
# ─────────────────────────────────────────────────────
def _kg_status_label(status: str) -> str:
    return {
        "mastered": "已掌握",
        "skipped":  "已跳过",
        "in_progress": "学习中",
        "not_started": "未开始",
        "assessed_high": "测评良好",
        "assessed_low": "测评待补",
    }.get(status, "未开始")


def _string_list(values: list[object] | tuple[object, ...] | None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def _graph_step_titles(values: list[object] | tuple[object, ...] | None) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        text = ""
        if isinstance(value, dict):
            for key in ("target", "title", "name", "label"):
                candidate = str(value.get(key) or "").strip()
                if candidate:
                    text = candidate
                    break
        else:
            text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        titles.append(text)
    return titles


def _graph_context_from_state(state: dict) -> dict[str, object]:
    return {
        "anchor_id": str(state.get("graph_anchor_id") or "").strip(),
        "anchor_title": str(state.get("graph_anchor_title") or "").strip(),
        "anchor_filename": str(state.get("graph_anchor_filename") or "").strip(),
        "prerequisites": _string_list(state.get("graph_prerequisites") or []),
        "neighbors": _string_list(state.get("graph_neighbors") or []),
        "learning_objectives": _string_list(state.get("graph_learning_objectives") or []),
        "must_know": _string_list(state.get("graph_must_know") or []),
        "common_errors": _string_list(state.get("graph_common_errors") or []),
        "target_mastery_level": str(state.get("graph_target_mastery_level") or "").strip(),
        "difficulty": str(state.get("graph_difficulty") or "").strip(),
        "next_steps": list(state.get("graph_next_steps") or []),
    }


def _coalesce_graph_context(state: dict, graph_context: dict[str, object] | None) -> dict[str, object]:
    latest = dict(graph_context or {})
    latest_anchor = str(latest.get("anchor_title") or "").strip()
    if latest_anchor:
        return {
            "anchor_id": str(latest.get("anchor_id") or latest_anchor).strip(),
            "anchor_title": latest_anchor,
            "anchor_filename": str(latest.get("anchor_filename") or "").strip(),
            "prerequisites": _string_list(latest.get("prerequisites") or []),
            "neighbors": _string_list(latest.get("neighbors") or []),
            "learning_objectives": _string_list(latest.get("learning_objectives") or []),
            "must_know": _string_list(latest.get("must_know") or []),
            "common_errors": _string_list(latest.get("common_errors") or []),
            "target_mastery_level": str(latest.get("target_mastery_level") or "").strip(),
            "difficulty": str(latest.get("difficulty") or "").strip(),
            "next_steps": list(latest.get("next_steps") or []),
        }

    merged = _graph_context_from_state(state)
    if latest.get("anchor_id"):
        merged["anchor_id"] = str(latest.get("anchor_id") or "").strip()
    if latest.get("anchor_title"):
        merged["anchor_title"] = str(latest.get("anchor_title") or "").strip()
    if latest.get("anchor_filename"):
        merged["anchor_filename"] = str(latest.get("anchor_filename") or "").strip()

    for key in ("prerequisites", "neighbors", "learning_objectives", "must_know", "common_errors"):
        if latest.get(key):
            merged[key] = _string_list(latest.get(key) or [])

    for key in ("target_mastery_level", "difficulty"):
        if latest.get(key):
            merged[key] = str(latest.get(key) or "").strip()

    if latest.get("next_steps"):
        merged["next_steps"] = list(latest.get("next_steps") or [])

    return merged


def _minimal_graph_context(anchor_title: str, anchor_id: str = "") -> dict[str, object]:
    title = str(anchor_title or "").strip()
    if not title:
        return {}
    return {
        "anchor_id": str(anchor_id or title).strip(),
        "anchor_title": title,
        "anchor_filename": "",
        "prerequisites": [],
        "neighbors": [],
        "learning_objectives": [],
        "must_know": [],
        "common_errors": [],
        "target_mastery_level": "",
        "difficulty": "",
        "next_steps": [],
    }


def _derive_affect_signal(state: dict, *, gap_type: str = "") -> str:
    if int(state.get("attempt_count") or 0) >= 2 or bool(state.get("needs_hint")):
        return "受挫"
    if gap_type == "underconfident":
        return "谨慎"
    if gap_type == "overconfident":
        return "自信偏高"
    if str(state.get("topic_background") or "").strip():
        return "稳定"
    return "平稳"


def _subject_profile_summary(
    *,
    topic: str,
    learning_target: str,
    difficulty: dict[str, str],
    strategy: str,
) -> str:
    target = str(learning_target or topic).strip() or str(topic or "").strip()
    return f"主题：{topic}；当前焦点：{target}；学生层级：{difficulty['depth']}；当前策略：{strategy}"


def _resolve_graph_context_for_title(knowledge_provider, title: str) -> dict[str, object]:
    resolver = getattr(knowledge_provider, "resolve_graph_context", None)
    if not callable(resolver):
        return {}
    try:
        return dict(resolver(title) or {})
    except Exception:
        return {}


def _resolve_graph_marker_reference(
    knowledge_provider,
    marker_value: str,
    *,
    fallback_context: dict[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    token = str(marker_value or "").strip()
    if not token:
        return "", {}

    fallback = dict(fallback_context or {})
    fallback_title = str(fallback.get("anchor_title") or "").strip()
    fallback_id = str(fallback.get("anchor_id") or "").strip()
    if token and token in {fallback_title, fallback_id} and fallback_title:
        return fallback_title, fallback

    resolved = _resolve_graph_context_for_title(knowledge_provider, token)
    resolved_title = str(resolved.get("anchor_title") or "").strip()
    if resolved_title:
        return resolved_title, resolved
    return token, {}


# ─────────────────────────────────────────────────────
# 图谱感知教学指令块（注入 system prompt）
# ─────────────────────────────────────────────────────
def _build_graph_instruction_block(
    state: dict,
    graph_context: dict[str, object],
    *,
    topic: str,
    learning_target: str,
    diff: dict[str, str],
    strategy: str,
) -> str:
    anchor = str(graph_context.get("anchor_title") or "").strip()
    if not anchor:
        return ""

    anchor_id = str(graph_context.get("anchor_id") or anchor).strip() or anchor
    must_know = _string_list(graph_context.get("must_know") or [])
    common_errors = _string_list(graph_context.get("common_errors") or [])
    learning_objectives = _string_list(graph_context.get("learning_objectives") or [])
    target_mastery = str(graph_context.get("target_mastery_level") or "理解层")
    difficulty = str(graph_context.get("difficulty") or "").strip() or "3"
    prerequisites = _string_list(graph_context.get("prerequisites") or [])
    next_steps = list(graph_context.get("next_steps") or [])
    neighbors = _string_list(graph_context.get("neighbors") or [])
    user_kg: dict = dict(state.get("user_knowledge_graph") or {})
    concept_gaps: dict = dict(state.get("assessment_concept_gaps") or {})

    mastered = [k for k, v in user_kg.items() if isinstance(v, dict) and v.get("status") == "mastered"]
    skipped = [k for k, v in user_kg.items() if isinstance(v, dict) and v.get("status") == "skipped"]
    downstream = [item for item in _graph_step_titles(next_steps) if item != anchor] or [n for n in neighbors if n != anchor][:4]
    downstream_str = "、".join(downstream[:4]) if downstream else "（待确定）"
    prerequisites_status = []
    for item in prerequisites[:4]:
        kg_val = user_kg.get(item, {})
        status = _kg_status_label(kg_val.get("status", "not_started") if isinstance(kg_val, dict) else "not_started")
        prerequisites_status.append(f"{item}（{status}）")

    current_gap = concept_gaps.get(anchor, {})
    gap_type = str(current_gap.get("gap_type") or "")
    gap_desc_map = {
        "overconfident": "overconfident",
        "underconfident": "underconfident",
        "aligned_high": "aligned_high",
        "aligned_low": "aligned_low",
    }
    node_core_concept = " / ".join((must_know or learning_objectives or [anchor])[:2])
    mastery_criteria = "；".join((learning_objectives or must_know or [f"能把 {anchor} 的判断标准说清楚并用于新情境。"])[:2])
    turn_count = 1
    if isinstance(user_kg.get(anchor), dict):
        turn_count = int(user_kg[anchor].get("turn_count") or 0) + 1
    affect_signal = _derive_affect_signal(state, gap_type=gap_type)
    gap_labels = []
    if gap_type:
        gap_labels.append(gap_desc_map.get(gap_type, gap_type))
    if current_gap:
        gap_labels.append(f"校准分 {current_gap.get('calibrated', '—')}")
    gap_summary = "；".join(gap_labels) if gap_labels else "暂未发现显著偏差"
    subject_profile = _subject_profile_summary(
        topic=topic,
        learning_target=learning_target,
        difficulty=diff,
        strategy=strategy,
    )

    lines = [
        "",
        f"你是一个自适应伴学导师，当前学科档案：{subject_profile}。",
        "",
        "# 身份定位",
        "你不是问答机器人，而是会持续判断教学位置的老师。",
        "你的每一句话都要推动理解往前走一步，不做礼貌性复述，不做空泛总结。",
        "",
        "# 当前教学上下文",
        f"- 当前知识节点：{anchor}（图谱 ID: {anchor_id}）",
        f"- 节点难度：{difficulty}/5，目标掌握层级：{target_mastery}",
        f"- 已确认掌握：{'、'.join(mastered[:6]) if mastered else '暂无'}",
        f"- 存在认知差距：{gap_summary}（类型：{gap_type or '未校准'}）",
        f"- 前置节点完成情况：{'、'.join(prerequisites_status) if prerequisites_status else '暂无显式前置'}",
        f"- 本节已交互轮数：{turn_count}，学生最近情绪信号：{affect_signal}",
        "",
        "# 对话风格原则",
        "1. 开口就进入实质，不说“好的”“当然”“这是个好问题”“我来解释一下”。",
        "2. 每轮只推进一个概念，宁可短，也不要把多个知识点堆在一条回复里。",
        "3. 抽象概念必须落回具体例子、物理直觉或工程场景；公式后面要补一句这意味着什么。",
        "4. 提问是教学工具，不是礼貌性收尾；每个问题都要能暴露学生当前卡点。",
        "5. 一旦检测到卡壳信号，就立刻换解释角度，不重复同一路径。",
        "",
        "# 知识图谱驱动规则",
        f"- 当前在讲 {anchor}，它的核心是：{node_core_concept}",
        f"- 该节点连接的下游概念：{downstream_str}",
        f"- 该节点的常见错误：{'；'.join(common_errors[:3]) if common_errors else '暂无显式记录'}",
        f"- 掌握度评估标准：{mastery_criteria}",
        "",
        "# 掌握度实时判断",
        "- 隐性评估学生能否复述核心概念、说明适用条件、并迁移到新情境。",
        f"- 当判断达到 {target_mastery} 层时，在回复末尾追加：[MASTERY_ACHIEVED: {anchor_id}]",
        f"- 当学生明确要求跳过当前节点时，追加：[SKIPPED: {anchor_id}]",
        "- 当准备自然引向下游节点时，追加：[→ 下一概念: 下游概念名称 | 下游节点ID]",
        "",
        "# 教学策略选择",
        "- overconfident：用边界条件反问，让学生自己发现矛盾。",
        "- underconfident：先确认已会的部分，再小步推进。",
        "- aligned_low：先类比，再拆步骤。",
        "- aligned_high：减少铺垫，直接进入变体、边界和挑战。",
        "",
        "# 格式规范",
        "- 主流程节点讲授默认 650-1000 字，必须充分使用节点素材包中的定义、关键点、公式、例子、图表线索和前后置关系。",
        "- 纠错轮可到 200 字，但一次只纠正一个错误层面。",
        "- 列表只在步骤明确或并列项超过 3 个且必须比较时使用。",
        "- 如果有资料证据，保留系统要求的 [1]/[2] 行内引用；不要伪造来源。",
        "",
        "# 特殊场景处理",
        "- 学生主动跳题：先给一句基础回应，再说明当前位置，并拉回当前节点。",
        "- 连续两轮没有实质进展：换更具体的例子，或改成低门槛填空式提问。",
        "- 学生表达沮丧：不要安慰式空话，直接换一种更简单的切入方式。",
        "",
        "# 输出提醒",
        "- 保持自然、紧凑、直接。最终输出结构、引用和 JSON/Markdown 格式，以本轮用户消息中的格式约束为准。",
    ]
    return "\n".join(lines)


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
    if strategy == "summary":
        return """
【本轮策略：短总结回看】
- 不要重复大段讲解，只做压缩回顾
- 优先输出：这一步最该记住的判断主线、一个易混点、一个记忆抓手
- 总长度控制在 180 字以内，像讲完后回头帮学生收束笔记"""

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


def _format_tutor_prose(payload: dict, topic: str) -> str:
    main_line = _normalize_phrase(payload.get("main_line", "")) or f"这一轮先抓住【{topic}】最关键的判断主线。"
    steps = [
        _normalize_phrase(item)
        for item in payload.get("steps", [])
        if _normalize_phrase(item)
    ]
    example = _normalize_phrase(payload.get("example", ""))
    self_check = _normalize_phrase(payload.get("self_check", ""))

    sentences: list[str] = [main_line]
    if steps:
        flow = "先" + "，再".join(steps[:2])
        if len(steps) >= 3:
            flow += f"，最后{steps[2]}"
        sentences.append(flow)
    if example:
        sentences.append(example)
    if self_check:
        sentences.append(f"你先想一下：{self_check}")
    return collapse_blank_lines(" ".join(sentences[:4]))


def _render_teacher_reply(raw_text: str, topic: str) -> str:
    structured = parse_json_object(raw_text)
    if structured is not None:
        return _format_tutor_prose(structured, topic)
    return collapse_blank_lines(raw_text).strip()


INLINE_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def _normalize_goal_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _append_unique(parts: list[str], value: str) -> None:
    normalized = _normalize_goal_text(value)
    if not normalized:
        return
    for existing in parts:
        if normalized == existing:
            return
        if normalized in existing or existing in normalized:
            return
    parts.append(normalized)


def _select_learning_target(
    topic: str,
    current_user_goal: str,
    session_goal: str = "",
    turn_goal: str = "",
    topic_focus: str = "",
    topic_starter_options: list[str] | None = None,
) -> str:
    topic_text = _normalize_goal_text(topic)
    starter_options = [_normalize_goal_text(item) for item in (topic_starter_options or []) if _normalize_goal_text(item)]
    candidates = [
        _normalize_goal_text(turn_goal),
        _normalize_goal_text(topic_focus),
        _normalize_goal_text(current_user_goal),
        _normalize_goal_text(session_goal),
    ]
    for candidate in candidates:
        if candidate and candidate != topic_text:
            return candidate
    if starter_options:
        return starter_options[0]
    return topic_text


def _build_goal_aware_query(
    topic: str,
    current_user_goal: str,
    session_goal: str = "",
    turn_goal: str = "",
    topic_focus: str = "",
    topic_starter_options: list[str] | None = None,
) -> str:
    parts: list[str] = []
    topic_text = _normalize_goal_text(topic)
    _append_unique(parts, topic_text)
    for value in (
        _select_learning_target(
            topic,
            current_user_goal,
            session_goal=session_goal,
            turn_goal=turn_goal,
            topic_focus=topic_focus,
            topic_starter_options=topic_starter_options,
        ),
        topic_focus,
        turn_goal,
        current_user_goal,
        session_goal,
    ):
        if _normalize_goal_text(value) != topic_text:
            _append_unique(parts, value)
    return " ".join(parts).strip() or topic_text


def _build_evidence_prompt(citation_plan: list[dict]) -> str:
    lines = []
    for item in citation_plan:
        rank = item.get("rank")
        label = str(item.get("display_label") or item.get("filename") or f"证据 {rank}").strip()
        snippet = str(item.get("snippet") or "").strip()
        if rank and snippet:
            lines.append(f"[{rank}] {label}：{snippet}")
    return "\n".join(lines)


def _state_seeded_citation_plan(state: dict) -> list[dict]:
    seeded = state.get("tutor_citations") or []
    return [dict(item) for item in seeded if isinstance(item, dict)] if isinstance(seeded, list) else []


def _state_seeded_evidence(state: dict) -> list[dict]:
    seeded = state.get("tutor_evidence") or []
    return [dict(item) for item in seeded if isinstance(item, dict)] if isinstance(seeded, list) else []


def _build_node_content_prompt(state: dict, citation_plan: list[dict]) -> tuple[str, bool]:
    node_context = str(state.get("node_content_context") or "").strip()
    if not node_context:
        return "", False
    prompt = (
        "\n\n【图谱 2.1 当前节点材料】\n"
        "下面内容来自 node_content_loader 对当前 graph.json 节点的结构化抽取。"
        "正式讲解必须优先覆盖这里的学习目标、必会要点、常见误区和节点解释；"
        "只有这里不足时，才补充图谱 2.2 检索或通用资料。\n"
        f"---\n{node_context}\n---\n"
    )
    if citation_plan:
        prompt += f"\n【节点预取证据】\n{_build_evidence_prompt(citation_plan)}\n"
    return prompt, True



def _filter_cited_lines(text: str, citation_count: int) -> str:
    valid_ids = {str(index) for index in range(1, citation_count + 1)}
    filtered_lines: list[str] = []
    for raw_line in collapse_blank_lines(text).splitlines():
        stripped = raw_line.strip()
        if not stripped:
            filtered_lines.append("")
            continue
        if stripped.startswith("#"):
            filtered_lines.append(raw_line)
            continue
        if _TEACHING_MARKER_RE.search(stripped):
            filtered_lines.append(raw_line)
            continue
        citations = INLINE_CITATION_PATTERN.findall(stripped)
        if citations and all(citation in valid_ids for citation in citations):
            filtered_lines.append(raw_line)
    return collapse_blank_lines("\n".join(filtered_lines)).strip()


def _build_evidence_backed_fallback(topic: str, citation_plan: list[dict]) -> str:
    if not citation_plan:
        return f"我现在还没有定位到能直接支撑【{topic}】这一步的资料证据。你可以把问题再收紧一点，我再继续往下带。"

    supported = []
    for item in citation_plan[:2]:
        rank = item.get("rank")
        snippet = str(item.get("snippet") or "").strip()
        if not rank or not snippet:
            continue
        supported.append(f"{snippet} [{rank}]")
    if not supported:
        return f"我先把这一步能确认的资料依据重新收紧，再继续往下讲。"
    joined = " ".join(supported)
    return collapse_blank_lines(f"{joined}\n\n先把这条主线站稳，再把它放回题目或场景里看。")


def _build_resilient_teacher_fallback(
    topic: str,
    learning_target: str = "",
    graph_context: dict[str, object] | None = None,
) -> str:
    context = dict(graph_context or {})
    anchor = str(
        context.get("anchor_title")
        or learning_target
        or topic
    ).strip() or topic
    must_know = _string_list(context.get("must_know"))
    common_errors = _string_list(context.get("common_errors"))

    parts = [f"这一轮先抓【{anchor}】最关键的判断，不要急着把所有细节一起背。"]
    if must_know:
        parts.append(f"先记住：{must_know[0]}。")
    if common_errors:
        parts.append(f"最容易出错的是：{common_errors[0]}。")
    parts.append("你先把这条主线站稳，我们下一步再把它放进例子或题目里。")
    return collapse_blank_lines(" ".join(parts))


def _invoke_llm_text(llm, messages: list[object]) -> str:
    response = llm.invoke(messages)
    return content_to_text(getattr(response, "content", response))


def _collect_llm_text_with_fallback(
    llm,
    messages: list[object],
    *,
    source: str,
    prefer_invoke: bool = False,
) -> tuple[str, bool]:
    if prefer_invoke:
        try:
            return _invoke_llm_text(llm, messages), False
        except Exception:
            logger.exception("%s invoke failed while stream disabled", source)
            return "", False
    try:
        raw_response = ""
        for chunk in llm.stream(messages):
            raw_response += content_to_text(getattr(chunk, "content", chunk))
        return raw_response, False
    except Exception as stream_exc:
        logger.warning("%s stream failed, retrying with invoke: %s", source, stream_exc)
        try:
            return _invoke_llm_text(llm, messages), True
        except Exception as invoke_exc:
            logger.exception("%s invoke fallback failed", source)
            return "", True


# ─────────────────────────────────────────────────────
# 主节点构建函数
# ─────────────────────────────────────────────────────
def build_tutor_node(tutor_llm, runtime: RuntimeContext):
    def tutor_node(state: AgentState):
        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider
        graph_rag_pipeline = getattr(runtime, "graph_rag_pipeline", None)
        student_state_store = getattr(runtime, "student_state_store", None)
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        llm_stream_disabled = bool(state.get("llm_stream_disabled", False))
        llm_stream_failures = int(state.get("llm_stream_failures") or 0)

        topic = state["current_topic"]
        current_user_goal = str(state.get("current_user_goal") or topic).strip() or topic
        session_goal = str(state.get("session_goal") or current_user_goal).strip() or current_user_goal
        turn_goal = str(state.get("turn_goal") or "").strip()
        topic_focus = str(state.get("topic_focus") or "").strip()
        topic_background = str(state.get("topic_background") or "").strip()
        topic_starter_options = [str(item).strip() for item in (state.get("topic_starter_options") or []) if str(item).strip()]
        learning_target = _select_learning_target(
            topic,
            current_user_goal,
            session_goal=session_goal,
            turn_goal=turn_goal,
            topic_focus=topic_focus,
            topic_starter_options=topic_starter_options,
        )
        difficulty_level = state.get("difficulty_level", 3)
        attempt_count = state.get("attempt_count", 0)
        feedback = state.get("feedback", "")
        radar = state.get("assessment_radar", {})
        preferred_opening_strategy = str(state.get("teaching_strategy") or "").strip()
        next_step_choice = str(state.get("next_step_choice") or "").strip()
        strategy = (
            preferred_opening_strategy
            if preferred_opening_strategy in set(_STRATEGY_MAP.values()) | {"summary"}
            else _select_strategy(attempt_count)
        )
        diff = _get_diff(difficulty_level)
        weak_hint = _weak_areas_hint(radar)

        event_sink.emit(
            make_event(
                "node.start",
                "tutor",
                message=f"正在围绕【{learning_target or topic}】定制讲解方案（难度 Lv.{difficulty_level} · 策略: {strategy} · 第{attempt_count + 1}轮）",
                data={
                    "topic": topic,
                    "learning_target": learning_target,
                    "difficulty": difficulty_level,
                    "attempt": attempt_count,
                    "strategy": strategy,
                },
            )
        )

        user_kg: dict = dict(state.get("user_knowledge_graph") or {})

        # ── 情绪信号检测 ──
        last_user_msg = ""
        for m in reversed(state.get("message_history") or []):
            if m.get("role") == "user":
                last_user_msg = str(m.get("content") or "")
                break
        affect_signals = detect_affect(last_user_msg)
        affect_label = primary_affect(affect_signals)
        if affect_signals:
            event_sink.emit(
                make_event(
                    "affect.detected",
                    "tutor",
                    message=f"情绪信号：{affect_label}",
                    data={"signals": affect_signals, "primary": affect_label},
                )
            )

        # 主流程当前节点讲解：已由 node_content_loader 固定写入 explanation_teacher_style。
        # 这里必须直接输出该字段，不再调用图谱搜索、通用检索或 LLM 改写，避免 relation_path 等检索产物混入教学正文。
        direct_node_content = str(state.get("node_content_context") or "").strip()
        # 主流程节点讲授不能再把 node_content_context 原样输出。
        # 这里仅记录“有节点素材包”，后面统一交给 tutor LLM 生成详实讲解，
        # 并通过 GraphRAG 的 media_items 渲染公式/图/表卡片。
        has_direct_node_content = bool(direct_node_content)

        # RAG: 非主流程节点讲解的回退路径才允许检索相关知识
        citations = []
        seeded_citation_plan = _state_seeded_citation_plan(state)
        seeded_evidence = _state_seeded_evidence(state)
        citation_plan = list(seeded_citation_plan)
        context = ""
        graph_guidance = ""
        graph_context: dict[str, object] = {}
        evidence_contract = bool(citation_plan)
        graph_result: dict[str, object] | None = None
        updated_goal = learning_target
        rewrite_request = RetrievalRewriteRequest(
            channel="tutor",
            raw_query=learning_target,
            current_topic=topic,
            attempt_count=int(attempt_count or 0),
            teaching_strategy=str(strategy or ""),
            weak_areas_hint=str(weak_hint or ""),
        )
        search_query = _build_goal_aware_query(
            topic,
            current_user_goal,
            session_goal=session_goal,
            turn_goal=turn_goal,
            topic_focus=topic_focus,
            topic_starter_options=topic_starter_options,
        )
        if graph_rag_pipeline is not None:
            try:
                if has_direct_node_content:
                    graph_query = " ".join(
                        part for part in [
                            str(state.get("current_node_name") or state.get("graph_anchor_title") or learning_target or "").strip(),
                            str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip(),
                            "定义 关键点 公式 图表 表格 例子 工程意义 常见误区",
                        ] if part
                    ) or search_query
                else:
                    graph_query = search_query
                graph_result = graph_rag_pipeline.ask(graph_query, traversal_mode="balanced")
            except Exception as exc:
                graph_result = None
                event_sink.emit(
                    make_event(
                        "session.warning",
                        "tutor",
                        message="图谱 2.2 检索失败，已仅使用当前已有图谱节点材料继续讲解。",
                        data={"error": str(exc)},
                    )
                )

        if graph_result is not None:
            context = str(graph_result.get("context_text") or "").strip()
            graph_guidance = build_graph_guidance_from_result(graph_result)
            graph_context = build_graph_context_from_result(
                graph_rag_pipeline,
                graph_result,
                fallback_query=search_query,
            )
            graph_citation_plan = build_graph_citation_plan(graph_result)
            citation_plan = seeded_citation_plan + [item for item in graph_citation_plan if item not in seeded_citation_plan]
            citations = citation_plan
            evidence_contract = bool(citation_plan)
        elif hasattr(knowledge_provider, "query_with_sources"):
            try:
                retrieval = knowledge_provider.query_with_sources(search_query, rewrite_request=rewrite_request)
            except TypeError:
                retrieval = knowledge_provider.query_with_sources(search_query)
            context = retrieval.get("context", "")
            graph_guidance = str(retrieval.get("graph_guidance") or "").strip()
            graph_context = dict(retrieval.get("graph_context") or {})
            citations = retrieval.get("citations", [])
            citation_plan = retrieval.get("citation_plan", citations) or seeded_citation_plan
            evidence_contract = bool(citation_plan) or any(key in retrieval for key in ("citation_plan", "evidence", "needs_follow_up"))
            if retrieval.get("needs_follow_up") and hasattr(runtime, "answer_provider"):
                follow_up_question = str(retrieval.get("follow_up_question") or "").strip()
                if follow_up_question:
                    try:
                        refined_goal = runtime.answer_provider.get_answer(follow_up_question, state=state).strip()
                    except Exception:
                        refined_goal = ""
                    if refined_goal:
                        updated_goal = refined_goal
                        retry_request = RetrievalRewriteRequest(
                            channel="tutor",
                            raw_query=refined_goal,
                            current_topic=topic,
                            attempt_count=int(attempt_count or 0),
                            teaching_strategy=str(strategy or ""),
                            weak_areas_hint=str(weak_hint or ""),
                        )
                        retry_query = _build_goal_aware_query(topic, refined_goal)
                        try:
                            retrieval = knowledge_provider.query_with_sources(retry_query, rewrite_request=retry_request)
                        except TypeError:
                            retrieval = knowledge_provider.query_with_sources(retry_query)
                        context = retrieval.get("context", "")
                        graph_guidance = str(retrieval.get("graph_guidance") or "").strip()
                        graph_context = dict(retrieval.get("graph_context") or {})
                        citations = retrieval.get("citations", [])
                        citation_plan = retrieval.get("citation_plan", citations) or seeded_citation_plan
        else:
            try:
                context = knowledge_provider.query(search_query, rewrite_request=rewrite_request)
            except TypeError:
                context = knowledge_provider.query(search_query)
        node_content_prompt, has_node_content_context = _build_node_content_prompt(state, citation_plan)
        knowledge_prompt = node_content_prompt
        if graph_result is not None and context:
            knowledge_prompt += (
                "\n\n【图谱 2.2 上下文】\n"
                "请在已经覆盖图谱 2.1 当前节点材料后，再依据以下知识图谱检索结果补充图表、公式和关系路径信息：\n"
                f"---\n{context}\n---\n"
            )
            if citation_plan:
                knowledge_prompt += f"\n【图谱 2.2 证据】\n{_build_evidence_prompt(citation_plan)}\n"
        elif context and citation_plan:
            knowledge_prompt += (
                "\n\n【证据资料】下面是已经通过检索选出的可引用证据。"
                "你只能依据这些证据组织讲解，不能补充没有证据支持的事实。\n"
                f"{_build_evidence_prompt(citation_plan)}\n"
            )
        elif context:
            knowledge_prompt += f"\n\n【参考资料】请在覆盖图谱 2.1 当前节点材料后，再结合以下知识进行讲解：\n{context}\n"
        if graph_guidance:
            knowledge_prompt += f"\n【课程图谱教学提示】\n{graph_guidance}\n"

        # ── 知识不足时的多层回退策略 ──
        # 不再停止并要求用户"收紧问题"，而是利用 LLM 自身知识继续讲解
        knowledge_source_hint = ""
        if graph_result is None and hasattr(knowledge_provider, "query_with_sources") and evidence_contract and not citation_plan:
            # 无课程资料证据：降级为 LLM 自身知识讲解模式
            knowledge_source_hint = (
                "\n\n【知识来源说明】当前课程资料库中暂未找到直接匹配的证据片段。"
                "请基于你作为控制理论领域专家的知识储备来讲解，确保准确性。"
                "如果某些内容你没有把握，请明确告诉学生这部分建议查阅教材原文。"
            )
            event_sink.emit(
                make_event(
                    "session.info",
                    "tutor",
                    message=f"当前资料库未找到【{updated_goal or topic}】的直接证据，将基于专业知识为你讲解。",
                    data={"fallback_mode": "llm_knowledge"},
                )
            )

        active_graph_context = _coalesce_graph_context(state, graph_context)
        graph_anchor = str(active_graph_context.get("anchor_title") or "").strip()
        student_state_snapshot = dict(state.get("student_state_snapshot") or {})

        # ── 图谱驱动：前驱缺口检测与后继路径定位 ──
        prerequisite_gap_hint = ""
        successor_path_hint = ""
        _course_graph_nodes = getattr(knowledge_provider, "course_graph_nodes", None) or {}
        if _course_graph_nodes and graph_anchor:
            gqs = GraphQueryService(_course_graph_nodes)
            # 卡点触发：attempt_count >= 1 或 needs_hint 时检测前驱缺口
            if attempt_count >= 1 or state.get("needs_hint"):
                gaps = gqs.detect_prerequisite_gaps(graph_anchor, user_kg, max_depth=2)
                if gaps:
                    prerequisite_gap_hint = gqs.format_prerequisite_gaps_hint(
                        gaps, current_node=graph_anchor
                    )
                    event_sink.emit(
                        make_event(
                            "graph.prerequisite_gap",
                            "tutor",
                            message=f"前驱缺口检测：{', '.join(g['title'] for g in gaps[:3])}",
                            data={"gaps": gaps[:3], "current_node": graph_anchor},
                        )
                    )
            # 新知引导：首次进入节点时定位后继路径
            node_entry = user_kg.get(graph_anchor, {})
            is_first_visit = (
                not isinstance(node_entry, dict)
                or int(node_entry.get("turn_count") or 0) <= 1
            )
            if is_first_visit:
                successors = gqs.find_successor_path(graph_anchor, max_depth=2)
                if successors:
                    successor_path_hint = gqs.format_successor_path_hint(
                        graph_anchor, successors
                    )
                    event_sink.emit(
                        make_event(
                            "graph.successor_path",
                            "tutor",
                            message=f"后继路径：{', '.join(successors[:3])}",
                            data={"successors": successors[:4], "current_node": graph_anchor},
                        )
                    )

        if graph_anchor:
            graph_anchor_id = str(active_graph_context.get("anchor_id") or graph_anchor).strip()
            prev_entry = user_kg.get(graph_anchor, {})
            if isinstance(prev_entry, dict):
                user_kg[graph_anchor] = {
                    **prev_entry,
                    "status": "in_progress",
                    "turn_count": int((prev_entry.get("turn_count") or 0)) + 1,
                }
            else:
                user_kg[graph_anchor] = {"status": "in_progress", "turn_count": 1}
            event_sink.emit(
                make_event(
                    "graph.node_update",
                    "tutor",
                    message=f"当前节点：{graph_anchor}",
                    data={"title": graph_anchor, "id": graph_anchor_id, "status": "in_progress", "type": "current"},
                )
            )
            started_snapshot = mark_student_node_started(
                student_state_store,
                student_id=student_id,
                node_id=graph_anchor_id,
                question=updated_goal or learning_target or topic,
                title=graph_anchor,
            )
            if started_snapshot:
                student_state_snapshot = started_snapshot

        graph_instruction = _build_graph_instruction_block(
            {**state, "user_knowledge_graph": user_kg},
            active_graph_context,
            topic=topic,
            learning_target=updated_goal or learning_target or topic,
            diff=diff,
            strategy=strategy,
        )
        # 追加图谱驱动的前驱缺口提示和后继路径提示
        if prerequisite_gap_hint:
            graph_instruction += prerequisite_gap_hint
        if successor_path_hint:
            graph_instruction += successor_path_hint

        system_content = build_teacher_voice(
            f"""你现在负责正式讲解环节，要把一个知识点讲得既有方向感，又让学生愿意继续跟着你走。

当前学生档案：
- 知识水平：{diff["depth"]}
- 你的角色定位：{diff["persona"]}
- 讲解风格：{diff["style"]}
- 字数控制：{diff["length"]}{weak_hint}

讲解要求：
1. 开头 **直接进入实质**，不说"好的让我解释"，不重复学生的问题
2. 每轮只解释 **一个关键点**——宁可短，也不要让学生不知道抓住什么
3. 如果适合，给一个贴近日常直觉的类比、判断口诀或观察角度
4. 如果学生容易混淆两个概念，要直接点破"不要把 A 和 B 混在一起"
5. **提问是教学工具**，每次提问都有明确预期——你期待学生回答什么、这个回答能告诉你什么
6. 如果有【图谱 2.1 当前节点材料】，必须先覆盖该材料中的学习目标、必会要点、常见误区和节点解释，再做扩展
7. 如果有证据资料，优先使用这些证据来组织讲解
8. 如果使用了证据，每一句事实性内容后面都必须加上形如 [1]、[2] 的行内引用
9. 不要输出"参考来源"列表，来源面板由系统单独渲染
10. 如果没有证据资料，你仍然要基于你作为专业领域专家的知识来讲解，但请注意：
   - 讲解内容必须准确、负责，不确定的地方要明确说明
   - 可以适当推荐学生查阅哪些经典教材或资料
   - 不要因为缺少资料就拒绝讲解或要求学生换问法
11. 默认输出自然中文段落；除非确实在给步骤或对比，否则不要用列表{knowledge_source_hint}{graph_instruction}"""
        )

        strategy_inst = _strategy_instruction(strategy, feedback, attempt_count)
        transition_hint = ""
        if next_step_choice == "continue_deeper":
            transition_hint = "\n【用户要求】这次不要停留在入门概念上，请顺着刚才那一步继续往深处讲，尽量补足判断依据、边界和常见误区。"
        elif next_step_choice == "example_first":
            transition_hint = "\n【用户要求】这次优先换一个更直观的例子或场景来讲，不要照着上一轮的表述重复。"
        elif next_step_choice == "summarize_now":
            transition_hint = "\n【用户要求】这次先不要展开新内容，优先把刚才那一步压成一个短总结，方便学生抓住主线。"

        if citation_plan and not has_node_content_context:
            human_content = f"""请讲解主题：【{topic}】
当前用户这次最想解决的问题：【{updated_goal or topic}】
当前会话目标：【{session_goal or updated_goal or topic}】
当前这一轮先抓：【{turn_goal or topic_focus or updated_goal or topic}】
用户当前状态：【{topic_background or '未明确说明'}】

{strategy_inst}{transition_hint}{knowledge_prompt}

输出要求：
- 直接输出 Markdown 或纯文本，不要输出 JSON，不要输出代码块
- 正常情况控制在 2~4 句，先把当前节点最关键的判断讲透
- 默认不要用列表，只有在明确分步骤时才用
- 每一句事实性内容后面都必须带 [n] 行内引用
- 可以做教学组织和表述润色，但不要补充证据里没有的事实
- 不要输出“参考来源”“资料如下”这类来源列表
- 可以在最后补一个短问题来探学生卡点，但不要礼貌性收尾"""
        else:
            human_content = f"""请讲解主题：【{topic}】
当前用户这次最想解决的问题：【{updated_goal or topic}】
当前会话目标：【{session_goal or updated_goal or topic}】
当前这一轮先抓：【{turn_goal or topic_focus or updated_goal or topic}】
用户当前状态：【{topic_background or '未明确说明'}】

{strategy_inst}{transition_hint}{knowledge_prompt}

输出格式要求：
- 直接输出 Markdown 或纯文本，不要输出 JSON，不要输出代码块
- 主流程节点讲授必须详实，建议 650-1000 字；不要压缩成 2~4 句短回答
- 必须按“主线解释 -> 定义归纳 -> 关键点拆解 -> 公式/图表/例子交叉说明 -> 常见误区 -> 小检查问题”的顺序组织
- 必须综合当前节点素材包中的 explanation_teacher_style、key_points、formulas、examples、figures_refs、definition_candidates、key_point_candidates、formula_candidates、example_candidates 等字段
- 如果素材包中有公式/公式候选，至少选择 1~3 个最有代表性的公式解释变量含义、适用场景和直观意义
- 如果素材包中有例子/例子候选，至少给出 1 个教材例子或工程类比，并说明它对应哪个关键点
- 如果素材包中有图表线索或图谱媒体结果，请在正文真正讲到该图/式/表的位置单独输出一行 [[MEDIA:媒体reference]]；不要把所有媒体堆到最后
- 可以使用小标题，但不要暴露字段名、CSV 痕迹、raw id 或调试信息
- 不要写“好的”“当然”“总结一下”“希望这有帮助”
- 结尾只问一个能暴露理解边界的小问题"""

        if graph_result is not None and not has_node_content_context:
            graph_answer_text = normalize_graph_answer(
                str(graph_result.get("answer") or ""),
                list(graph_result.get("media_items") or []),
            )
            if graph_answer_text:
                graph_payload = dict(graph_result)
                graph_payload["answer"] = graph_answer_text
                full_response = build_learning_answer_html(graph_payload).strip()
            else:
                full_response = _build_evidence_backed_fallback(topic, citation_plan)
            stream_text_chunks(event_sink, "tutor", full_response)
        else:
            system_msg = SystemMessage(content=system_content)
            human_msg = HumanMessage(content=human_content)
            raw_response, stream_failed = _collect_llm_text_with_fallback(
                tutor_llm,
                [system_msg, human_msg],
                source="tutor",
                prefer_invoke=llm_stream_disabled,
            )
            if stream_failed:
                llm_stream_disabled = True
                llm_stream_failures += 1

            if citation_plan and not has_node_content_context:
                full_response = _filter_cited_lines(raw_response, len(citation_plan))
                if not full_response:
                    full_response = _build_evidence_backed_fallback(topic, citation_plan)
            else:
                full_response = _render_teacher_reply(raw_response, topic)
                if not full_response:
                    full_response = _build_resilient_teacher_fallback(
                        topic,
                        learning_target=updated_goal or learning_target or topic,
                        graph_context=active_graph_context,
                    )

            if has_node_content_context:
                graph_payload = dict(graph_result or {})
                graph_payload["answer"] = full_response
                graph_payload.setdefault("question", updated_goal or learning_target or topic)
                graph_payload.setdefault("media_items", list((graph_result or {}).get("media_items", []) or []))
                graph_payload.setdefault("evidence_items", list((graph_result or {}).get("evidence_items", []) or []))
                rich_html = build_learning_answer_html(graph_payload).strip()
                if rich_html:
                    full_response = rich_html
                    event_sink.emit(
                        make_event(
                            "node.stream",
                            "tutor",
                            data={"text": full_response, "kind": "graph_rag_answer"},
                        )
                    )
                else:
                    stream_text_chunks(event_sink, "tutor", full_response)
            else:
                stream_text_chunks(event_sink, "tutor", full_response)

        # ── 提取并处理教学标记（掌握度更新、节点跳转）──
        full_response, teaching_markers = _extract_teaching_markers(full_response)
        returned_graph_context = dict(active_graph_context)
        next_graph_title = ""
        next_graph_query = ""
        for marker in teaching_markers:
            marker_type = str(marker.get("type") or "").strip()
            marker_value = str(marker.get("value") or "").strip()
            if marker_type == 'mastered':
                resolved_title, _ = _resolve_graph_marker_reference(
                    knowledge_provider,
                    marker_value,
                    fallback_context=active_graph_context,
                )
                kg_key = resolved_title or marker_value
                prev = user_kg.get(kg_key, {})

                # ── 掌握度门控校验 ──
                if _validate_mastery_claim(user_kg, kg_key):
                    new_status = "mastered"
                else:
                    new_status = "in_progress"

                user_kg[kg_key] = {
                    **(prev if isinstance(prev, dict) else {}),
                    "status": new_status,
                    "turn_count": int((prev.get("turn_count") or 0) if isinstance(prev, dict) else 0),
                }
                event_sink.emit(make_event("graph.node_update", "tutor",
                    message=f"{'已掌握' if new_status == 'mastered' else '学习中（轮次不足）'}：{kg_key}",
                    data={"title": kg_key, "status": new_status, "type": "mastered" if new_status == "mastered" else "in_progress"}))
            elif marker_type == 'skipped':
                resolved_title, _ = _resolve_graph_marker_reference(
                    knowledge_provider,
                    marker_value,
                    fallback_context=active_graph_context,
                )
                kg_key = resolved_title or marker_value
                prev = user_kg.get(kg_key, {})
                user_kg[kg_key] = {
                    **(prev if isinstance(prev, dict) else {}),
                    "status": "skipped",
                    "turn_count": int((prev.get("turn_count") or 0) if isinstance(prev, dict) else 0),
                }
                event_sink.emit(make_event("graph.node_update", "tutor",
                    message=f"已跳过：{kg_key}",
                    data={"title": kg_key, "status": "skipped", "type": "skipped"}))
            elif marker_type == 'next_node':
                if not next_graph_title:
                    next_graph_title = str(marker.get("title") or "").strip()
                    next_graph_query = str(marker.get("id") or next_graph_title).strip()
                event_sink.emit(make_event("graph.node_update", "tutor",
                    message=f"即将进入：{next_graph_title}",
                    data={
                        "title": next_graph_title,
                        "id": str(marker.get("id") or "").strip(),
                        "status": "upcoming",
                        "type": "next",
                    }))

        if next_graph_query:
            next_graph_context = _resolve_graph_context_for_title(knowledge_provider, next_graph_query)
            if not next_graph_context:
                next_graph_context = _minimal_graph_context(next_graph_title, next_graph_query)
            returned_graph_context = _coalesce_graph_context({}, next_graph_context)

        event_sink.emit(
            make_event(
                "node.complete",
                "tutor",
                message="这一步先讲到这里，接下来你可以自己决定是继续讲、换例子、先总结，还是来一道题。",
                data={"content_length": len(full_response), "strategy": strategy, "evidence": citation_plan},
            )
        )
        return {
            "tutor_content": full_response,
            "teaching_strategy": strategy,
            "next_step_choice": "",
            "post_eval_choice": "",
            "practice_generation_mode": "",
            "tutor_citations": citation_plan,
            "tutor_evidence": seeded_evidence or citation_plan,
            "user_knowledge_graph": user_kg,
            "graph_anchor_id": str(returned_graph_context.get("anchor_id") or ""),
            "graph_anchor_title": str(returned_graph_context.get("anchor_title") or ""),
            "graph_anchor_filename": str(returned_graph_context.get("anchor_filename") or ""),
            "current_node_id": str(returned_graph_context.get("anchor_id") or ""),
            "current_node_name": str(returned_graph_context.get("anchor_title") or ""),
            "current_node_status": "teaching" if str(returned_graph_context.get("anchor_title") or "").strip() else str(state.get("current_node_status") or ""),
            "graph_prerequisites": list(returned_graph_context.get("prerequisites") or []),
            "graph_neighbors": list(returned_graph_context.get("neighbors") or []),
            "graph_learning_objectives": list(returned_graph_context.get("learning_objectives") or []),
            "graph_must_know": list(returned_graph_context.get("must_know") or []),
            "graph_common_errors": list(returned_graph_context.get("common_errors") or []),
            "graph_target_mastery_level": str(returned_graph_context.get("target_mastery_level") or ""),
            "graph_difficulty": str(returned_graph_context.get("difficulty") or ""),
            "graph_next_steps": list(returned_graph_context.get("next_steps") or []),
            "current_user_goal": updated_goal,
            "session_goal": session_goal,
            "turn_goal": next_graph_title or turn_goal or topic_focus or updated_goal,
            "student_state_snapshot": student_state_snapshot,
            "learning_phase": "node_teaching",
            "learning_resume_target": "post_lesson_choice",
            "learning_resume_reason": "tutor_completed",
            "affect_signals": affect_signals,
            "llm_stream_disabled": llm_stream_disabled,
            "llm_stream_failures": llm_stream_failures,
        }

    return tutor_node
