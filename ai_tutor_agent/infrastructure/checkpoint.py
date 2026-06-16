import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


def create_sqlite_checkpointer(db_path: str):
    """创建 SQLite checkpointer，同时初始化长期记忆和知识图谱表。

    来自 origin/3.11yang 的改进：LangGraph checkpoint 之外额外维护
    long_term_memory（冷数据摘要）和 knowledge_graph（知识点依赖）两张表。
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # 1. 长期记忆表（存放冷数据的摘要）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            thread_id TEXT,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. 知识图谱表（存放知识点的依赖关系）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_graph (
            topic_id TEXT PRIMARY KEY,
            topic_name TEXT,
            prerequisites TEXT,
            content_description TEXT
        )
    """)

    conn.commit()

    memory = SqliteSaver(conn)
    return memory, conn
