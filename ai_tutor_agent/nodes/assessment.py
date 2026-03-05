import json
from typing import Any, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


class AssessmentQuestion(BaseModel):
    id: int = Field(description="Unique ID for the question, 1-20")
    type: str = Field(description="Type of question: 'self_eval' or 'objective'")
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 options (A, B, C, D)")


class AssessmentList(BaseModel):
    questions: List[AssessmentQuestion]


def build_assessment_generator_node(llm, event_sink: EventSink):
    def node(state: AgentState):
        topic = state["current_topic"]
        event_sink.emit(
            make_event("node.start", "assessment_generator", message=f"正在为【{topic}】生成测评量表...")
        )

        system_msg = SystemMessage(
            content="你是一位资深的教育测评专家，擅长设计精准的学习前评估量表。"
        )
        human_msg = HumanMessage(
            content=f"""
            请针对学习主题【{topic}】，设计一份包含20道题目的测评量表。
            
            量表结构如下：
            1. 第一部分：用户自我评估掌握情况（10题）。侧重于询问用户对于该主题相关概念、技能的熟悉程度和自信度。
               - 类型标记为 'self_eval'。
               - 题号 1-10。
               - 选项设置为程度递进，例如 A.完全不懂 B.听说过 C.了解基本概念 D.熟练掌握。
            
            2. 第二部分：主题相关基础题（10题）。侧重于通过客观题目测试用户的基础知识水平。
               - 类型标记为 'objective'。
               - 题号 11-20。
               - 均为单项选择题，4个选项。
            
            请直接输出合法的JSON格式，不包含Markdown代码块标记。
            Schema:
            {{
                "questions": [
                    {{
                        "id": 1,
                        "type": "self_eval",
                        "question": "...",
                        "options": ["A...", "B...", "C...", "D..."]
                    }},
                    ...
                ]
            }}
            """
        )

        parser = JsonOutputParser(pydantic_object=AssessmentList)
        
        # Use simple invoke for structured output if possible, but stream is safer for long content debugging
        response_content = ""
        for chunk in llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            response_content += chunk_text
            # We don't stream the generation text to user because it's JSON
        
        try:
            # Clean up potential markdown blocks if LLM ignores instructions
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            
            parsed = json.loads(cleaned_content)
            questions = parsed.get("questions", [])
        except Exception as e:
            # Fallback or retry logic could go here. For now, log error.
            event_sink.emit(make_event("error", "assessment_generator", message=f"Failed to parse assessment: {str(e)}"))
            questions = []

        event_sink.emit(
            make_event("node.complete", "assessment_generator", message="测评量表生成完毕。", data={"count": len(questions)})
        )
        return {"assessment_questions": questions}

    return node


def build_assessment_conductor_node(event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState):
        questions = state.get("assessment_questions", [])
        if not questions:
            return {}

        event_sink.emit(
            make_event("node.start", "assessment_conductor", message="开始进行学前测评...")
        )

        answers = {}
        
        # Present questions one by one
        for q in questions:
            q_text = f"【第{q['id']}题】 {q['question']}\n"
            for opt in q['options']:
                q_text += f"{opt}\n"
            
            # Send question to user via event (so frontend/CLI can render)
            event_sink.emit(
                make_event("assessment.question", "assessment_conductor", data={"question": q}, message=q_text)
            )
            
            # Get answer
            user_ans = answer_provider.get_answer(
                prompt=f"请选择 (A/B/C/D): ",
                state=state
            )
            answers[q['id']] = user_ans.strip().upper()

        event_sink.emit(
            make_event("node.complete", "assessment_conductor", message="测评完成，正在生成画像...")
        )
        return {"assessment_answers": answers}

    return node


def build_user_profiler_node(llm, event_sink: EventSink):
    def node(state: AgentState):
        topic = state["current_topic"]
        questions = state.get("assessment_questions", [])
        answers = state.get("assessment_answers", {})
        
        event_sink.emit(
            make_event("node.start", "user_profiler", message="正在分析用户能力模型...")
        )

        # Serialize Q&A for the LLM
        qa_pair_text = ""
        for q in questions:
            qid = q['id']
            ans = answers.get(qid, "未作答")
            qa_pair_text += f"Q{qid} [{q['type']}]: {q['question']}\nOptions: {q['options']}\nMy Answer: {ans}\n\n"

        system_msg = SystemMessage(
            content="你是一位教育心理学专家和数据分析师，擅长通过测评数据构建用户学习画像。"
        )
        human_msg = HumanMessage(
            content=f"""
            请根据以下测评数据，为学习主题【{topic}】生成一份用户能力画像报告。

            输入数据：
            {qa_pair_text}

            要求：
            1. 根据学习主题【{topic}】，自动划分出6个相关的核心能力维度。
            2. 根据用户的作答情况（自我评估 + 客观题），对这6个维度进行打分（0-100分）。
               - 必须分别给出【自我评估得分】和【客观评价得分】。
               - 自我评估得分基于 'self_eval' 类题目的回答。
               - 客观评价得分基于 'objective' 类题目的正确率（需要你自行判断正确答案）。
            3. 生成一份Markdown格式的报告，包含：
               - 标题：【{topic}】学习能力画像
               - 核心能力雷达图列表（列出6个维度及其两组得分）。
               - 综合分析：对比自我认知与客观水平的差异，给出学习建议。
            
            请直接输出Markdown报告内容。
            """
        )

        full_response = ""
        for chunk in llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(
                make_event("node.stream", "user_profiler", data={"text": chunk_text})
            )
        
        event_sink.emit(
            make_event("node.complete", "user_profiler", message="用户画像生成完毕。")
        )
        
        return {
            "assessment_result": full_response,
            "is_assessed": True
        }

    return node
