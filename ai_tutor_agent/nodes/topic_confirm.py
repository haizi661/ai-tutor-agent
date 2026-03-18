from ..core.events import make_event
from ..core.ports import EventSink, AnswerProvider
from ..core.state import AgentState


def build_topic_confirm_node(event_sink: EventSink, answer_provider: AnswerProvider = None):
    def node(state: AgentState) -> dict:
        proposed_topic = state.get("proposed_topic", "").strip()
        
        # 0. 错误处理：如果没有 proposed_topic
        if not proposed_topic:
            event_sink.emit(
                make_event(
                    "session.warning",
                    "topic_confirmer",
                    message="未找到待确认主题，返回主题识别阶段。",
                )
            )
            return {"flow_status": "greeting"}

        # 1. 检查是否已经是 "awaiting_topic_confirmation" 状态
        #    如果是，说明这是“第二轮”，用户发来了消息（可能是确认，也可能是修改）
        if state.get("flow_status") == "awaiting_topic_confirmation":
            # 尝试获取用户输入
            user_input = ""
            # 从 answer_provider 中拿（如果是同步 CLI 模式，它会阻塞拿；如果是异步 API 模式，它会从 session input 队列拿）
            # 注意：这里的 prompt 仅用于 CLI 回显，Web 模式下不显示
            if answer_provider:
                try:
                    user_input = answer_provider.get_answer("", state=state).strip()
                except Exception:
                    pass # 如果拿不到，说明可能是直接调起的
            
            # 如果没有拿到 input（比如某些极端情况），则不处理，直接再次请求确认
            if user_input:
                user_msg = user_input.lower()
                yes_intents = ["yes", "y", "ok", "确认", "是的", "好", "没问题", "对", "correct", "right"]
                
                # A. 判定为确认
                if user_msg in yes_intents or user_msg == proposed_topic.lower():
                    event_sink.emit(make_event("topic.confirmed", "topic_confirmer", data={"topic": proposed_topic}))
                    return {
                        "current_topic": proposed_topic,
                        "flow_status": "assessment_pending", # 进入下一个阶段
                        "conversation_history": state.get("conversation_history", []) + [
                            {"role": "user", "content": user_input},
                            {"role": "assistant", "content": f"好的，已确认主题：{proposed_topic}。"}
                        ]
                    }
                
                # B. 判定为修改 (用户输入了其他内容)
                else:
                    new_topic = user_input
                    event_sink.emit(make_event("topic.changed", "topic_confirmer", data={"old": proposed_topic, "new": new_topic}))
                    return {
                        "proposed_topic": new_topic,
                        # 递归自己：把状态重置为 pending，让下面的逻辑重新发确认卡片
                        "flow_status": "topic_confirmation_pending", 
                        "conversation_history": state.get("conversation_history", []) + [
                            {"role": "user", "content": user_input},
                            {"role": "assistant", "content": f"好的，根据您的输入，我将主题修改为：{new_topic}。请确认。"}
                        ]
                    }

        # 2. 默认行为：发送确认请求（第一次进入，或被重置为 pending 后）
        event_sink.emit(
            make_event(
                "topic.confirmation_needed",
                "topic_confirmer",
                message=f"我理解你想学的是【{proposed_topic}】。请确认或修改主题。",
                data={"proposed_topic": proposed_topic},
            )
        )
        
        # 对于 CLI 模式，我们需要在此处“阻塞”等待输入，否则会在此处 Pause
        # 但为了保持和 Web 异步模式一致，我们让它 Pause
        # 除非 answer_provider 是 CLIAdapter，它可以同步获取
        # 这里为了解决死循环，我们不强制在这里阻塞，而是依赖下次 invoke 带入 input
        
        event_sink.emit(
            make_event(
                "node.complete",
                "topic_confirmer",
                message="等待用户确认学习主题。",
            )
        )
        return {"flow_status": "awaiting_topic_confirmation"}

    return node
