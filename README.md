# Bosch Dashboard Prototype

A local mock dashboard that ingests ticket data via two flows (API and CSV/SFTP),
stores everything in a shared SQLite database, and visualises it with Streamlit.

---

## Folder Structure

```
bosch_dashboard/
├── mock_sftp/
│   ├── incoming/          ← drop CSV files here for Flow 2
│   └── processed/         ← file_ingestor moves CSVs here after ingestion
├── data/
│   ├── sample_api_data.json    ← dummy data served by customer_api.py
│   └── sample_nonapi_data.csv  ← sample CSV to copy into mock_sftp/incoming/
├── backend/
│   ├── __init__.py
│   ├── database.py        ← shared SQLite helpers (init, connect)
│   ├── customer_api.py    ← FastAPI dummy API server
│   ├── api_ingestor.py    ← Flow 1: fetch from API → SQLite
│   └── file_ingestor.py   ← Flow 2: read CSV from mock_sftp/ → SQLite
├── dashboard/
│   └── app.py             ← Streamlit dashboard (reads SQLite only)
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer      | Technology          |
|------------|---------------------|
| API server | FastAPI + Uvicorn   |
| Database   | SQLite (single file)|
| Ingestion  | Python + requests   |
| CSV parse  | pandas              |
| Dashboard  | Streamlit + Plotly  |

---

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

---

## Running the Project

All commands below are run from inside the `bosch_dashboard/` folder.

### Terminal 1 — Start the dummy API server (Flow 1)

```bash
uvicorn backend.customer_api:app --port 8000 --reload
```

Verify it works: open http://127.0.0.1:8000/tickets in your browser.

---

### Terminal 2 — Run Flow 1: API Ingestor

```bash
python -m backend.api_ingestor
```

This fetches tickets from the running FastAPI server and inserts them into
`bosch_tickets.db` with `source_method = 'api'`.

---

### Terminal 2 — Run Flow 2: File (CSV/SFTP) Ingestor

```bash
# First, copy the sample CSV into the incoming folder
cp data/sample_nonapi_data.csv mock_sftp/incoming/

# Then run the ingestor
python -m backend.file_ingestor
```

This reads every CSV in `mock_sftp/incoming/`, inserts rows with
`source_method = 'non_api'`, and moves processed files to `mock_sftp/processed/`.

---

### Terminal 3 — Start the Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501 automatically.

---

## Database Schema

Table: **tickets**

| Column        | Type    | Notes                          |
|---------------|---------|--------------------------------|
| id            | INTEGER | Auto-increment primary key     |
| ticket_id     | TEXT    | e.g. TKT-001                  |
| customer_name | TEXT    |                                |
| issue         | TEXT    | Description of the problem     |
| status        | TEXT    | pending / in_progress / completed |
| priority      | TEXT    | low / medium / high / critical |
| region        | TEXT    | North America / Europe / Asia  |
| source_method | TEXT    | **api** or **non_api**         |
| last_updated  | TEXT    | ISO-8601 UTC timestamp         |

---

## Dashboard Features

- **KPI tiles**: Total tickets, Pending, In Progress, Completed, Via API, Via File/SFTP
- **Last Updated** timestamp of the most recent record
- **Bar chart 1**: Ticket count by source method (api vs non_api)
- **Bar chart 2**: Ticket count by status
- **Sidebar filters**: Filter by source method, status, and priority
- **Records table**: Filtered, paginated view of all tickets
- **Refresh button**: Clears the Streamlit cache and reloads from SQLite

---

## Re-running / Resetting

To start fresh without duplicate rows, the `api_ingestor.py` automatically
deletes previous `api` rows before re-inserting. For file ingestion, processed
CSVs are moved to `mock_sftp/processed/` so they won't be read twice.

To reset the entire database:

```bash
python -c "from backend.database import clear_table; clear_table()"
```

---

## GitHub Deployment

This repository now supports two GitHub-based deployment paths:

### 1) Streamlit Cloud live app

Deploy `streamlit_app.py` as the main file. It exposes all three dashboards in one app using Streamlit's multi-page navigation:

- `dashboard/app.py` - Bosch ticket dashboard
- `dashboard/customer_portal.py` - Siemens supplier portal
- `dashboard/continental_portal.py` - Continental supplier portal

### 2) GitHub Pages static landing page

The repo also includes `index.html`, a static landing page that introduces the three dashboards and explains how the live app is structured.

If you use GitHub Pages, publish the repository root so `index.html` becomes the site entry point.
