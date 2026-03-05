import json

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


def build_evaluator_node(evaluator_llm, event_sink: EventSink):
    def evaluator_node(state: AgentState):
        event_sink.emit(
            make_event(
                "node.start",
                "evaluator",
                message="Evaluator node started.",
                data={"topic": state["current_topic"]},
            )
        )

        system_msg = SystemMessage(
            content="""
            你是绝对理性的阅卷机器。你只看逻辑和结果。
            你必须强制以合法的 JSON 格式输出评价结果，不要有任何 markdown 标记（如 ```json），直接输出纯 JSON 字符串。

            JSON 必须包含以下字段：
            - "total_score": 整数 (0-100)
            - "logic_score": 整数 (0-100，评估推演逻辑是否严密)
            - "concept_score": 整数 (0-100，评估专业术语和概念是否准确)
            - "feedback": 字符串 (一句话极其简短的犀利点评)
            """
        )
        human_msg = HumanMessage(
            content=f"""
            当前考核主题：{state['current_topic']}。
            测试题：{state['tester_question']}
            学生的作答：{state['user_answer']}。

            请直接输出 JSON 结果：
            """
        )

        response = evaluator_llm.invoke([system_msg, human_msg])
        full_evaluation = content_to_text(response.content).strip()

        try:
            if full_evaluation.startswith("```json"):
                full_evaluation = full_evaluation[7:-3].strip()
            elif full_evaluation.startswith("```"):
                full_evaluation = full_evaluation[3:-3].strip()

            result = json.loads(full_evaluation)
            score = int(result.get("total_score", 60))
            logic = int(result.get("logic_score", 60))
            concept = int(result.get("concept_score", 60))
            feedback = str(result.get("feedback", "解析正常，但未提取到评价。"))
            event_sink.emit(
                make_event(
                    "assessment.result",
                    "evaluator",
                    data={
                        "total_score": score,
                        "logic_score": logic,
                        "concept_score": concept,
                        "feedback": feedback,
                    },
                )
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            score = 60
            logic = 60
            concept = 60
            feedback = "系统解析答案格式失败，模型未遵循 JSON 规范。"
            event_sink.emit(
                make_event(
                    "session.warning",
                    "evaluator",
                    message=f"JSON 解析失败。原始输出: {full_evaluation}",
                )
            )
            event_sink.emit(
                make_event(
                    "assessment.result",
                    "evaluator",
                    data={
                        "total_score": score,
                        "logic_score": logic,
                        "concept_score": concept,
                        "feedback": feedback,
                    },
                )
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "evaluator",
                message="Evaluator node completed.",
            )
        )

        return {
            "score": score,
            "logic_score": logic,
            "concept_score": concept,
            "feedback": feedback,
        }

    return evaluator_node
