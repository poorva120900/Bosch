"""
file_ingestor.py — Flow 2 (Non-API / SFTP).
Reads every CSV file dropped into mock_sftp/incoming/ and inserts rows into SQLite.
Processed files are moved to mock_sftp/processed/ so they are not ingested twice.
Run with:  python -m backend.file_ingestor
"""

import os
import shutil
import pandas as pd
from datetime import datetime, timezone
from backend.database import get_connection, init_db

# Watch this folder for incoming CSV files
INCOMING_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_sftp", "incoming")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_sftp", "processed")


def ensure_dirs():
    """Make sure both incoming and processed directories exist."""
    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def ingest_csv(filepath):
    """Read a single CSV file and insert its rows into SQLite."""
    print(f"[File Ingestor] Reading file: {filepath}")
    df = pd.read_csv(filepath)

    # Normalise column names to lower-case with underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    required_cols = {"ticket_id", "customer_name", "issue", "status", "priority", "region"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"[File Ingestor] Skipping {filepath} — missing columns: {missing}")
        return 0

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

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
            row["region"],
            "non_api",   # source_method is always 'non_api' for this flow
            now,
        ))
        rows_inserted += 1

    conn.commit()
    conn.close()
    print(f"[File Ingestor] Inserted {rows_inserted} rows from {os.path.basename(filepath)}.")
    return rows_inserted


def move_to_processed(filepath):
    """Move a processed CSV to the processed/ folder to avoid re-ingestion."""
    filename = os.path.basename(filepath)
    dest = os.path.join(PROCESSED_DIR, filename)
    # Append timestamp if a file with the same name already exists in processed/
    if os.path.exists(dest):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(PROCESSED_DIR, f"{ts}_{filename}")
    shutil.move(filepath, dest)
    print(f"[File Ingestor] Moved to processed: {dest}")


def run():
    """Main entry point: initialise DB, scan incoming/, ingest each CSV."""
    init_db()
    ensure_dirs()

    csv_files = [f for f in os.listdir(INCOMING_DIR) if f.lower().endswith(".csv")]

    if not csv_files:
        print(f"[File Ingestor] No CSV files found in {INCOMING_DIR}. Nothing to do.")
        return

    total = 0
    for filename in csv_files:
        filepath = os.path.join(INCOMING_DIR, filename)
        count = ingest_csv(filepath)
        total += count
        move_to_processed(filepath)

    print(f"[File Ingestor] Done. Total rows inserted: {total}")


if __name__ == "__main__":
    run()
