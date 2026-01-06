import os
import json
from datetime import datetime
from perf_csv_writer import write_perf_csv

# ----------------------------------------------------
# 1. Read RESULT JSON (testReport_*.json)
# ----------------------------------------------------

RAW_INPUT = os.environ.get("INPUT")
if not RAW_INPUT:
    raise ValueError("INPUT environment variable not set")

INPUT_FILE = os.path.abspath(RAW_INPUT)
print("Using report JSON:", INPUT_FILE)

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Report JSON not found: {INPUT_FILE}")

with open(INPUT_FILE, "r") as f:
    report = json.load(f)

# ----------------------------------------------------
# 2. Extract meaningful test results
# ----------------------------------------------------

test_name = report.get("testName", "unknown_test")

# Example metrics (adjust keys if needed)
metrics = {
    "total_records": report.get("totalRecords"),
    "matched_records": report.get("matchedRecords"),
    "precision": report.get("precision"),
    "recall": report.get("recall"),
    "f1_score": report.get("f1Score"),
    "duration_sec": report.get("durationSeconds"),
}

# Remove None values
metrics = {k: v for k, v in metrics.items() if v is not None}

if not metrics:
    raise ValueError("No metrics found in testReport JSON")

# ----------------------------------------------------
# 3. Prepare CSV path
# ----------------------------------------------------

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(base_dir, "results")
os.makedirs(results_dir, exist_ok=True)

csv_path = os.path.join(results_dir, f"{test_name}_{timestamp}.csv")

# ----------------------------------------------------
# 4. Write CSV
# ----------------------------------------------------

write_perf_csv(
    test_name=test_name,
    metrics=metrics,
    csv_path=csv_path
)

print("✅ Results CSV written:", csv_path)
