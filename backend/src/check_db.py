import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sydney_memory.db"


def check_database():
    if not DB_PATH.exists():
        print(
            "Database file does not exist yet. Start a conversation with Sydney first!"
        )
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM callers").fetchall()

    if not rows:
        print("No caller records found in sydney_memory.db yet.")
        return

    print(f"\n--- Stored Callers in SQLite ({len(rows)} record(s)) ---\n")
    for row in rows:
        print(f"User ID:            {row['user_id']}")
        print(f"Name:               {row['name']}")
        print(f"Language Pref:      {row['language_preference']}")
        print(f"Last Interaction:   {row['last_interaction']}")
        print("Facts:")
        try:
            facts_obj = json.loads(row["facts"]) if row["facts"] else {}
            print(json.dumps(facts_obj, indent=2))
        except Exception:
            print(f"  {row['facts']}")
        print("-" * 50)


if __name__ == "__main__":
    check_database()
