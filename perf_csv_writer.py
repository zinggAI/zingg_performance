import csv
import os
from datetime import datetime


def write_perf_csv(data, csv_path):
    """
    Writes a timestamped CSV performance report.

    Expected CSV format:
    date, time, test, <dynamic phase columns>
    """

    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")

    test_name = data.get("testName", "unknown_test")

    results = data.get("results", {})
    if not isinstance(results, dict):
        raise ValueError("'results' must be a dictionary")

    headers = ["date", "time", "test"] + list(results.keys())
    row = [date_str, time_str, test_name] + list(results.values())

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)

    print("CSV written:", csv_path)
