from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
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

        system_content = f"""你是一位顶尖的自适应AI教师，拥有20年教学经验，能根据每位学生的水平动态调整教学方式。

当前学生档案：
- 知识水平：{diff["depth"]}
- 你的角色定位：{diff["persona"]}
- 讲解风格：{diff["style"]}
- 字数控制：{diff["length"]}{weak_hint}

核心准则（必须遵守）：
1. 用"你"直接称呼学生，一对一辅导感
2. 绝不说空话套话，每句话都有实质内容
3. 讲解结束时必须用「💡 本次核心要点：」总结 1~2 句关键记忆点
4. 如果有参考资料，优先参考，但要用自己的话讲，不要照搬原文
5. 根据难度级别严格匹配用语复杂度"""

        strategy_inst = _strategy_instruction(strategy, feedback, attempt_count)
        human_content = f"""请讲解主题：【{topic}】

{strategy_inst}{knowledge_prompt}

输出格式要求：
- 直接开始讲解正文，不要说"好的"、"当然"、"没问题"之类的开场白
- 结尾必须有「💡 本次核心要点：」一行总结"""

        system_msg = SystemMessage(content=system_content)
        human_msg = HumanMessage(content=human_content)

        full_response = ""
        for chunk in tutor_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tutor",
                    data={"text": chunk_text},
                )
            )

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
