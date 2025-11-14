import sqlite3
import os

DB_PATH = "chat_history.db"

def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # User message history
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Conversation summaries
    cur.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_message(user_id, role, message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )

    conn.commit()
    conn.close()


def get_user_messages(user_id, limit=50):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT role, message 
        FROM messages 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT ?
    """, (user_id, limit))

    rows = cur.fetchall()
    conn.close()
    return rows


def save_summary(user_id, summary):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO summaries (user_id, summary) VALUES (?, ?)",
        (user_id, summary)
    )

    conn.commit()
    conn.close()


def get_last_summary(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT summary FROM summaries 
        WHERE user_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (user_id,))

    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
