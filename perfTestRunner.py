import collections
import subprocess
import json
import csv
import time
import os
import platform
import re
import shutil
import multiprocessing
from datetime import date, datetime

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Set the timestamp as an environment variable
os.environ["TIMESTAMP"] = TIMESTAMP
print(f"perfTestRunner: Set TIMESTAMP = {TIMESTAMP}")

INPUT_FILE = os.environ.get("INPUT")
print(f"INPUT_FILE = {INPUT_FILE}")
PERFORMANCE_THRESHOLD = 1.05  # 5% increase in test time
WINDOW_THRESHOLD = 10 #set 10 minutes window threshold

def detect_pc_specs():
    specs = {}
    specs["OS"] = f"{platform.system()} {platform.release()}"
    try:
        cpu = platform.processor() or platform.machine()
        cores = multiprocessing.cpu_count()
        specs["CPU"] = f"{cpu} · {cores} cores"
    except Exception:
        specs["CPU"] = "N/A"
    try:
        if platform.system() == "Darwin":
            r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
            specs["RAM"] = f"{int(r.stdout.strip()) / (1024**3):.0f} GB"
        elif platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        specs["RAM"] = f"{int(line.split()[1]) / (1024**2):.0f} GB"
                        break
        else:
            specs["RAM"] = "N/A"
    except Exception:
        specs["RAM"] = "N/A"
    try:
        total, _, _ = shutil.disk_usage("/")
        specs["Storage"] = f"{total / (1024**3):.0f} GB"
    except Exception:
        specs["Storage"] = "N/A"
    try:
        
        r = subprocess.run(["spark-submit", "--version"], capture_output=True, text=True, timeout=10)
        #spark often prints out it version through the error stream, hence(stdout+stderr)
        for line in (r.stderr + r.stdout).splitlines():
            if "version" in line.lower():
                specs["Spark"] = line.strip()
                break
        else:
            specs["Spark"] = "N/A"
    except Exception:
        specs["Spark"] = "N/A"
    try:
        r = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
        first_line = (r.stderr + r.stdout).splitlines()[0]
        specs["Java"] = first_line.replace('"', '').strip()
    except Exception:
        specs["Java"] = "N/A"
    return specs

def load_test_config():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Configuration file not found!")
    with open(INPUT_FILE, "r") as file:
        return json.load(file)

# Load configuration
config = load_test_config()
testName = config["testName"]
test_prefix = re.sub(r'\W+', '_', os.path.splitext(os.path.basename(INPUT_FILE))[0]).strip('_').lower()
zinggScript = config["zinggScript"]
propertyFile = config["propertyFile"]
reportFile = config["reportFile"]
workingDirectory = config["directory"]
setup = config["setup"]
teardown = config["teardown"]

print(f"CONFIG: testName={testName} | zinggScript={zinggScript} | propertyFile={propertyFile} | reportFile={reportFile}")
# replace placeholders in command line
testConfig = config.copy()
for phase in testConfig["tests"]:
    testConfig["tests"][phase] = testConfig["tests"][phase].format(
        zinggScript=zinggScript,
        propertyFile=propertyFile
    )

tests = testConfig["tests"]

os.chdir(os.path.abspath(workingDirectory))

def load_results():
    """Load previous test results if available."""

    results = {}
    report_dir = os.path.dirname(reportFile) if reportFile else ""
    
    for phase in tests.keys():
        if report_dir:
            phase_file = os.path.join(report_dir, f"{test_prefix}_{phase}_report.csv")
        else:
            phase_file = f"{test_prefix}_{phase}_report.csv"

        if os.path.exists(phase_file) and os.path.getsize(phase_file)>0:
            with open(phase_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    last_row = rows[-1]

                    try:
                        results[phase] = float(last_row["duration"])
                    except ValueError:
                        results[phase] = last_row["duration"]
    return {"results": results}

def save_results(data):
    """Save current test results to the report file"""

    current_year = str(date.today().year)
    report_dir = os.path.dirname(reportFile) if reportFile else ""

    for phase, duration in data["results"].items():
        if report_dir:
            os.makedirs(os.path.abspath(report_dir), exist_ok=True)
            phase_file = os.path.join(report_dir, f"{test_prefix}_{phase}_report.csv")
        else:
            phase_file = f"{test_prefix}_{phase}_report.csv"

        # -----YEARLY ROLLOVER CHECK---
        if os.path.exists(phase_file) and os.path.getsize(phase_file)>0:
            with open(phase_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    last_row = rows[-1]
                    last_run_year = last_row["date"].split("-")[0]

                    if current_year != last_run_year:
                        archive_file = f"{test_prefix}_{phase}_report_{last_run_year}.csv"
                        os.rename(phase_file, archive_file)
                        print(f"Year changed! Archived {phase_file} to {archive_file}")   

        file_exists = os.path.exists(phase_file) and os.path.getsize(phase_file)>0

        with open(phase_file, "a", newline="") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(["date", "time", "test", "duration"])

            writer.writerow([
                data["date"],
                data["time"],
                data["test"],
                duration
            ])

        print(f"Results for {phase} saved to {phase_file}")

    
def run_phase(phases, commandLine):
    """Run a single test phase."""
    print(f"Running phase - {phases}")
    exit_code = subprocess.call(commandLine, shell=True)
    return exit_code


def write_on_start():
    """Initialize test report with metadata."""
    test_data = {
        "date": str(date.today()),
        "time": current_time,
        "test": testName,
        "results": {},
        "pcSpecs": detect_pc_specs(),
        "dataSpecs": config.get("dataSpecs", {})
    }
    return test_data

def save_json_report(test_data):
    """Write full report (results + specs) to reportFile."""
    if not reportFile:
        return
    os.makedirs(os.path.dirname(os.path.abspath(reportFile)), exist_ok=True)
    with open(reportFile, "w") as f:
        json.dump(test_data, f, indent=4)
    print(f"JSON report written to {reportFile}")

def perform_window_validation(new_time, prev_time):
    print(f"Comparing new_time: {new_time} with prev_time: {prev_time}")
    if new_time - prev_time > WINDOW_THRESHOLD:
        return False
    return True

def perform_percentage_validation(new_time, prev_time):
    print(f"Comparing new_time: {new_time} with prev_time: {prev_time}")
    if new_time > prev_time * PERFORMANCE_THRESHOLD:
        return False
    return True


def compare_results(prev_results, new_results):
    """Compare new results with previous ones and check for performance degradation."""

    test_fail = False

    for phaseName, times in new_results.items():
        if phaseName in prev_results:
            print(f"Comparing results for phase: {phaseName}")
            prev_time = prev_results[phaseName]
            new_time = round(times / 60, 2)  # Convert seconds to minutes
            test_pass = True
            if phaseName == "train":
                test_pass = perform_window_validation(new_time, prev_time)
            else:
                test_pass = perform_percentage_validation(new_time, prev_time)

            if test_pass == False:
                print(f"Performance degradation detected in phase {phaseName}!")
                print(f"Previous time: {prev_time} min, New time: {new_time} min")
                test_fail = True
    return test_fail


def perform_load_test():

    prev_results = load_results().get("results", {})

    test_data = write_on_start()  # Initialize metadata

    phase_time = {
        "results": {}
    }

    for phases, commandLine in tests.items():
        try:
            t1 = time.time()
            exit_code = run_phase(phases, commandLine)
            t2 = time.time()
            if exit_code == 1:
                phase_time["results"][phases] = "errored_out"
            else:
                phase_time["results"][phases] = t2 - t1
        except Exception as e:
            print(e)

    # Compare results **before** writing
    test_fail = compare_results(prev_results, phase_time["results"])

    test_data["results"] = {}

    # write results
    for phaseName, times in phase_time["results"].items():
        if times == "errored_out":
            test_data["results"][phaseName] =  "phase errored out!"
        else:
            test_data["results"][phaseName] =  round(times / 60, 2)

    # Save results after successful test execution
    save_results(test_data)
    save_json_report(test_data)

    if test_fail:
        exit(1)

def main():
    if setup is not None:
        subprocess.run(f"python3 {setup}", shell=True, check=True, env=os.environ)
    perform_load_test()
    if teardown:
        subprocess.run(f"python3 {teardown}", shell=True, check=True, env=os.environ)

if __name__ == "__main__":
    main()
