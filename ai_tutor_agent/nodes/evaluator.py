import json
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


class EvaluationResult(BaseModel):
    total_score: int = Field(description="整数 (0-100)，总体得分")
    logic_score: int = Field(description="整数 (0-100)，评估推演逻辑是否严密")
    concept_score: int = Field(description="整数 (0-100)，评估专业术语和概念是否准确")
    feedback: str = Field(description="字符串，一句话极其简短的犀利点评")


def build_evaluator_node(evaluator_llm, event_sink: EventSink):
    # Try to use structured output if supported by the model
    try:
        structured_llm = evaluator_llm.with_structured_output(EvaluationResult)
    except Exception:
        structured_llm = None

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
            你必须评估学生的回答，并给出详细的评分（0-100）和简短反馈。
            """
        )
        human_msg = HumanMessage(
            content=f"""
            当前考核主题：{state['current_topic']}。
            测试题：{state['tester_question']}
            学生的作答：{state['user_answer']}。
            """
        )

        if structured_llm:
            try:
                result = structured_llm.invoke([system_msg, human_msg])
                score = result.total_score
                logic = result.logic_score
                concept = result.concept_score
                feedback = result.feedback
            except Exception as e:
                print(f"⚠️ Structured output failed: {e}, falling back to manual parsing.")
                score, logic, concept, feedback = _manual_eval(evaluator_llm, system_msg, human_msg, event_sink)
        else:
            score, logic, concept, feedback = _manual_eval(evaluator_llm, system_msg, human_msg, event_sink)

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

        history = list(state.get("conversation_history", []))
        history.append(
            {
                "role": "assistant",
                "kind": "evaluator_feedback",
                "content": (
                    f"评估结果：总分 {score}，逻辑 {logic}，概念 {concept}。"
                    f" 反馈：{feedback}"
                ),
            }
        )

        return {
            "score": score,
            "logic_score": logic,
            "concept_score": concept,
            "feedback": feedback,
            "conversation_history": history,
        }

    return evaluator_node

def _manual_eval(llm, system_msg, human_msg, event_sink):
    # Fallback to manual JSON parsing with improved prompts
    prompt = f"{system_msg.content}\n\n请强制以 JSON 格式输出结果：\n{human_msg.content}"
    response = llm.invoke(prompt)
    full_evaluation = content_to_text(response.content).strip()
    
    try:
        # Clean potential markdown
        if "```json" in full_evaluation:
            full_evaluation = full_evaluation.split("```json")[1].split("```")[0].strip()
        elif "```" in full_evaluation:
            full_evaluation = full_evaluation.split("```")[1].split("```")[0].strip()

        result = json.loads(full_evaluation)
        return (
            int(result.get("total_score", 60)),
            int(result.get("logic_score", 60)),
            int(result.get("concept_score", 60)),
            str(result.get("feedback", "解析成功但内容缺失。"))
        )
    except Exception:
        event_sink.emit(make_event("session.warning", "evaluator", message="JSON解析失败，使用默认评分"))
        return 60, 60, 60, "系统解析失败，请检查模型输出。"
