import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


def create_sqlite_checkpointer(db_path: str):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    return memory, conn
