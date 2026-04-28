"""
customer_api.py — Bosch Customer Ticket API.
Serves historical dummy tickets AND accepts live Siemens AG ticket submissions.

Run with (from the bosch_dashboard/ root directory):
    uvicorn backend.customer_api:app --port 8000 --reload
"""

import json
import os
import random
import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Bosch Customer Ticket API")

# ── Historical dummy data loaded once at startup ──────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_api_data.json")

with open(DATA_FILE, "r") as f:
    TICKETS = json.load(f)

# ── Shared database path ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "bosch_tickets.db")

# ── Auth constant ─────────────────────────────────────────────────────────────
MOCK_API_KEY = "BOSCH-MOCK-KEY-2024"


# ── Request body schema ───────────────────────────────────────────────────────
class TicketSubmission(BaseModel):
    subject: str
    category: str
    priority: str
    description: str = ""


# ── Existing endpoints (unchanged) ────────────────────────────────────────────

@app.get("/")
def root():
    """Health-check endpoint."""
    return {"message": "Bosch Customer API is running", "total_tickets": len(TICKETS)}


@app.get("/tickets")
def get_tickets():
    """Return all historical dummy tickets — used by api_ingestor.py."""
    return {"source": "api", "tickets": TICKETS}


# ── New endpoint: GET /tickets/siemens ────────────────────────────────────────
# IMPORTANT: this specific route must be declared BEFORE /tickets/{ticket_id}
# so FastAPI does not absorb "siemens" as a path parameter.

@app.get("/tickets/siemens")
def get_siemens_tickets():
    """Return all tickets raised by Siemens AG, ordered newest first."""
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT ticket_id,
               issue        AS subject,
               status,
               priority,
               last_updated AS submitted_at
        FROM   tickets
        WHERE  customer_name = 'Siemens AG'
        ORDER  BY last_updated DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Existing parametric endpoint (must stay AFTER /tickets/siemens) ───────────

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Return a single historical ticket by its ticket_id, or 404 if not found."""
    for ticket in TICKETS:
        if ticket["ticket_id"] == ticket_id:
            return ticket
    return {"error": f"Ticket {ticket_id} not found"}


# ── New endpoint: POST /submit-ticket ─────────────────────────────────────────

@app.post("/submit-ticket")
def submit_ticket(
    payload: TicketSubmission,
    x_api_key: str = Header(default=None, alias="x-api-key"),
):
    """
    Accept a ticket from a Siemens AG portal submission.
    Validates the API key, generates a TKT-XXXX ID, and writes to bosch_tickets.db.
    """
    if x_api_key != MOCK_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

    ticket_id = f"TKT-{random.randint(1000, 9999)}"
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO tickets
            (ticket_id, customer_name, issue, status, priority, region, source_method, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            "Siemens AG",
            payload.subject,
            "open",
            payload.priority,
            "Unknown",
            "api",
            now,
        ),
    )
    conn.commit()
    conn.close()

    return {"success": True, "ticket_id": ticket_id}
