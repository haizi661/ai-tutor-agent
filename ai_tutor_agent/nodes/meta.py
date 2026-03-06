from ..config import Settings
from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState


PROFILE_LABELS = {
    "gemini": "Gemini",
    "qwen": "Qwen",
    "deepseek": "DeepSeek",
    "openai": "OpenAI / GPT",
    "minimax": "MiniMax",
    "glm": "GLM",
    "custom": "Custom",
}


def _current_profile_text(settings: Settings) -> str:
    profile_label = PROFILE_LABELS.get(settings.chat_profile, settings.chat_profile or "Custom")
    return f"当前默认使用的是 `{profile_label}` 档案，模型是 `{settings.model_name}`。"


def _build_meta_answer(user_text: str, settings: Settings) -> str:
    normalized = user_text.strip()

    if "模型" in normalized:
        return (
            f"{_current_profile_text(settings)} "
            "如果你愿意，也可以在“本地配置”里切到 Qwen、DeepSeek、OpenAI、MiniMax 或 GLM。"
        )
    if "能做什么" in normalized or "会什么" in normalized:
        return (
            "我是一个伴学智能体，能先做学前测评、生成能力画像、按你的掌握情况讲解知识、出题检查、分析错因，也能简单聊几句。"
        )
    if "聊天" in normalized:
        return "可以简单聊几句，但我的核心定位还是伴学和讲解知识，不是无限开放的通用聊天机器人。"
    if "前测" in normalized or "画像" in normalized:
        return "前测用于摸底你的基础，画像会把自评和客观题结果整理成固定维度的能力雷达图，再决定后续讲解策略。"
    if "配置" in normalized or "本地配置" in normalized:
        return "本地配置页主要用于个人本地使用：选择厂商、模型并填写对应 API Key，系统会自动匹配接口地址。"
    if "知识库" in normalized or "rag" in normalized.lower():
        return "知识库用于在讲解前检索本地资料，当前默认是轻量 RAG：切块、向量化、取 Top-K，再把相关内容注入导师讲解。"
    if "你是谁" in normalized:
        return "我是你的伴学导师，重点不是陪聊，而是帮你确认主题、评估基础、讲解、出题和纠错。"
    return (
        f"{_current_profile_text(settings)} "
        "如果你想问配置、前测、能力画像或知识库，也可以继续问。"
    )


def build_meta_node(settings: Settings, event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        user_text = state.get("current_topic", "").strip()
        answer = _build_meta_answer(user_text, settings)
        event_sink.emit(
            make_event(
                "node.start",
                "meta_qa",
                message="正在回答系统相关问题...",
            )
        )
        event_sink.emit(
            make_event("node.stream", "meta_qa", data={"text": answer})
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "meta_qa",
                message="系统问题已回答，等待下一步输入。",
            )
        )
        next_input = answer_provider.get_answer(
            prompt="如果你准备开始学习，直接告诉我主题；如果还想继续问系统问题，也可以继续输入。",
            state=state,
        )
        return {
            "current_topic": next_input,
            "flow_status": "greeting",
        }

    return node
