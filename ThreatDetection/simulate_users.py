import requests
import random
import time
import json
from datetime import datetime
from pathlib import Path
from multiprocessing import Process, current_process
import signal
import sys

# API base URL
BASE_URL = "http://localhost:80"

# JSON file to store user data and tokens
USER_DATA_FILE = "user_data.json"
LOG_FILE = "user_activity_log.txt"

# Sample data template for users
user_template = {
    "admin": {"email": "admin@example.com", "password": "AdminPass123"},
    "patient": {"email": "patient@example.com", "password": "PatientPass123"},
    "provider": {"email": "provider@example.com", "password": "ProviderPass123"},
}

# Global flag for gracefully stopping the simulation
is_running = True

# Load or initialize user data
def load_user_data():
    if Path(USER_DATA_FILE).exists():
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    else:
        return {"tokens": {}, "users": {}}

# Save user data to file
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Log user activity to a file
def log_activity(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [PID {current_process().pid}] {message}"
    print(log_entry)  # Prints log to console for live monitoring
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry + "\n")

# Initialize user data
user_data = load_user_data()
tokens = user_data["tokens"]

def create_user(user_type, user_id):
    if not is_running:
        return
    username = f"{user_type}_user_{user_id}"
    if username in user_data["users"]:
        log_activity(f"User '{username}' already exists. Skipping creation.")
        return

    user_info = {
        "username": username,
        "email": f"{username}@example.com",
        "password1": user_template[user_type]["password"],
        "password2": user_template[user_type]["password"],
        "user_type": user_type
    }
    log_activity(f"Creating user '{username}'...")
    try:
        response = requests.post(f"{BASE_URL}/register/", data=user_info)
        if response.status_code == 201:
            log_activity(f"User '{username}' created successfully.")
            user_data["users"][username] = user_info
            save_user_data(user_data)
        else:
            log_activity(f"Failed to create user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception while creating user '{username}': {str(e)}")
    time.sleep(random.uniform(1, 2))

def login_user(user_type, user_id):
    if not is_running:
        return
    username = f"{user_type}_user_{user_id}"
    log_activity(f"Logging in user '{username}'...")
    try:
        response = requests.post(f"{BASE_URL}/login/", data={
            "username": username,
            "password": user_template[user_type]["password"]
        })
        if response.status_code == 200:
            tokens[username] = {
                "access": response.json().get("access"),
                "refresh": response.json().get("refresh")
            }
            user_data["tokens"] = tokens
            save_user_data(user_data)
            log_activity(f"User '{username}' logged in successfully.")
        else:
            log_activity(f"Failed to log in user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception during login for user '{username}': {str(e)}")
    time.sleep(random.uniform(1, 2))

def refresh_token(user_type, user_id):
    if not is_running:
        return
    username = f"{user_type}_user_{user_id}"
    refresh_token = tokens.get(username, {}).get("refresh")
    if not refresh_token:
        log_activity(f"No refresh token found for '{username}'. Cannot refresh token.")
        return

    log_activity(f"Refreshing token for user '{username}'...")
    try:
        response = requests.post(f"{BASE_URL}/token/refresh/", data={"refresh": refresh_token})
        if response.status_code == 200:
            tokens[username]["access"] = response.json().get("access")
            user_data["tokens"] = tokens
            save_user_data(user_data)
            log_activity(f"Token refreshed for user '{username}'.")
        else:
            log_activity(f"Failed to refresh token for user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception while refreshing token for user '{username}': {str(e)}")

def perform_random_user_action(user_type, user_id):
    actions = [get_user_data, update_user, delete_user]
    action = random.choice(actions)
    log_activity(f"User '{user_type}_user_{user_id}' performing action '{action.__name__}'...")
    action(user_type, user_id)

def get_user_data(user_type, user_id):
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    log_activity(f"Fetching data for user '{username}'...")
    try:
        response = requests.get(f"{BASE_URL}/user/", headers=headers)
        if response.status_code == 200:
            log_activity(f"Data for user '{username}' retrieved successfully.")
        elif response.status_code == 401 and "token_not_valid" in response.json().get("code", ""):
            log_activity(f"Token for '{username}' expired; refreshing token...")
            refresh_token(user_type, user_id)
        else:
            log_activity(f"Failed to retrieve data for user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception while fetching data for user '{username}': {str(e)}")

def update_user(user_type, user_id):
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    log_activity(f"Updating data for user '{username}'...")
    try:
        response = requests.patch(f"{BASE_URL}/user/pk/", headers=headers, data={"email": f"updated_{username}@example.com"})
        if response.status_code == 200:
            log_activity(f"User '{username}' updated successfully.")
        else:
            log_activity(f"Failed to update user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception during update for user '{username}': {str(e)}")

def delete_user(user_type, user_id):
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    log_activity(f"Deleting user '{username}'...")
    try:
        response = requests.delete(f"{BASE_URL}/users/pk/", headers=headers)
        if response.status_code == 204:
            log_activity(f"User '{username}' deleted successfully.")
            user_data["users"].pop(username, None)
            user_data["tokens"].pop(username, None)
            save_user_data(user_data)
        else:
            log_activity(f"Failed to delete user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception while deleting user '{username}': {str(e)}")

def simulate_user_activity(user_type, user_id):
    delay_start = random.uniform(1, 5)
    log_activity(f"Delaying start of '{user_type}_user_{user_id}' simulation by {delay_start:.2f} seconds.")
    time.sleep(delay_start)
    log_activity(f"Starting simulation for '{user_type}_user_{user_id}'...")
    create_user(user_type, user_id)
    login_user(user_type, user_id)
    while is_running:
        perform_random_user_action(user_type, user_id)
        delay = random.uniform(60, 300)
        log_activity(f"User '{user_type}_user_{user_id}' waiting for {delay:.2f} seconds before next action...")
        time.sleep(delay)

def signal_handler(sig, frame):
    global is_running
    log_activity("Simulation stopping gracefully...")
    is_running = False
    sys.exit(0)

if __name__ == "__main__":
    log_activity("Starting user simulation...")
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C interrupt

    processes = []
    for user_type in user_template.keys():
        for user_id in range(1, 11):  # Example: simulate 10 users per type
            process = Process(target=simulate_user_activity, args=(user_type, user_id))
            process.start()
            processes.append(process)
    
    for process in processes:
        process.join()  # Wait for all processes to finish

    log_activity("User simulation terminated.")
