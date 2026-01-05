import os
import json
import time
from datetime import datetime
from perf_csv_writer import write_perf_csv

# -------------------------------------------------------------------
# 1. Resolve INPUT file ONCE, as an ABSOLUTE path (CRITICAL FIX)
# -------------------------------------------------------------------

RAW_INPUT = os.environ.get("INPUT")
if not RAW_INPUT:
    raise ValueError("INPUT environment variable is not set")

INPUT_FILE = os.path.abspath(RAW_INPUT)

print("RAW_INPUT =", RAW_INPUT)
print("ABS_INPUT_FILE =", INPUT_FILE)
print("Exists before chdir =", os.path.exists(INPUT_FILE))

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Configuration file not found: {INPUT_FILE}")

# -------------------------------------------------------------------
# 2. Timestamp (used for unique CSV names)
# -------------------------------------------------------------------

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
os.environ["TIMESTAMP"] = TIMESTAMP
print(f"perfTestRunner: Set TIMESTAMP = {TIMESTAMP}")

# -------------------------------------------------------------------
# 3. Load test configuration (NO relative paths here)
# -------------------------------------------------------------------

def load_test_config():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

config = load_test_config()

# -------------------------------------------------------------------
# 4. Extract required fields from JSON
# -------------------------------------------------------------------

test_name = config.get("testName", "unknown_test")
zingg_script = config.get("zinggScript")
property_file = config.get("propertyFile")
working_directory = config.get("workingDirectory", ".")

if not zingg_script or not property_file:
    raise ValueError("Missing required fields in test config JSON")

# Convert important paths to ABSOLUTE before chdir
zingg_script = os.path.abspath(zingg_script)
property_file = os.path.abspath(property_file)
working_directory = os.path.abspath(working_directory)

print("zingg_script =", zingg_script)
print("property_file =", property_file)
print("working_directory =", working_directory)

# -------------------------------------------------------------------
# 5. Change directory ONLY AFTER paths are frozen
# -------------------------------------------------------------------

os.makedirs(working_directory, exist_ok=True)
os.chdir(working_directory)

print("PWD after chdir =", os.getcwd())

# -------------------------------------------------------------------
# 6. Run the performance test
# -------------------------------------------------------------------

start_time = time.time()

exit_code = os.system(f"bash {zingg_script} {property_file}")

end_time = time.time()
duration_sec = round(end_time - start_time, 2)

# -------------------------------------------------------------------
# 7. Prepare CSV output directory
# -------------------------------------------------------------------

RESULTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "results")
)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Unique CSV name every run
csv_file = os.path.join(
    RESULTS_DIR,
    f"{test_name}_{TIMESTAMP}.csv"
)

# -------------------------------------------------------------------
# 8. Write CSV
# -------------------------------------------------------------------

write_perf_csv(
    csv_path=csv_file,
    test_name=test_name,
    duration_sec=duration_sec,
    exit_code=exit_code,
    timestamp=TIMESTAMP
)

print("CSV written to:", csv_file)

# -------------------------------------------------------------------
# 9. Exit with correct status
# -------------------------------------------------------------------

if exit_code != 0:
    raise RuntimeError(f"Performance test failed with exit code {exit_code}")

print("Performance test completed successfully.")
