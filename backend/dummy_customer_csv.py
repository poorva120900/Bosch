"""
dummy_customer_csv.py — Simulates Continental dropping a fresh export from
their internal ticketing system into a shared SFTP folder.

Each run overwrites mock_sftp/incoming/nonapi_customer_data.csv with a new
batch of randomly generated tickets so the file feels live.

Run with:
    python -m backend.dummy_customer_csv
"""

import csv
import random
from datetime import datetime, timezone
from pathlib import Path

# ── Randomisation pools ───────────────────────────────────────────────────────

SUBJECTS = [
    "Tyre pressure monitoring sensor fault",
    "Lane departure warning camera calibration required",
    "Adaptive cruise control radar misalignment",
    "Park assist ultrasonic sensor failure — rear cluster",
    "Rear-view camera image distortion at low temperature",
    "Blind spot monitor radar intermittent fault",
    "Automatic emergency braking false activation",
    "Electronic stability control warning light on",
    "Air suspension compressor fault code C1234",
    "Door control module unresponsive on driver side",
    "HVAC actuator stuck in defrost position",
    "Seatbelt pre-tensioner pyrotechnic fault",
    "Instrument cluster display backlight failure",
    "USB hub communication timeout in infotainment",
    "OBD-II port data stream interrupted during upload",
    "Heated steering wheel relay failure",
    "Rain sensor calibration lost after windscreen replacement",
    "Navigation map update fails with error 0x8004",
    "Wireless charging pad overheating alert",
    "Start/Stop system disabled — battery voltage low",
]

STATUSES = ["pending", "in_progress", "completed"]
PRIORITIES = ["low", "medium", "high", "critical"]
REGIONS = ["Europe", "North America", "Asia"]

STATUS_WEIGHTS   = [0.40, 0.35, 0.25]
PRIORITY_WEIGHTS = [0.15, 0.35, 0.35, 0.15]

# Output file — same location every run so the ingestor always knows where to look
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH  = PROJECT_ROOT / "mock_sftp" / "incoming" / "nonapi_customer_data.csv"

FIELDNAMES = [
    "ticket_id", "customer_name", "issue", "status",
    "priority", "region", "source_method", "last_updated",
]


# ── Generator ─────────────────────────────────────────────────────────────────

def generate_csv() -> Path:
    """Write a fresh CSV to mock_sftp/incoming/ and return the path."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    n = random.randint(6, 12)
    subject_pool = SUBJECTS.copy()
    random.shuffle(subject_pool)

    rows = []
    for i in range(1, n + 1):
        rows.append({
            "ticket_id":     f"CON-{2000 + i:04d}",
            "customer_name": "Continental",
            "issue":         subject_pool[i % len(subject_pool)],
            "status":        random.choices(STATUSES,   weights=STATUS_WEIGHTS)[0],
            "priority":      random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0],
            "region":        random.choice(REGIONS),
            "source_method": "non_api",
            "last_updated":  datetime.now(timezone.utc).isoformat(),
        })

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[CSV Generator] Generated {n} Continental tickets → {OUTPUT_PATH}")
    return OUTPUT_PATH


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    generate_csv()
