import csv
import os
from datetime import datetime


def write_perf_csv(
    csv_path: str,
    test_name: str,
    duration_sec: float,
    exit_code: int,
    timestamp: str | None = None,
):
    """
    Write a single-run performance CSV.

    Guaranteed schema (DO NOT CHANGE):
    date,time,test_name,duration_sec,exit_code

    This format is required by:
    - generate_plots.py
    - GitHub Actions automation
    """

    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Timestamp handling
    if timestamp:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
    else:
        dt = datetime.now()

    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M:%S")

    headers = [
        "date",
        "time",
        "test_name",
        "duration_sec",
        "exit_code",
    ]

    row = [
        date_str,
        time_str,
        test_name,
        round(float(duration_sec), 2),
        int(exit_code),
    ]

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)

    print(f"[perf_csv_writer] CSV written: {csv_path}")
