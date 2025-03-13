import os
import json
import time
import requests
import threading

# Input folder
INPUT_FOLDER = "inputs"

# File paths
metrics_profile_path = os.path.join(os.getcwd(), INPUT_FOLDER, "metrics_profile.json")
experiment_path = os.path.join(os.getcwd(), INPUT_FOLDER, "create_exp.json")

# API URLs
CREATE_METRICS_PROFILE = "http://127.0.0.1:8080/createMetricProfile"
CREATE_EXPERIMENT = "http://127.0.0.1:8080/createExperiment"
GENERATE_RECOMMENDATIONS = "http://127.0.0.1:8080/generateRecommendations"

# Number of threads and experiments per thread
NUM_THREADS = 4
TOTAL_EXPERIMENTS = 100_000
EXPERIMENTS_PER_THREAD = TOTAL_EXPERIMENTS // NUM_THREADS


def read_json(file_path):
    """ Reads a JSON file and returns the data """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f" ✗ Error reading {file_path}: {e}")
        return None


def post_request(url, json_data, name):
    """ Sends a POST request and prints the status """
    try:
        response = requests.post(url, json=json_data)
        if 200 <= response.status_code <= 299:
            print(f" ✓ Successfully created {name}")
            return True
        else:
            print(f" ✗ Failed to create {name} (Status: {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f" ✗ Error sending request to {name}: {e}")
        return False
    
def generate_recommendations(exp_name):
    """ Calls /generateRecommendations as a POST request but ignores the response """
    try:
        post_request(GENERATE_RECOMMENDATIONS, {"experiment_name": exp_name}, f"Recommendation for {exp_name}", silent=True)
        print(f" → Triggered recommendation for {exp_name}")
    except Exception:
        pass  # Silently ignore errors



def create_experiments(thread_id, base_experiment_data, start_index, end_index):
    """ Creates experiments with unique names and sends requests """
    for i in range(start_index, end_index):
        # Modify the experiment JSON dynamically
        exp_data = base_experiment_data.copy()
        exp_name = f"thread_{thread_id}_exp_{i}"
        exp_data["experiment_name"] = f"thread_{thread_id}_exp_{i}"
        exp_data["kubernetes_objects"][0]["name"] = f"thread_{thread_id}_deployment_{i}"
        exp_data["kubernetes_objects"][0]["containers"][0]["container_name"] = f"thread_{thread_id}_container_{i}"
        exp_data["kubernetes_objects"][0]["containers"][0]["container_image_name"] = f"docker.io/thread_{thread_id}_image_{i}"

        # Send the request
        if post_request(CREATE_EXPERIMENT, [exp_data], f"Experiment {exp_name}"):
            generate_recommendations(exp_name)


def main():
    # Read metrics profile
    metrics_data = read_json(metrics_profile_path)
    if metrics_data is None:
        print("✗ Error reading metrics profile")
        return

    # Create metrics profile first
    if not post_request(CREATE_METRICS_PROFILE, metrics_data, "Metric Profile"):
        print("✗ Error creating Metrics Profile")
        return

    # Read base experiment data
    experiment_data = read_json(experiment_path)
    if experiment_data is None:
        print("✗ Error reading experiment template")
        return

    # Start threads
    threads = []
    for thread_id in range(NUM_THREADS):
        start_index = thread_id * EXPERIMENTS_PER_THREAD
        end_index = start_index + EXPERIMENTS_PER_THREAD
        thread = threading.Thread(target=create_experiments, args=(thread_id + 1, experiment_data[0], start_index, end_index))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("✓ All experiments created successfully!")


if __name__ == "__main__":
    main()
