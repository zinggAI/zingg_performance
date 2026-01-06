import csv
import os


def write_perf_csv(report_json, csv_path):
    """
    Writes performance CSV from Zingg testReport JSON.

    Expected JSON format:
    {
      "date": "...",
      "time": "...",
      "test": "...",
      "results": {
          "train": <number>,
          "match": <number>,
          ...
      }
    }
    """

    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    date = report_json.get("date")
    time = report_json.get("time")
    test = report_json.get("test")
    results = report_json.get("results", {})

    if not isinstance(results, dict) or not results:
        raise ValueError("❌ 'results' field missing or empty in testReport JSON")

    # CSV headers
    headers = ["date", "time", "test"] + list(results.keys())

    # CSV row
    row = [date, time, test] + [results[k] for k in results.keys()]

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)

    print("✅ CSV written:", csv_path)
