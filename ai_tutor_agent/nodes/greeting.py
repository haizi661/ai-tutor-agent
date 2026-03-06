import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink, AnswerProvider
from ..core.state import AgentState
from ..core.text import content_to_text


AMBIGUOUS_INPUTS = {
    "",
    "hi",
    "hello",
    "你好",
    "您好",
    "嗨",
    "哈喽",
    "在吗",
    "有人吗",
    "额",
    "呃",
    "嗯",
    "em",
    "emm",
    "emmm",
    "?",
    "？",
}


def _looks_ambiguous(text: str) -> bool:
    cleaned = text.strip().lower()
    if cleaned in AMBIGUOUS_INPUTS:
        return True
    if len(cleaned) <= 2 and not re.search(r"[a-zA-Z0-9\u4e00-\u9fff]{3,}", cleaned):
        return True
    if cleaned in {"不知道", "随便", "没想好", "先聊聊", "先看看"}:
        return True
    return False


# ---------------------------------------------------------------------------
# Greeter Node - Figure out what the user wants to learn
# ---------------------------------------------------------------------------
def build_greeting_node(llm, event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        user_input = state.get("current_topic", "").strip()
        
        event_sink.emit(
            make_event(
                "node.start",
                "greeter",
                message="正在与用户沟通学习需求...",
            )
        )

        if _looks_ambiguous(user_input):
            event_sink.emit(
                make_event(
                    "node.complete",
                    "greeter",
                    message="用户输入还不足以确认学习主题，继续追问。",
                )
            )
            new_input = answer_provider.get_answer(
                prompt="我还没听清你想学什么。请直接告诉我一个明确主题，例如“控制理论”“高等数学”“PID 控制器”。",
                state=state,
            )
            return {"current_topic": new_input, "flow_status": "greeting"}

        system_msg = SystemMessage(
            content="""你是一位AI伴学导师，负责确认用户真正想学习的主题。
你的输出必须遵守以下 JSON schema，不要输出其他内容：
{
  "status": "confirmed" | "clarify",
  "topic": "如果已确认则写核心主题，否则空字符串",
  "assistant_reply": "如果还需要追问，给用户一句简洁明确的追问；如果已确认，这里可以为空字符串"
}

判断规则：
1. "你好"、"额"、"在吗"、"先看看"、"不知道学什么" 这类都不算学习主题，返回 clarify。
2. 只有用户明确说出知识点、课程、技能、概念、问题类型时，才返回 confirmed。
3. 不要把寒暄、语气词、模糊表达误判成主题。
4. 如果用户说“我想学控制理论”“给我讲讲 PID”“复习高数极限”，请提取核心主题。"""
        )
        human_msg = HumanMessage(content=f"用户的输入: {user_input}")

        # 收集结构化识别结果，不向前端流式暴露原始中间文本
        full_response = ""
        for chunk in llm.stream([system_msg, human_msg]):
            full_response += content_to_text(chunk.content)

        try:
            cleaned = full_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:].split("```")[0].strip()
                
            if cleaned.startswith("{") and cleaned.endswith("}"):
                data = json.loads(cleaned)
                status = data.get("status")
                topic = (data.get("topic") or "").strip()
                assistant_reply = (data.get("assistant_reply") or "").strip()
                if status == "confirmed" and topic:
                    event_sink.emit(make_event("node.complete", "greeter", message=f"已识别候选主题: {topic}"))
                    return {
                        "proposed_topic": topic,
                        "flow_status": "topic_confirmation_pending",
                    }
                if status == "clarify":
                    event_sink.emit(make_event("node.complete", "greeter", message="等待用户进一步澄清学习主题..."))
                    new_input = answer_provider.get_answer(
                        prompt=assistant_reply or "请直接告诉我一个明确的学习主题。",
                        state=state,
                    )
                    return {"current_topic": new_input, "flow_status": "greeting"}
        except Exception:
            pass

        event_sink.emit(make_event("node.complete", "greeter", message="等待用户确认学习主题..."))
        new_input = answer_provider.get_answer(
            prompt="请直接告诉我你想学的具体主题，例如“线性代数矩阵乘法”或“控制理论中的 PID”。",
            state=state
        )

        return {"current_topic": new_input, "flow_status": "greeting"}

    return node
