import re

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState


STUDY_PATTERNS = [
    r"我想学",
    r"想学习",
    r"帮我学",
    r"教我",
    r"讲讲",
    r"复习",
    r"解释一下",
    r"题目",
    r"知识点",
    r"高等数学",
    r"控制理论",
    r"线性代数",
]

META_PATTERNS = [
    r"你是什么模型",
    r"你用什么模型",
    r"你是啥模型",
    r"当前.*模型",
    r"你是谁",
    r"你能做什么",
    r"会什么",
    r"怎么切换模型",
    r"怎么配置",
    r"本地配置",
    r"前测",
    r"能力画像",
    r"知识库",
    r"rag",
    r"可以聊天吗",
    r"能聊天吗",
]

SMALLTALK_PATTERNS = [
    r"^你好[呀啊]?[,，!！。？? ]*$",
    r"^您好[,，!！。？? ]*$",
    r"^哈喽[,，!！。？? ]*$",
    r"^嗨[,，!！。？? ]*$",
    r"^在吗[？?]?$",
    r"谢谢",
    r"辛苦了",
    r"聊聊天",
    r"有点焦虑",
    r"有点紧张",
    r"有点烦",
    r"心情不好",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _looks_like_meta_question(text: str) -> bool:
    normalized = text.strip().lower()
    if _matches_any(normalized, META_PATTERNS):
        return True

    if any(token in normalized for token in ["前测", "画像", "知识库", "rag", "本地配置", "api key"]):
        return True

    if "模型" in normalized and any(
        token in normalized
        for token in ["什么", "哪些", "哪个", "切换", "支持", "当前", "默认", "档案", "厂商", "厂家", "供应商", "配置", "列表"]
    ):
        return True

    if any(token in normalized for token in ["你是谁", "你能做什么", "会什么", "怎么配置", "能聊天", "可以聊天"]):
        return True

    return False


def classify_intent(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return "smalltalk"
    if _looks_like_meta_question(cleaned):
        return "meta_qa"
    if _matches_any(cleaned, STUDY_PATTERNS):
        return "study_topic"
    if _matches_any(cleaned, SMALLTALK_PATTERNS):
        return "smalltalk"
    return "study_topic"


def build_intake_router_node(event_sink: EventSink):
    def node(state: AgentState) -> dict:
        user_input = state.get("current_topic", "").strip()
        intent = classify_intent(user_input)
        event_sink.emit(
            make_event(
                "node.start",
                "intake_router",
                message="正在判断当前输入是学习主题、系统问题还是轻闲聊...",
                data={"input": user_input},
            )
        )
        event_sink.emit(
            make_event(
                "intent.detected",
                "intake_router",
                message=f"当前输入被识别为：{intent}",
                data={"intent": intent, "input": user_input},
            )
        )

        next_status = {
            "study_topic": "topic_intake",
            "meta_qa": "meta_qa",
            "smalltalk": "smalltalk",
        }[intent]
        event_sink.emit(
            make_event(
                "node.complete",
                "intake_router",
                message="入口意图判断完成。",
            )
        )
        return {"flow_status": next_status}

    return node
