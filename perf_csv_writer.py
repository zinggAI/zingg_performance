import csv
import os
from datetime import datetime


def write_perf_csv(data, csv_path):
    """
    Writes a timestamped CSV performance report.

    - Compatible with perfTestRunner.py
    - Generic: supports any number of phases dynamically
    - Does NOT overwrite previous reports
    """

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")

    # Extract test name safely
    test_name = data.get("testName", "unknown_test")

    # Extract performance results safely
    # If JSON has a 'results' block, use it; otherwise flatten top-level
    results = data.get("results", {})

    if not isinstance(results, dict):
        raise ValueError("'results' must be a dictionary in input JSON")

    # Base headers
    headers = ["date", "time", "test"]

    # Dynamic phase headers
    phase_names = sorted(results.keys())
    headers.extend(phase_names)

    # CSV row
    row = [date_str, time_str, test_name]
    for phase in phase_names:
        row.append(results.get(phase))

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerow(row)

    print("CSV written successfully:", csv_path)
