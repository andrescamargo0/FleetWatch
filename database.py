"""
database.py

Saves teacher assignments in a small SQLite database (data/fleetwatch.db).

Why a database? Every new export CSV replaces the old one, so if you fixed a
laptop's teacher by editing the CSV, the fix would disappear with the next upload.
Assignments saved here are kept, and the app applies them on top of every export.

SQLite is a whole database stored in one file
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "fleetwatch.db"

def connect():
    """Open a connection to the database file"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Create the assignments table the first time the app runs."""
    DB_PATH.parent.mkdir(exist_ok=True)
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                serial_number TEXT PRIMARY KEY,
                teacher       TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            )
        """)

def get_assignments():
    """Return every saved assignment as a dictionary: {serial_number: teacher}."""
    with connect() as conn:
        rows = conn.execute("SELECT serial_number, teacher FROM assignments").fetchall()
    return dict(rows)

def set_assignment(serial_number, teacher):
    """Save one laptop's teacher. An empty teacher means "unassigned on purpose"."""
    with connect() as conn:
        # "Upsert": insert a new row, or if this serial already has one, update it instead.
        conn.execute("""
            INSERT INTO assignments (serial_number, teacher, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(serial_number) DO UPDATE SET
                teacher = excluded.teacher,
                updated_at = excluded.updated_at
        """, (serial_number, teacher))

if __name__ == "__main__":
    init_db()
    saved = get_assignments()
    print(f"{len(saved)} saved assignments")
    for serial, teacher in saved.items():
        print(f"  {serial}: {teacher or '(unassigned)'}")