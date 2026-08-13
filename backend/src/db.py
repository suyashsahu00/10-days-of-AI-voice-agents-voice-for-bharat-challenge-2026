import os
import sqlite3
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "sydney_memory.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            last_topic TEXT,
            facts TEXT,
            opted_out INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            ref_id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            reason TEXT,
            summary TEXT,
            language TEXT,
            follow_up TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            room_name TEXT,
            outcome TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(callers)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    columns_to_add = {
        "name": "TEXT",
        "last_topic": "TEXT",
        "facts": "TEXT",
        "opted_out": "INTEGER DEFAULT 0",
        "updated_at": "TIMESTAMP",
    }
    for col, col_type in columns_to_add.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE callers ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()


def get_caller(user_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, name, last_topic, facts, opted_out FROM callers WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_caller(
    user_id: str,
    name: Optional[str] = None,
    last_topic: Optional[str] = None,
    facts: Optional[str] = None,
    opted_out: bool = False,
):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    existing = get_caller(user_id)
    if existing:
        name = name if name is not None else existing.get("name")
        last_topic = (
            last_topic if last_topic is not None else existing.get("last_topic")
        )
        facts = facts if facts is not None else existing.get("facts")
        opted_out_int = 1 if opted_out else existing.get("opted_out", 0)
        cursor.execute(
            """UPDATE callers
               SET name=?, last_topic=?, facts=?, opted_out=?, updated_at=CURRENT_TIMESTAMP
               WHERE user_id=?""",
            (name, last_topic, facts, opted_out_int, user_id),
        )
    else:
        cursor.execute(
            """INSERT INTO callers (user_id, name, last_topic, facts, opted_out)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, name, last_topic, facts, 1 if opted_out else 0),
        )
    conn.commit()
    conn.close()


def save_escalation(
    ref_id: str,
    user_id: str,
    name: str,
    reason: str,
    summary: str,
    language: str,
    follow_up: str,
):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO escalations
           (ref_id, user_id, name, reason, summary, language, follow_up, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'open')""",
        (ref_id, user_id, name, reason, summary, language, follow_up),
    )
    conn.commit()
    conn.close()


def get_escalations():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM escalations ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_call(user_id: str, room_name: str, outcome: str):
    """outcome: 'success' or 'failed'"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO calls (user_id, room_name, outcome, ended_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
        (user_id, room_name, outcome),
    )
    conn.commit()
    conn.close()


def get_call_stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM calls")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM calls WHERE outcome='success'")
    successful = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM calls WHERE outcome='failed'")
    failed = cursor.fetchone()[0]
    cursor.execute(
        """SELECT user_id, room_name, outcome, ended_at
           FROM calls ORDER BY ended_at DESC LIMIT 10"""
    )
    recent = [
        {"user_id": r[0], "room_name": r[1], "outcome": r[2], "ended_at": r[3]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "recent": recent,
    }


def reset_calls():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM calls")
    conn.commit()
    conn.close()
