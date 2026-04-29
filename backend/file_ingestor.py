"""
file_ingestor.py — Flow 2 (Non-API / SFTP).
Reads mock_sftp/incoming/continental_tickets.csv (written by
continental_portal.py when Continental submits a ticket) and stores
the rows into SQLite. Old non_api records are cleared first so there
are never duplicates.

The CSV file is NOT moved after ingestion — it accumulates rows as
Continental submits new tickets through their portal.

Run with:
    python -m backend.file_ingestor
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from backend.database import get_connection, init_db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH     = PROJECT_ROOT / "mock_sftp" / "incoming" / "continental_tickets.csv"

# Column name aliases — allow CSVs that use API-style field names
COLUMN_ALIASES = {
    "customer": "customer_name",
    "subject":  "issue",
}

REQUIRED_COLS = {"ticket_id", "customer_name", "issue", "status", "priority"}


def ingest_csv(csv_path: Path) -> int:
    """Read the CSV and insert its rows into SQLite. Returns the row count."""
    print(f"[File Ingestor] Reading: {csv_path}")
    df = pd.read_csv(csv_path)

    # Normalise column names: lower-case, spaces → underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Apply aliases so both 'customer'/'customer_name' and 'subject'/'issue' work
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        print(f"[File Ingestor] Skipping — missing columns: {missing}")
        return 0

    # Provide defaults for optional columns
    if "region"      not in df.columns:
        df["region"] = "Unknown"
    if "source_method" not in df.columns:
        df["source_method"] = "non_api"
    if "last_updated" not in df.columns:
        df["last_updated"] = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    rows_inserted = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO tickets
                (ticket_id, customer_name, issue, status, priority, region, source_method, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["ticket_id"],
            row["customer_name"],
            row["issue"],
            row["status"],
            row["priority"],
            row.get("region", "Unknown"),
            "non_api",
            row.get("last_updated", datetime.now(timezone.utc).isoformat()),
        ))
        rows_inserted += 1

    conn.commit()
    conn.close()
    print(f"[File Ingestor] Inserted {rows_inserted} rows from {csv_path.name}.")
    return rows_inserted


def run():
    """Main entry point: initialise DB, clear stale non_api rows, ingest CSV."""
    init_db()

    if not CSV_PATH.exists():
        print(
            f"[File Ingestor] No CSV found at {CSV_PATH}.\n"
            "Run dummy_customer_csv.py first to generate the file."
        )
        return

    # Clear previous non_api records so re-runs never produce duplicates
    conn = get_connection()
    conn.execute("DELETE FROM tickets WHERE source_method = 'non_api'")
    conn.commit()
    conn.close()
    print("[File Ingestor] Cleared old non_api rows.")

    ingest_csv(CSV_PATH)
    print("[File Ingestor] Done.")


if __name__ == "__main__":
    run()
