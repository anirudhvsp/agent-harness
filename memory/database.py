import sqlite3
import json
from config import settings

def get_db():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT,
        tool_calls TEXT,
        tool_call_id TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permanent_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def get_messages(session_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id", (session_id,))
    messages = []
    for row in cursor.fetchall():
        msg = {"role": row["role"], "content": row["content"] or ""}
        
        # Handle tool_calls
        raw_tool_calls = row["tool_calls"]
        if raw_tool_calls:
            try:
                # Check if it's a string that needs loading
                if isinstance(raw_tool_calls, str):
                    tool_calls = json.loads(raw_tool_calls)
                else:
                    tool_calls = raw_tool_calls
                
                # Ensure tool_calls is a list of dictionaries
                if isinstance(tool_calls, list) and all(isinstance(tc, dict) for tc in tool_calls):
                    msg["tool_calls"] = tool_calls
                else:
                    # Fallback for malformed data
                    msg["content"] = msg["content"] + f"\n(Malformed tool_calls data: {raw_tool_calls})"

            except json.JSONDecodeError:
                msg["content"] = msg["content"] + f"\n(Invalid JSON in tool_calls: {raw_tool_calls})"


        if row["tool_call_id"]:
            msg["tool_call_id"] = row["tool_call_id"]
        
        messages.append(msg)
    conn.close()
    return messages

def add_message(session_id: str, message: dict):
    conn = get_db()
    cursor = conn.cursor()

    # Ensure content is not None
    content = message.get("content")
    if content is None:
        content = ""

    tool_calls = message.get("tool_calls")
    if tool_calls and not isinstance(tool_calls, str):
        tool_calls_str = json.dumps(tool_calls)
    else:
        tool_calls_str = tool_calls

    cursor.execute(
        """
        INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            message.get("role"),
            content,
            tool_calls_str,
            message.get("tool_call_id"),
        ),
    )
    conn.commit()
    conn.close()

def clear_messages(session_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def add_fact(fact: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO permanent_memory (fact) VALUES (?)", (fact,))
    conn.commit()
    conn.close()

def get_facts() -> list[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT fact FROM permanent_memory ORDER BY id")
    facts = [row["fact"] for row in cursor.fetchall()]
    conn.close()
    return facts