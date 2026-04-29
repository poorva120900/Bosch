"""
app.py — Streamlit dashboard for Bosch ticket data.
Reads exclusively from SQLite. Refreshes on every page interaction.
Run with:  streamlit run dashboard/app.py
"""

import sys
import sqlite3
import os
import pandas as pd
import plotly.express as px
import streamlit as st

# Make sure the project root (bosch_dashboard/) is on sys.path so the
# backend package is importable even when Streamlit is launched from a
# different working directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.api_ingestor import run as run_api_ingestor    # Flow 1: API → SQLite
from backend.file_ingestor import run as run_file_ingestor  # Flow 2: CSV/SFTP → SQLite

# ── Path to the shared database ──────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "bosch_tickets.db")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bosch Ticket Dashboard",
    page_icon="🔧",
    layout="wide",
)

st.title("🔧 Bosch Customer Ticket Dashboard")
st.caption("Data source: SQLite  |  Flows: API + Non-API (CSV/SFTP)")


# ── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)  # re-query every 10 seconds so new ingestions show up
def load_data():
    """Sync the SFTP CSV into SQLite, then pull all rows into a DataFrame.
    Running the file ingestor here means every cache cycle (10 s) automatically
    picks up new Continental tickets — no Refresh button required."""
    # Always sync the SFTP file first so SQLite is up to date
    try:
        run_file_ingestor()
    except Exception:
        pass  # missing CSV is fine — ingestor prints a message and returns

    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY last_updated DESC", conn)
    conn.close()
    return df


df = load_data()

# ── Empty-state guard ─────────────────────────────────────────────────────────
if df.empty:
    st.warning(
        "No data found in the database yet.\n\n"
        "Run the ingestors first:\n"
        "- **Flow 1 (API):** start `customer_api.py` then run `api_ingestor.py`\n"
        "- **Flow 2 (CSV):** copy a CSV into `mock_sftp/incoming/` then run `file_ingestor.py`"
    )
    st.stop()

# ── KPI metrics row ───────────────────────────────────────────────────────────
total       = len(df)
pending     = len(df[df["status"] == "pending"])
completed   = len(df[df["status"] == "completed"])
in_progress = len(df[df["status"] == "in_progress"])
api_count   = len(df[df["source_method"] == "api"])
nonapi_count= len(df[df["source_method"] == "non_api"])
last_updated= df["last_updated"].max()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Tickets",   total)
col2.metric("Pending",         pending)
col3.metric("In Progress",     in_progress)
col4.metric("Completed",       completed)
col5.metric("Via API",         api_count)
col6.metric("Via File/SFTP",   nonapi_count)

st.markdown(f"**Last Updated (most recent record):** `{last_updated}`")
st.divider()

# ── Charts row ────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Tickets by Source Method")
    source_counts = df["source_method"].value_counts().reset_index()
    source_counts.columns = ["source_method", "count"]
    fig1 = px.bar(
        source_counts,
        x="source_method",
        y="count",
        color="source_method",
        color_discrete_map={"api": "#0072CE", "non_api": "#E5202A"},  # Bosch-ish colors
        text="count",
        labels={"source_method": "Source", "count": "Ticket Count"},
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    st.subheader("Tickets by Status")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    color_map = {"pending": "#FFA500", "completed": "#28A745", "in_progress": "#007BFF"}
    fig2 = px.bar(
        status_counts,
        x="status",
        y="count",
        color="status",
        color_discrete_map=color_map,
        text="count",
        labels={"status": "Status", "count": "Ticket Count"},
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Filters sidebar ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

source_filter = st.sidebar.multiselect(
    "Source Method",
    options=df["source_method"].unique().tolist(),
    default=df["source_method"].unique().tolist(),
)

status_filter = st.sidebar.multiselect(
    "Status",
    options=df["status"].unique().tolist(),
    default=df["status"].unique().tolist(),
)

priority_filter = st.sidebar.multiselect(
    "Priority",
    options=df["priority"].unique().tolist(),
    default=df["priority"].unique().tolist(),
)

# Apply filters
filtered_df = df[
    df["source_method"].isin(source_filter) &
    df["status"].isin(status_filter) &
    df["priority"].isin(priority_filter)
]

# ── Records table ─────────────────────────────────────────────────────────────
st.subheader(f"All Records ({len(filtered_df)} shown)")

display_cols = ["ticket_id", "customer_name", "issue", "status",
                "priority", "region", "source_method", "last_updated"]

_COL_NAMES = {
    "ticket_id":     "Ticket ID",
    "customer_name": "Customer",
    "issue":         "Issue",
    "status":        "Status",
    "priority":      "Priority",
    "region":        "Region",
    "source_method": "Source",
    "last_updated":  "Last Updated",
}


def _badge_source(col):
    """Return per-cell CSS so 'api' shows green and 'non_api' shows orange."""
    out = []
    for v in col:
        if v == "api":
            out.append("background-color:#c3e6cb; color:#155724; border-radius:4px; font-weight:600;")
        elif v == "non_api":
            out.append("background-color:#fde8bd; color:#856404; border-radius:4px; font-weight:600;")
        else:
            out.append("")
    return out


display_df = filtered_df[display_cols].reset_index(drop=True).rename(columns=_COL_NAMES)

st.dataframe(
    display_df.style.apply(_badge_source, subset=["Source"]),
    use_container_width=True,
    hide_index=True,
)

# ── Manual refresh button ─────────────────────────────────────────────────────
if st.button("Refresh Data"):
    # Pull latest tickets from both sources before re-querying the database.
    # API ingestor is wrapped in try/except so a stopped API server doesn't
    # block the file/SFTP flow from completing.
    with st.spinner("Ingesting latest data from all sources..."):
        try:
            run_api_ingestor()
        except Exception as exc:
            st.warning(f"API ingestor skipped — server may not be running. ({exc})")
        try:
            run_file_ingestor()
        except Exception as exc:
            st.warning(f"File ingestor error: {exc}")
    st.cache_data.clear()
    st.rerun()
