import csv
import os


def write_perf_csv(report_json, csv_path):
    """
    Writes performance CSV from Zingg testReport JSON.

    Expected JSON format:
    {
      "date": "YYYY-MM-DD",
      "time": "HH:MM:SS",
      "test": "<test_name>",
      "results": {
          "train": <number>,
          "match": <number>,
          ...
      }
    }
    """

    # ----------------------------------------------------
    # 1. Validate input JSON
    # ----------------------------------------------------

    if not isinstance(report_json, dict):
        raise ValueError("❌ report_json must be a dictionary")

    date = report_json.get("date")
    time = report_json.get("time")
    test = report_json.get("test")
    results = report_json.get("results")

    if not date or not time or not test:
        raise ValueError("❌ 'date', 'time', or 'test' missing in testReport JSON")

    if not isinstance(results, dict) or not results:
        raise ValueError("❌ 'results' field missing or empty in testReport JSON")

    # Ensure all result values are numeric (critical for plotting)
    cleaned_results = {}
    for key, value in results.items():
        if isinstance(value, (int, float)):
            cleaned_results[key] = value
        else:
            raise ValueError(
                f"❌ Result '{key}' must be numeric, got {type(value).__name__}"
            )

    # ----------------------------------------------------
    # 2. Ensure output directory exists
    # ----------------------------------------------------

    output_dir = os.path.dirname(csv_path)
    os.makedirs(output_dir, exist_ok=True)

    # ----------------------------------------------------
    # 3. Prepare CSV structure
    # ----------------------------------------------------

    headers = ["date", "time", "test"] + list(cleaned_results.keys())
    row = [date, time, test] + list(cleaned_results.values())

    # ----------------------------------------------------
    # 4. Write CSV (overwrite-safe due to timestamped filename)
    # ----------------------------------------------------

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)

    print("✅ Performance CSV written successfully:")
    print(csv_path)
