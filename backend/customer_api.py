"""
customer_api.py — dummy FastAPI server that acts as the "Bosch customer API".
Run with:  uvicorn backend.customer_api:app --port 8000 --reload
"""

import json
import os
from fastapi import FastAPI

app = FastAPI(title="Bosch Customer Ticket API")

# Load the sample JSON data file once at startup
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_api_data.json")

with open(DATA_FILE, "r") as f:
    TICKETS = json.load(f)


@app.get("/")
def root():
    """Health-check endpoint."""
    return {"message": "Bosch Customer API is running", "total_tickets": len(TICKETS)}


@app.get("/tickets")
def get_tickets():
    """Return all dummy tickets as JSON — this is what api_ingestor.py fetches."""
    return {"source": "api", "tickets": TICKETS}


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Return a single ticket by its ticket_id, or 404 if not found."""
    for ticket in TICKETS:
        if ticket["ticket_id"] == ticket_id:
            return ticket
    return {"error": f"Ticket {ticket_id} not found"}
