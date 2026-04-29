"""
continental_portal.py — Continental Supplier Portal (Non-API Flow).

Continental does not have a Bosch API key.  Instead they submit tickets
through this Streamlit form.  On submission the portal writes a row
directly to  mock_sftp/incoming/continental_tickets.csv  — the same file
that file_ingestor.py picks up whenever the Bosch operator presses
"Refresh Data" on the main dashboard.

No backend endpoint is called; all I/O is pure Python / pandas.

Run with:
    streamlit run dashboard/continental_portal.py --server.port 8503
"""

import random
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
# Resolve from this file's location so the path is correct regardless of
# which directory the operator launches Streamlit from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH     = PROJECT_ROOT / "mock_sftp" / "incoming" / "continental_tickets.csv"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Continental — Supplier Portal",
    page_icon="🚗",
    layout="centered",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Continental — Supplier Portal")
st.subheader("Bosch Procurement Integration — Secure File Exchange")

# ── How-it-works info box ─────────────────────────────────────────────────────
st.info(
    "You do not need an API key. Simply fill in your ticket details below and "
    "click Submit. Your ticket will be packaged as a secure file and dropped "
    "into the Bosch SFTP folder automatically. Bosch will pick it up on their "
    "next refresh."
)

# ── Ticket submission form ─────────────────────────────────────────────────────
st.subheader("Raise a New Ticket")

with st.form("continental_ticket_form", clear_on_submit=True):

    subject = st.text_input("Ticket Subject")

    category = st.selectbox(
        "Category",
        options=[
            "Part Shortage",
            "Delivery Delay",
            "Invoice Mismatch",
            "Quality Complaint",
            "Logistics Query",
            "Stock Discrepancy",
        ],
    )

    priority = st.selectbox(
        "Priority",
        options=["High", "Medium", "Low"],
    )

    description = st.text_area("Description")

    submitted = st.form_submit_button("Submit Ticket")

# ── Submission handler (runs outside the form block so st.success renders) ────
if submitted:
    if not subject.strip():
        st.error("Ticket Subject cannot be empty. Please enter a subject and resubmit.")
    else:
        # Generate a random 4-digit ticket ID
        ticket_id = f"TKT-{random.randint(1000, 9999)}"

        # Combine category + subject so context is preserved in the CSV
        full_subject = f"[{category}] {subject.strip()}"

        # Build the single-row DataFrame.
        # Column names deliberately use "customer" and "subject" — file_ingestor.py
        # carries COLUMN_ALIASES that map these to the DB schema automatically.
        new_row = pd.DataFrame([{
            "ticket_id":     ticket_id,
            "customer":      "Continental",
            "subject":       full_subject,
            "status":        "open",
            "priority":      priority.lower(),
            "source_method": "non_api",
            "last_updated":  datetime.now(timezone.utc).isoformat(),
        }])

        # Append to existing CSV — or create it fresh if this is the first ticket
        if CSV_PATH.exists():
            existing_df = pd.read_csv(CSV_PATH)
            updated_df  = pd.concat([existing_df, new_row], ignore_index=True)
        else:
            # Ensure the directory exists (mock_sftp/incoming/ should already
            # exist, but this guards against a clean-checkout scenario)
            CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
            updated_df = new_row

        updated_df.to_csv(CSV_PATH, index=False)

        st.success(
            f"**Ticket {ticket_id} submitted.** Your ticket has been securely "
            "dropped into the Bosch SFTP folder. It will appear on the Bosch "
            "dashboard after the next refresh."
        )

st.divider()

# ── Previously submitted tickets ──────────────────────────────────────────────
st.subheader("Previously Submitted Tickets")

if CSV_PATH.exists():
    history_df = pd.read_csv(CSV_PATH)

    if history_df.empty:
        st.info("No tickets submitted yet.")
    else:
        # Select and rename only the columns the user asked for
        display_df = (
            history_df
            .rename(columns={
                "ticket_id":    "Ticket ID",
                "subject":      "Subject",
                "priority":     "Priority",
                "status":       "Status",
                "last_updated": "Submitted At",
            })
            [["Ticket ID", "Subject", "Priority", "Status", "Submitted At"]]
            .reset_index(drop=True)
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No tickets submitted yet.")
