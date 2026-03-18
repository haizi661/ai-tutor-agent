import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

def create_sqlite_checkpointer(db_path: str):
    # 连接数据库
    conn = sqlite3.connect(db_path, check_same_thread=False)
    
    # 获取游标执行 SQL
    cursor = conn.cursor()
    
    # 1. 创建长期记忆表 (用于存放冷数据的摘要)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            thread_id TEXT,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. 创建知识图谱表 (用于存放知识点的依赖关系)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_graph (
            topic_id TEXT PRIMARY KEY,
            topic_name TEXT,
            prerequisites TEXT,  -- 存储为逗号分隔的字符串，如 "加法,减法"
            content_description TEXT
        )
    ''')
    
    conn.commit()
    
    # 返回 LangGraph 原有的存储器
    memory = SqliteSaver(conn)
    return memory, conn