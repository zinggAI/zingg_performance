import csv
import os
from datetime import datetime


def write_perf_csv(test_name: str, metrics: dict, csv_path: str):
    """
    Writes a single-row CSV containing performance metrics.

    Parameters
    ----------
    test_name : str
        Name of the test (e.g. febrl_120K)

    metrics : dict
        Dictionary of numeric test results extracted from testReport JSON
        Example:
        {
            "total_records": 120000,
            "matched_records": 98234,
            "precision": 0.91,
            "recall": 0.88,
            "f1_score": 0.895,
            "duration_sec": 183.42
        }

    csv_path : str
        Absolute path where CSV should be written
    """

    # ----------------------------------------------------
    # 1. Validate inputs
    # ----------------------------------------------------

    if not isinstance(metrics, dict):
        raise ValueError("metrics must be a dictionary")

    if not metrics:
        raise ValueError("metrics dictionary is empty")

    # Ensure all metric values are numeric (important for plots)
    for key, value in metrics.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"Metric '{key}' is not numeric: {value}")

    # ----------------------------------------------------
    # 2. Ensure output directory exists
    # ----------------------------------------------------

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # ----------------------------------------------------
    # 3. Timestamp columns (human readable)
    # ----------------------------------------------------

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # ----------------------------------------------------
    # 4. Prepare CSV structure
    # ----------------------------------------------------

    headers = ["date", "time", "test"] + list(metrics.keys())
    row = [date_str, time_str, test_name] + list(metrics.values())

    # ----------------------------------------------------
    # 5. Write CSV (overwrite-safe due to timestamped filename)
    # ----------------------------------------------------

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerow(row)

    print("✅ Performance CSV written successfully:")
    print(csv_path)
