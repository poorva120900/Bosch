"""
customer_portal.py — Siemens AG Supplier Portal.
A customer-facing Streamlit app for raising support tickets with Bosch.

Run with (from the bosch_dashboard/ root directory):
    streamlit run dashboard/customer_portal.py --server.port 8502
"""

import pandas as pd
import requests
import streamlit as st

# ── Constants ─────────────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"
API_KEY  = "BOSCH-MOCK-KEY-2024"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Siemens AG — Supplier Portal",
    page_icon="🏭",
    layout="centered",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Siemens AG — Supplier Portal")
st.subheader("Bosch Procurement Integration")
st.divider()

# ── API Key display (light grey info box, read-only) ──────────────────────────
st.markdown(
    """
    <div style="
        background-color:#f0f2f6;
        padding:16px 20px;
        border-radius:8px;
        margin-bottom:4px;
        border:1px solid #dde1ea;
    ">
        <p style="margin:0 0 4px 0;font-size:0.8em;color:#555;font-weight:600;
                  letter-spacing:0.05em;text-transform:uppercase;">Your API Key</p>
        <p style="margin:0;font-size:1.05em;font-family:monospace;
                  color:#1a1a2e;font-weight:700;letter-spacing:0.04em;">
            BOSCH-MOCK-KEY-2024
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("This key authenticates your tickets with Bosch systems")
st.divider()

# ── Ticket submission form ────────────────────────────────────────────────────
st.subheader("Raise a New Ticket")

with st.form("ticket_form", clear_on_submit=True):
    subject = st.text_input(
        "Ticket Subject",
        placeholder="e.g. Missing parts for order #4421",
    )

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

    description = st.text_area(
        "Description",
        placeholder="Please describe the issue in detail...",
        height=120,
    )

    submitted = st.form_submit_button(
        "Submit Ticket",
        type="primary",
        use_container_width=True,
    )

# ── Handle form submission (outside the with block so st.success renders) ─────
if submitted:
    if not subject.strip():
        st.error("Ticket Subject is required.")
    else:
        payload = {
            "subject":     subject.strip(),
            "category":    category,
            "priority":    priority,
            "description": description.strip(),
        }
        try:
            response = requests.post(
                f"{API_BASE}/submit-ticket",
                json=payload,
                headers={"x-api-key": API_KEY},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                st.success(
                    "Ticket submitted successfully. "
                    "Bosch will pick this up on next refresh.\n\n"
                    f"**Ticket ID:** `{data.get('ticket_id', 'N/A')}`"
                )
            elif response.status_code == 401:
                st.error("Authentication failed — invalid API key.")
            else:
                st.error(
                    f"Submission failed (HTTP {response.status_code}): {response.text}"
                )
        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to the Bosch API server. "
                "Make sure it is running on port 8000."
            )
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")

st.divider()

# ── Previously submitted tickets ──────────────────────────────────────────────
st.subheader("Previously Submitted Tickets")

try:
    resp = requests.get(f"{API_BASE}/tickets/siemens", timeout=10)
    if resp.status_code == 200:
        tickets = resp.json()
        if tickets:
            df = pd.DataFrame(tickets)
            # Map API field names to the required display column headers
            df = df.rename(columns={
                "ticket_id":    "Ticket ID",
                "subject":      "Subject",
                "status":       "Status",
                "priority":     "Priority",
                "submitted_at": "Submitted At",
            })
            st.dataframe(
                df[["Ticket ID", "Subject", "Status", "Priority", "Submitted At"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ticket ID":    st.column_config.TextColumn("Ticket ID",    width="small"),
                    "Subject":      st.column_config.TextColumn("Subject",      width="large"),
                    "Status":       st.column_config.TextColumn("Status",       width="small"),
                    "Priority":     st.column_config.TextColumn("Priority",     width="small"),
                    "Submitted At": st.column_config.TextColumn("Submitted At", width="medium"),
                },
            )
        else:
            st.info(
                "No tickets submitted yet. "
                "Use the form above to raise your first ticket."
            )
    else:
        st.warning(f"Could not fetch tickets (HTTP {resp.status_code}).")
except requests.exceptions.ConnectionError:
    st.warning(
        "Cannot connect to the Bosch API server. "
        "Make sure it is running on port 8000."
    )
except Exception as exc:
    st.warning(f"Error fetching tickets: {exc}")
