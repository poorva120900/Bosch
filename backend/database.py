"""
database.py — creates and manages the shared SQLite database.
Both api_ingestor.py and file_ingestor.py import from here.
"""

import sqlite3
import os

# Database file lives at the project root so all modules can reach it easily
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "bosch_tickets.db")


def get_connection():
    """Return a sqlite3 connection to the shared database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets callers access columns by name
    return conn


def init_db():
    """
    Create the tickets table if it doesn't exist yet.
    Call this once at startup from any ingestor or the dashboard.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id     TEXT NOT NULL,
            customer_name TEXT,
            issue         TEXT,
            status        TEXT,
            priority      TEXT,
            region        TEXT,
            source_method TEXT NOT NULL,   -- 'api' or 'non_api'
            last_updated  TEXT NOT NULL    -- ISO-8601 timestamp
        )
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Database ready at: {os.path.abspath(DB_PATH)}")


def clear_table():
    """Drop all rows — useful for re-running demos without duplicates."""
    conn = get_connection()
    conn.execute("DELETE FROM tickets")
    conn.commit()
    conn.close()
    print("[DB] tickets table cleared.")


if __name__ == "__main__":
    init_db()
