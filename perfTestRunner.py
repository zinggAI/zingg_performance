import os
import json
from datetime import datetime
from perf_csv_writer import write_perf_csv

# ----------------------------------------------------
# 1. Resolve testReport JSON path
# ----------------------------------------------------

RAW_INPUT = os.environ.get("INPUT")
if not RAW_INPUT:
    raise ValueError("❌ INPUT environment variable not set")

REPORT_FILE = os.path.abspath(RAW_INPUT)

print("Using testReport JSON:", REPORT_FILE)
print("Exists:", os.path.exists(REPORT_FILE))

if not os.path.exists(REPORT_FILE):
    raise FileNotFoundError(f"❌ testReport JSON not found: {REPORT_FILE}")

# ----------------------------------------------------
# 2. Load report JSON
# ----------------------------------------------------

with open(REPORT_FILE, "r") as f:
    report = json.load(f)

# ----------------------------------------------------
# 3. Prepare CSV path
# ----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

test_name = report.get("test", "unknown_test")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

csv_path = os.path.join(
    RESULTS_DIR,
    f"{test_name}_{timestamp}.csv"
)

print("Writing CSV to:", csv_path)

# ----------------------------------------------------
# 4. Write CSV from report JSON
# ----------------------------------------------------

write_perf_csv(report, csv_path)

print("🎉 Performance CSV generation completed successfully")
