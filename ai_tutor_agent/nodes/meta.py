from langchain_core.messages import HumanMessage, SystemMessage

from ..config import Settings
from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


def _build_meta_system(settings: Settings) -> str:
    profile_map = {
        "gemini": "Gemini", "qwen": "Qwen", "deepseek": "DeepSeek",
        "openai": "OpenAI / GPT", "minimax": "MiniMax", "glm": "GLM", "custom": "Custom",
    }
    profile_label = profile_map.get(settings.chat_profile, settings.chat_profile or "Custom")
    model_name = settings.model_name or "未配置"

    return f"""你是一位AI伴学助手，现在有学生在问关于"你是谁/你能做什么/怎么配置"之类的系统问题。

你的真实情况：
- 当前使用的模型档案：{profile_label}（模型：{model_name}）
- 可用档案：Gemini、Qwen、DeepSeek、OpenAI/GPT、MiniMax、GLM、Custom
- 核心能力：学前测评（20题摸底）→ 六维能力画像 → 自适应讲解 → 出题考核 → 评估+参考答案 → 闭环循环
- 知识库：支持上传讲义/笔记，RAG 检索增强讲解
- 教学策略：自动根据掌握程度切换（标准讲解/类比/逐步拆解/苏格拉底法）

回答原则：
1. 直接、准确地回答，用自然语言，不要列太多条款
2. 回答限2~4句，简洁有力
3. 友善收尾，询问"还有什么想知道的，或者准备开始学点什么？"——但措辞要有变化，不要每次都一样
4. 禁止说空话套话"""


def build_meta_node(settings: Settings, llm, event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        user_text = state.get("current_topic", "").strip()

        event_sink.emit(
            make_event(
                "node.start",
                "meta_qa",
                message="正在回答关于系统的问题…",
            )
        )

        system_msg = SystemMessage(content=_build_meta_system(settings))
        human_msg = HumanMessage(content=user_text or "你能做什么？")

        full_response = ""
        for chunk in llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(
                make_event("node.stream", "meta_qa", data={"text": chunk_text})
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "meta_qa",
                message="系统问题已回答，等待下一步输入。",
            )
        )

        next_input = answer_provider.get_answer(
            prompt="还有什么想知道的，或者准备开始学点什么？",
            state=state,
        )
        return {
            "current_topic": next_input,
            "flow_status": "greeting",
        }

    return node
