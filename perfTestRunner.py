import subprocess
import json
import time
import os
from datetime import date, datetime

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Set the timestamp as an environment variable
os.environ["TIMESTAMP"] = TIMESTAMP
print(f"perfTestRunner: Set TIMESTAMP = {TIMESTAMP}")

INPUT_FILE = os.environ.get("INPUT")
print(f"INPUT_FILE = {INPUT_FILE}")
PERFORMANCE_THRESHOLD = 1.2  # 5% increase in test time
WINDOW_THRESHOLD = 10 #set 10 minutes window threshold

def load_test_config():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Configuration file not found!")
    with open(INPUT_FILE, "r") as file:
        return json.load(file)

# Load configuration
config = load_test_config()
testName = config["testName"]
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
    if os.path.exists(reportFile):
        with open(reportFile, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_results(data):
    """Save current test results to the report file."""
    with open(reportFile, "w") as f:
        json.dump(data, f, indent=4)


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
        "results": {}
    }
    return test_data

def perform_window_validation(new_time, prev_time):
    if new_time - prev_time > WINDOW_THRESHOLD:
        return False
    return True

def perform_percentage_validation(new_time, prev_time):
    if new_time > prev_time * PERFORMANCE_THRESHOLD:
        return False
    return True


def compare_results(prev_results, new_results):
    """Compare new results with previous ones and check for performance degradation."""

    test_fail = False

    for phaseName, times in new_results.items():
        if phaseName in prev_results:
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
