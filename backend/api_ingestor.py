"""
api_ingestor.py — Flow 1 (API).
Fetches ticket data from the Siemens AG dummy API server (port 8001) and
stores the results in SQLite. Old API records are cleared first so there
are never duplicates.

Run with:
    python -m backend.api_ingestor
"""

import requests
from datetime import datetime, timezone
from backend.database import get_connection, init_db

# URL of the Siemens AG SAP Ariba simulator started by dummy_customer_api.py
API_URL = "http://127.0.0.1:8000/tickets"


def fetch_tickets_from_api():
    """Call the dummy API and return the list of ticket dicts."""
    print(f"[API Ingestor] Fetching data from {API_URL} ...")
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    # Handle both a plain list and a {"tickets": [...]} envelope defensively
    if isinstance(data, list):
        tickets = data
    else:
        tickets = data.get("tickets", [])

    print(f"[API Ingestor] Received {len(tickets)} tickets from API.")
    return tickets


def insert_tickets(tickets):
    """
    Insert a list of ticket dicts into the SQLite database.
    Accepts either field names from the dummy API (customer/subject) or the
    DB schema names (customer_name/issue) so both formats work transparently.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    rows_inserted = 0
    for t in tickets:
        # Map API field names → DB column names
        customer_name = t.get("customer") or t.get("customer_name", "")
        issue         = t.get("subject")  or t.get("issue", "")

        cursor.execute("""
            INSERT INTO tickets
                (ticket_id, customer_name, issue, status, priority, region, source_method, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t.get("ticket_id"),
            customer_name,
            issue,
            t.get("status"),
            t.get("priority"),
            t.get("region", "Unknown"),
            "api",
            t.get("last_updated", now),
        ))
        rows_inserted += 1

    conn.commit()
    conn.close()
    print(f"[API Ingestor] Inserted {rows_inserted} rows with source_method='api'.")


def run():
    """Main entry point: initialise DB, clear stale API rows, fetch and insert."""
    init_db()

    # Clear previous API records so re-runs never produce duplicates
    conn = get_connection()
    conn.execute("DELETE FROM tickets WHERE source_method = 'api'")
    conn.commit()
    conn.close()
    print("[API Ingestor] Cleared old API rows.")

    tickets = fetch_tickets_from_api()
    insert_tickets(tickets)
    print("[API Ingestor] Done.")


if __name__ == "__main__":
    run()
