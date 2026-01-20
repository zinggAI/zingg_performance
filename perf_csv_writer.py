import csv
import os

def json_to_csv(test_data, base_dir="performance_reports/csv"):
    """
    Convert a single performance JSON report to a CSV file.

    Addresses PR requirements:
    1. Generic columns (auto-detected test phases)
    2. Reports per test per year
    3. One CSV per test run (timestamped)
    """

    test_name = test_data["test"]
    date = test_data["date"]          # YYYY-MM-DD
    time = test_data["time"]          # HH:MM:SS
    year = date.split("-")[0]

    # Clean time for filename (HHMMSS)
    clean_time = time.replace(":", "")

    # Directory structure: csv/<test_name>/<year>/
    output_dir = os.path.join(base_dir, test_name, year)
    os.makedirs(output_dir, exist_ok=True)

    # CSV file name: testName_date_time.csv
    csv_file = f"{test_name}_{date}_{clean_time}.csv"
    csv_path = os.path.join(output_dir, csv_file)

    # Base headers
    headers = ["date", "time", "test"]

    # Dynamically add phase names
    phase_columns = list(test_data["results"].keys())
    headers.extend(phase_columns)

    # Build row
    row = {
        "date": date,
        "time": time,
        "test": test_name
    }

    for phase, value in test_data["results"].items():
        row[phase] = value

    # Write CSV (new file every run)
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row)

    print(f"CSV performance report written to {csv_path}")
