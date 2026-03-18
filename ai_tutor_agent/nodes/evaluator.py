import json
import sqlite3#检查轮数
from langchain_core.messages import HumanMessage, SystemMessage
from ..core.events import make_event
from ..core.ports import RuntimeContext, EventSink
from ..core.state import AgentState
from ..core.text import content_to_text

# 注意：这里第二个参数改为 runtime，因为 workflow.py 里可以轻松获取它
def build_evaluator_node(evaluator_llm, runtime: RuntimeContext):
    # 尝试结构化输出
    structured_llm = None
    try:
        # 保持你原来的 EvaluationResult 导入逻辑
        from .evaluator_schema import EvaluationResult 
        structured_llm = evaluator_llm.with_structured_output(EvaluationResult)
    except Exception:
        pass

    def evaluator_node(state: AgentState):
        # 从 runtime 中提取 event_sink
        print(f"DEBUG: 进入了评估节点, state keys: {list(state.keys())}")
        event_sink = runtime.event_sink
        
        event_sink.emit(
            make_event(
                "node.start",
                "evaluator",
                message="Evaluator node started.",
                data={"topic": state["current_topic"]},
            )
        )

        # 0. 检查是否跳过
        user_answer = state.get("user_answer", "").strip()
        if user_answer.lower() in ["/skip", "/pass", "skip", "掌握", "已掌握", "跳过"]:
             event_sink.emit(make_event("node.info", "evaluator", message="User skipped assessment (mastered)."))
             return {
                 "score": 100,
                 "logic_score": 100,
                 "concept_score": 100,
                 "feedback": "用户自评已掌握该知识点。",
                 "skip_reason": "user_mastered"
             }

        # 0.5 RAG: 检索参考答案 (Ground Truth)
        knowledge_provider = runtime.knowledge_provider
        # 使用题目作为检索词
        search_query = f"{state['current_topic']} {state['tester_question']}"
        context = knowledge_provider.query(search_query)
        
        rag_prompt = ""
        if context:
            rag_prompt = (
                f"\n\n【参考答案/评分依据】\n"
                f"以下是知识库中关于该题目的相关资料，请以此为【最高标准】进行评分。"
                f"如果学生的回答与参考资料冲突，以资料为准；如果资料未覆盖，则使用通用知识。\n"
                f"---\n{context}\n---\n"
            )
            print(f"✅ [Evaluator] RAG 检索命中，长度: {len(context)}")
        else:
            print(f"⚠️ [Evaluator] RAG 未命中，使用通用知识评分")

        system_msg = SystemMessage(
            content="你是绝对理性的阅卷机器。你只看逻辑和结果。你必须评估学生的回答，并给出详细的评分（0-100）和简短反馈。"
        )
        human_msg = HumanMessage(
            content=f"当前考核主题：{state['current_topic']}。\n测试题：{state['tester_question']}\n学生的作答：{state['user_answer']}。\n{rag_prompt}"
        )

        # 1. 评分逻辑
        if structured_llm:
            try:
                res = structured_llm.invoke([system_msg, human_msg])
                score, logic, concept, feedback = res.total_score, res.logic_score, res.concept_score, res.feedback
            except Exception:
                score, logic, concept, feedback = _manual_eval(evaluator_llm, system_msg, human_msg, event_sink)
        else:
            score, logic, concept, feedback = _manual_eval(evaluator_llm, system_msg, human_msg, event_sink)

# --- 2. 自动总结逻辑 ---
        db_path = None
        try:
            if hasattr(runtime, 'settings'):
                db_path = runtime.settings.memory_db_path
            elif hasattr(runtime, 'config'):
                db_path = runtime.config.memory_db_path
        except Exception:
            db_path = None

        if db_path:
            try:
                import sqlite3 # 确保导入了
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM checkpoints")
                count = cursor.fetchone()[0]
                
                # 调试打印：让你看到现在数据库里有多少条记录
                print(f"DEBUG: 数据库 checkpoints 记录数 = {count}", flush=True)

                # 满足 10 轮且是 10 的倍数时执行（测试时可以临时改成 > 0）
                if count >= 0:
                    print("📢 触发长期记忆总结...", flush=True)
                    student_id = state.get("student_id", "default_student")
                    summary_prompt = f"请简要总结学生(ID:{student_id})的表现，100字以内。"
                    summary_res = evaluator_llm.invoke([HumanMessage(content=summary_prompt)])
                    summary_text = content_to_text(summary_res.content)
                    
                    cursor.execute(
                        "INSERT INTO long_term_memory (student_id, summary) VALUES (?, ?)",
                        (student_id, summary_text)
                    )
                    conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠️ 数据库操作跳过: {e}", flush=True)
        # ------------------------------------

        # 3. 后续的事件发送逻辑（确保缩进和 def evaluator_node 对齐）
        event_sink.emit(
            make_event(
                "assessment.result",
                "evaluator",
                data={"total_score": score, "logic_score": logic, "concept_score": concept, "feedback": feedback},
            )
        )

        event_sink.emit(
            make_event("node.complete", "evaluator", message="Evaluator node completed.")
        )

        return {
            "score": score,
            "logic_score": logic,
            "concept_score": concept,
            "feedback": feedback,
            "skip_reason": "",
        }

    return evaluator_node

# 记得保留你文件末尾原来的 _manual_eval 函数定义

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
