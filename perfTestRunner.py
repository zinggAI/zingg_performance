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

print(f"[INFO] Using testReport JSON: {REPORT_FILE}")

if not os.path.exists(REPORT_FILE):
    raise FileNotFoundError(f"❌ testReport JSON not found: {REPORT_FILE}")

# ----------------------------------------------------
# 2. Load report JSON
# ----------------------------------------------------

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report = json.load(f)

# ----------------------------------------------------
# 3. Validate expected JSON structure
# ----------------------------------------------------

required_keys = ["date", "test", "results"]

for key in required_keys:
    if key not in report:
        raise ValueError(f"❌ Missing required key '{key}' in testReport JSON")

if not isinstance(report["results"], dict) or not report["results"]:
    raise ValueError("❌ 'results' must be a non-empty dictionary")

print("[INFO] Test name:", report["test"])
print("[INFO] Metrics found:", list(report["results"].keys()))

# ----------------------------------------------------
# 4. Prepare CSV output path (append-only history)
# ----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

test_name = report["test"]
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

csv_path = os.path.join(
    RESULTS_DIR,
    f"{test_name}_{timestamp}.csv"
)

print(f"[INFO] Writing CSV to: {csv_path}")

# ----------------------------------------------------
# 5. Write CSV from report JSON
# ----------------------------------------------------

write_perf_csv(report, csv_path)

print("✅ Performance CSV generation completed successfully")

