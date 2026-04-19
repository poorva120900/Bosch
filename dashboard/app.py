"""
app.py — Streamlit dashboard for Bosch ticket data.
Reads exclusively from SQLite.

The Refresh Data button at the top:
  1. Runs dummy_customer_csv.py  → drops a fresh Continental CSV into mock_sftp/incoming/
  2. Runs api_ingestor.py        → fetches latest Siemens AG tickets from port 8001
  3. Runs file_ingestor.py       → ingests the fresh Continental CSV
  4. Clears the cache and reruns the dashboard

Run with:
    streamlit run dashboard/app.py
(from the bosch_dashboard/ root directory)
"""

import sys
import subprocess
import sqlite3
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH      = PROJECT_ROOT / "bosch_tickets.db"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bosch Ticket Dashboard",
    page_icon="🔧",
    layout="wide",
)

# ── Header row: title + Refresh button ───────────────────────────────────────
header_col, btn_col = st.columns([6, 1])

with header_col:
    st.title("🔧 Bosch Customer Ticket Dashboard")
    st.caption(
        "Live data · Siemens AG via SAP Ariba API (port 8001) "
        "· Continental via SFTP CSV drop"
    )

with btn_col:
    st.write("")   # vertical alignment spacer
    st.write("")
    refresh_clicked = st.button("🔄 Refresh Data", type="primary", use_container_width=True)

# ── Refresh logic (runs BEFORE data load so the query sees fresh rows) ────────
if refresh_clicked:
    progress = st.empty()

    with st.spinner("Step 1/3 — Generating fresh Continental CSV..."):
        result = subprocess.run(
            [sys.executable, "-m", "backend.dummy_customer_csv"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            st.error(f"CSV generator failed:\n{result.stderr}")
            st.stop()

    with st.spinner("Step 2/3 — Fetching Siemens AG tickets from API..."):
        result = subprocess.run(
            [sys.executable, "-m", "backend.api_ingestor"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            st.error(
                f"API ingestor failed — is dummy_customer_api.py running on port 8001?\n\n"
                f"{result.stderr}"
            )
            st.stop()

    with st.spinner("Step 3/3 — Ingesting Continental CSV..."):
        result = subprocess.run(
            [sys.executable, "-m", "backend.file_ingestor"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            st.error(f"File ingestor failed:\n{result.stderr}")
            st.stop()

    st.cache_data.clear()
    st.success("Data refreshed successfully!")
    st.rerun()

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_data() -> pd.DataFrame:
    """Pull all rows from the tickets table into a DataFrame."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY last_updated DESC", conn)
    conn.close()
    return df


df = load_data()

# ── Empty-state guard ─────────────────────────────────────────────────────────
if df.empty:
    st.warning(
        "No data in the database yet.\n\n"
        "**Quick start:**\n"
        "1. Start the Siemens AG API server: "
        "`uvicorn backend.dummy_customer_api:app --host 127.0.0.1 --port 8001`\n"
        "2. Press **🔄 Refresh Data** above — it will generate a CSV and run both ingestors automatically."
    )
    st.stop()

# ── KPI metrics row ───────────────────────────────────────────────────────────
total        = len(df)
pending      = len(df[df["status"] == "pending"])
completed    = len(df[df["status"] == "completed"])
in_progress  = len(df[df["status"] == "in_progress"])
api_count    = len(df[df["source_method"] == "api"])
nonapi_count = len(df[df["source_method"] == "non_api"])
last_updated = df["last_updated"].max()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Tickets",  total)
col2.metric("Pending",        pending)
col3.metric("In Progress",    in_progress)
col4.metric("Completed",      completed)
col5.metric("Via API",        api_count,    help="Siemens AG · SAP Ariba")
col6.metric("Via File/SFTP",  nonapi_count, help="Continental · CSV drop")

st.markdown(f"**Last record timestamp:** `{last_updated}`")
st.divider()

# ── Charts row ────────────────────────────────────────────────────────────────
chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    st.subheader("Tickets by Source")
    source_counts = df["source_method"].value_counts().reset_index()
    source_counts.columns = ["source_method", "count"]
    # Human-friendly labels
    source_counts["label"] = source_counts["source_method"].map(
        {"api": "API (Siemens AG)", "non_api": "File/SFTP (Continental)"}
    ).fillna(source_counts["source_method"])
    fig1 = px.bar(
        source_counts,
        x="label",
        y="count",
        color="source_method",
        color_discrete_map={"api": "#0072CE", "non_api": "#E5202A"},
        text="count",
        labels={"label": "Source", "count": "Tickets"},
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                       xaxis_title="", yaxis_title="Ticket Count")
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
        labels={"status": "Status", "count": "Tickets"},
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                       xaxis_title="", yaxis_title="Ticket Count")
    st.plotly_chart(fig2, use_container_width=True)

with chart_col3:
    st.subheader("Tickets by Priority")
    priority_counts = df["priority"].value_counts().reset_index()
    priority_counts.columns = ["priority", "count"]
    priority_color = {
        "critical": "#DC3545",
        "high":     "#FD7E14",
        "medium":   "#FFC107",
        "low":      "#28A745",
    }
    fig3 = px.bar(
        priority_counts,
        x="priority",
        y="count",
        color="priority",
        color_discrete_map=priority_color,
        text="count",
        labels={"priority": "Priority", "count": "Tickets"},
        category_orders={"priority": ["critical", "high", "medium", "low"]},
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                       xaxis_title="", yaxis_title="Ticket Count")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Filters sidebar ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

source_options = df["source_method"].unique().tolist()
source_labels  = {"api": "API — Siemens AG", "non_api": "File/SFTP — Continental"}
source_filter  = st.sidebar.multiselect(
    "Source Method",
    options=source_options,
    default=source_options,
    format_func=lambda x: source_labels.get(x, x),
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

# Add a human-readable source label column for clarity
filtered_df = filtered_df.copy()
filtered_df["source_label"] = filtered_df["source_method"].map(
    {"api": "API · Siemens AG", "non_api": "File/SFTP · Continental"}
).fillna(filtered_df["source_method"])

display_cols = [
    "ticket_id", "customer_name", "issue", "status",
    "priority", "region", "source_label", "last_updated",
]

st.dataframe(
    filtered_df[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticket_id":     st.column_config.TextColumn("Ticket ID", width="small"),
        "customer_name": st.column_config.TextColumn("Customer",  width="small"),
        "issue":         st.column_config.TextColumn("Issue",     width="large"),
        "status":        st.column_config.TextColumn("Status",    width="small"),
        "priority":      st.column_config.TextColumn("Priority",  width="small"),
        "region":        st.column_config.TextColumn("Region",    width="small"),
        "source_label":  st.column_config.TextColumn("Source",    width="medium"),
        "last_updated":  st.column_config.TextColumn("Last Updated", width="medium"),
    },
)
