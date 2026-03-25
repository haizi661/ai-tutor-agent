from langchain_core.messages import HumanMessage, SystemMessage
import sqlite3
import sys

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text

def build_tutor_node(tutor_llm, runtime: RuntimeContext):
    def tutor_node(state: AgentState):
        # 使用 stderr 强制输出，这通常会绕过普通的 print 缓存
        #raise ValueError("WORKS")
        sys.stderr.write("\n" + "="*50 + "\n")
        sys.stderr.write("🔥 [CRITICAL DEBUG] TUTOR NODE IS RUNNING!\n")
        sys.stderr.write(f"🔥 当前主题: {state.get('current_topic')}\n")
        sys.stderr.write("="*50 + "\n")
        sys.stderr.flush()

        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider

        event_sink.emit(
            make_event(
                "node.start",
                "tutor",
                message="Tutor node started.",
                data={"topic": state["current_topic"]},
            )
        )

        # --- 安全获取数据库路径并读取长期记忆 ---
        db_path = None
        if hasattr(runtime, 'settings'):
            db_path = runtime.settings.memory_db_path
        elif hasattr(runtime, 'config'):
            db_path = runtime.config.memory_db_path
            
        long_term_context = ""
        if db_path:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # 查出这个学生最近的 3 条学习总结
                cursor.execute(
                    "SELECT summary FROM long_term_memory WHERE student_id = ? ORDER BY created_at DESC LIMIT 3", 
                    (state.get("student_id", "default_student"),)
                )
                summaries = cursor.fetchall()
                if summaries:
                    long_term_context = "\n【学生往期学习背景】：\n" + "\n".join([s[0] for s in summaries])
                conn.close()
            except Exception as e:
                print(f"⚠️ 读取长期记忆跳过: {e}\n")
        # ----------------------------------------

        # RAG 逻辑: 智能构建查询词
        history = list(state.get("conversation_history", []))
        last_user_msg = ""
        # 寻找最近的一条用户消息
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_msg = str(msg.get("content", "")).strip()
                break
        
        search_query = state["current_topic"]
        rag_reason = "topic_only"

        # 策略1: 错题讲解模式 -> Topic + 错因
        if state.get("feedback"):
             search_query = f"{state['current_topic']} {state['feedback']}"
             rag_reason = "topic_with_feedback"
        # 策略2: 追问模式 -> Topic + 用户问题
        elif last_user_msg:
             search_query = f"{state['current_topic']} {last_user_msg}"
             rag_reason = "topic_with_question"
        
        rag_hybrid_enabled = bool(
            getattr(getattr(runtime, "settings", None), "rag_hybrid_enabled", False)
        )
        rag_mode = "hybrid" if rag_hybrid_enabled else "vector"
        sys.stderr.write(f"🔍 [RAG] 由于 {rag_reason}，使用查询词: '{search_query}'\n")
        sys.stderr.write(f"[RAG][node_query] node=tutor mode={rag_mode} query={search_query}\n")

        context = knowledge_provider.query(search_query)
        knowledge_prompt = ""
        
        if context:
            # 增强 Prompt，明确要求引用
            knowledge_prompt = (
                f"\n\n【必须参考的知识库内容】\n"
                f"以下是从知识库中检索到的关于“{search_query}”的相关资料，"
                f"请务必优先基于这些资料回答，如果资料不足再补充通用知识：\n"
                f"---\n{context}\n---\n"
            )
            sys.stderr.write(f"✅ RAG 检索成功，内容长度: {len(context)}\n")
        else:
            sys.stderr.write("⚠️ RAG 未检索到相关内容\n")
        sys.stderr.flush()

        system_msg = SystemMessage(
            content="你是一位拥有20年教龄的顶尖工科教授，性格极度耐心、温柔，最擅长把极其复杂的理论转化为通俗易懂的工程或生活案例。"
        )

        if state.get("feedback"):
            human_content = f"""
                {long_term_context}
                学生在考核时失败了。
                错因反馈是：{state['feedback']}。
                学生当前卡在知识点：【{state['current_topic']}】。
                {knowledge_prompt}
                请针对该错因，结合上述专业知识（如果有），换一个完全不同、更具直观性的生活比喻，重新开导他。字数控制在400字左右。
                """
        else:
            human_content = f"""
                {long_term_context}
                请为学生详细讲解【{state['current_topic']}】的核心原理。
                {knowledge_prompt}
                要求逻辑严密，专业术语准确，并给出一个具体的实际应用场景。字数控制在400字左右。
                """
        
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

        event_sink.emit(
            make_event(
                "node.complete",
                "tutor",
                message="Tutor node completed.",
                data={"content_length": len(full_response)},
            )
        )
        return {"tutor_content": full_response}

    return tutor_node