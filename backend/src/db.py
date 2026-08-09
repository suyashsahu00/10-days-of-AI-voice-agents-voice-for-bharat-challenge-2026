import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "sydney_memory.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS callers (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                facts TEXT,
                last_interaction TEXT
            )
        """)


def get_caller(user_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM callers WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return None
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": json.loads(row["facts"] or "{}"),
        "last_interaction": row["last_interaction"],
    }


def save_caller(user_id: str, name: str, language_preference: str, new_facts: dict):
    existing = get_caller(user_id)
    merged_facts = {**(existing["facts"] if existing else {}), **new_facts}
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                language_preference=excluded.language_preference,
                facts=excluded.facts,
                last_interaction=excluded.last_interaction
        """,
            (
                user_id,
                name,
                language_preference,
                json.dumps(merged_facts),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
