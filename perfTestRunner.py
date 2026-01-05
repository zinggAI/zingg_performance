import os
import json
from datetime import datetime
from perf_csv_writer import write_perf_csv

# ----------------------------------------------------
# 1. Read INPUT JSON path from environment
# ----------------------------------------------------

RAW_INPUT = os.environ.get("INPUT")
if not RAW_INPUT:
    raise ValueError("❌ INPUT environment variable is not set")

INPUT_FILE = os.path.abspath(RAW_INPUT)

print("RAW_INPUT =", RAW_INPUT)
print("ABS_INPUT_FILE =", INPUT_FILE)
print("Exists =", os.path.exists(INPUT_FILE))

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"❌ Input JSON not found: {INPUT_FILE}")

# ----------------------------------------------------
# 2. Load JSON content
# ----------------------------------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, dict):
    raise ValueError("❌ Input JSON must be a dictionary")

# ----------------------------------------------------
# 3. Generate timestamp (unique per run)
# ----------------------------------------------------

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Safe test name
test_name = data.get("testName", "febrl_test")

# ----------------------------------------------------
# 4. Prepare results directory
# ----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

csv_path = os.path.join(
    RESULTS_DIR,
    f"{test_name}_{TIMESTAMP}.csv"
)

print("Writing CSV to:", csv_path)

# ----------------------------------------------------
# 5. Write CSV
# ----------------------------------------------------

write_perf_csv(
    data=data,
    csv_path=csv_path
)

print("✅ CSV successfully written")
print(csv_path)
