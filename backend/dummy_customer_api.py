"""
dummy_customer_api.py — Simulates Siemens AG's SAP Ariba ticketing system.
Runs as a standalone FastAPI server on http://127.0.0.1:8001/
Each call to /tickets returns a freshly randomised set of tickets so the
dashboard feels live when you press Refresh.

Start with:
    uvicorn backend.dummy_customer_api:app --host 127.0.0.1 --port 8001 --reload
"""

import random
from datetime import datetime, timezone
from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Siemens AG SAP Ariba Simulator",
    description="Dummy REST endpoint that mimics a real customer's ticket API.",
    version="1.0.0",
)

# ── Randomisation pools ───────────────────────────────────────────────────────

SUBJECTS = [
    "ECU firmware update required",
    "Brake sensor calibration failure",
    "Fuel injection timing error",
    "ABS module communication timeout",
    "Transmission control fault code P0700",
    "Battery management system alert",
    "Engine coolant temperature threshold exceeded",
    "Turbocharger pressure sensor drift",
    "Exhaust gas recirculation valve stuck open",
    "Power steering assist intermittent failure",
    "CAN bus error on chassis domain controller",
    "Airbag system diagnostic fault — driver side",
    "ADAS radar alignment lost after vehicle service",
    "Electric motor inverter overheat warning",
    "Cooling system pump cavitation detected",
    "Keyless entry module unresponsive",
    "HMI display flickering at startup",
    "OTA update package checksum mismatch",
    "Ambient light sensor calibration needed",
    "Tyre pressure monitoring system offline",
]

STATUSES = ["pending", "in_progress", "completed"]
PRIORITIES = ["low", "medium", "high", "critical"]
REGIONS = ["Europe", "North America", "Asia"]

# Weighted distributions so the randomisation feels realistic
STATUS_WEIGHTS   = [0.40, 0.35, 0.25]   # more pending than completed
PRIORITY_WEIGHTS = [0.15, 0.35, 0.35, 0.15]  # mostly medium/high


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def root():
    """Health-check — confirms the simulator is running."""
    return {
        "service": "Siemens AG SAP Ariba API Simulator",
        "status": "running",
        "description": "Call GET /tickets to retrieve live dummy ticket data.",
    }


@app.get("/tickets", tags=["tickets"])
def get_tickets():
    """
    Return a randomised list of Siemens AG support tickets.
    Ticket count varies between 8 and 14 on every call to simulate live data.
    """
    n = random.randint(8, 14)
    tickets = []

    # Shuffle the subject pool so the selection order is unpredictable
    subject_pool = SUBJECTS.copy()
    random.shuffle(subject_pool)

    for i in range(1, n + 1):
        ticket = {
            "ticket_id":     f"SIE-{1000 + i:04d}",
            "customer":      "Siemens AG",
            "subject":       subject_pool[i % len(subject_pool)],
            "status":        random.choices(STATUSES,   weights=STATUS_WEIGHTS)[0],
            "priority":      random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0],
            "region":        random.choice(REGIONS),
            "source_method": "api",
            "last_updated":  datetime.now(timezone.utc).isoformat(),
        }
        tickets.append(ticket)

    return tickets


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.dummy_customer_api:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
    )
