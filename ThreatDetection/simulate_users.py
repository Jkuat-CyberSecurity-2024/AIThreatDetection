import requests
import random
import time
import json
from datetime import datetime
from pathlib import Path
from multiprocessing import Process, Lock, current_process
import signal
import sys

# API base URL
BASE_URL = "http://localhost:80"

# JSON files to store user data and tokens
USER_DATA_FILE = "user_data.json"
LOG_FILE = "user_activity_log.txt"
HISTORY_LOG_FILE = "user_history_log.txt"

# Sample data template for users
user_template = {
    "admin": {"email": "admin@example.com", "password": "AdminPass123"},
    "patient": {"email": "patient@example.com", "password": "PatientPass123"},
    "provider": {"email": "provider@example.com", "password": "ProviderPass123"},
}

# Global flag for gracefully stopping the simulation
is_running = True
file_lock = Lock()  # Lock for file access synchronization

# Load or initialize user data
def load_user_data():
    with file_lock:
        if Path(USER_DATA_FILE).exists():
            with open(USER_DATA_FILE, "r") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    log_activity("Error reading user data file; initializing empty data.")
                    return {"tokens": {}, "users": {}}
        else:
            return {"tokens": {}, "users": {}}

# Save user data to file with file lock
def save_user_data(data):
    with file_lock:
        with open(USER_DATA_FILE, "w") as file:
            json.dump(data, file, indent=4)

# Log user activity to a file
def log_activity(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [PID {current_process().pid}] {message}"
    print(log_entry)  # Print log to console for live monitoring
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry + "\n")

# Log user history for audit
def log_history(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    with open(HISTORY_LOG_FILE, "a") as history_file:
        history_file.write(log_entry + "\n")

# Initialize user data
user_data = load_user_data()
tokens = user_data["tokens"]
def create_user(user_type, user_id):
    if not is_running:
        return
    
    username = f"{user_type}_user_{user_id}"
    
    # Check if user is already registered
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
    
    # Retry loop for user registration
    while is_running:
        log_activity(f"Attempting to create user '{username}'...")
        
        try:
            response = requests.post(f"{BASE_URL}/register/", data=user_info)
            if response.status_code == 201:
                log_activity(f"User '{username}' created successfully.")
                
                # Store user info and tokens
                user_data["users"][username] = user_info
                save_user_data(user_data)
                log_history(f"User '{username}' created.")
                break  # Exit loop if registration succeeds
            else:
                log_activity(f"Failed to create user '{username}': {response.json()}")
                
        except Exception as e:
            log_activity(f"Exception while creating user '{username}': {str(e)}")
        
        # Delay before retrying
        retry_delay = random.uniform(5, 15)
        log_activity(f"Retrying registration for '{username}' in {retry_delay:.2f} seconds.")
        time.sleep(retry_delay)

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
            user_info = response.json()
            tokens[username] = {
                "access": user_info.get("access"),
                "refresh": user_info.get("refresh")
            }
            user_data["tokens"] = tokens
            save_user_data(user_data)
            log_activity(f"User '{username}' logged in successfully.")
            log_history(f"User '{username}' logged in.")
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
    
    new_data = {
        "first_name": f"Updated_{user_type.capitalize()}_{user_id}",
        "last_name": f"User_{user_id}",
        "email": f"updated_{username}@example.com"
    }
    
    try:
        response = requests.patch(f"{BASE_URL}/user/pk/", headers=headers, data=new_data)
        if response.status_code == 200:
            log_activity(f"User '{username}' updated successfully.")
        else:
            log_activity(f"Failed to update user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception during update for user '{username}': {str(e)}")

def delete_user(user_type, user_id):
    username = f"{user_type}_user_{user_id}"
    if tokens.get(username) is None:
        log_activity(f"Skipping deletion for '{username}' as no valid credentials are available.")
        return

    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    log_activity(f"Deleting user '{username}'...")
    try:
        response = requests.delete(f"{BASE_URL}/users/pk/", headers=headers)
        if response.status_code == 204:
            log_activity(f"User '{username}' deleted successfully.")
            log_history(f"User '{username}' deleted.")
            user_data["users"].pop(username, None)
            user_data["tokens"].pop(username, None)
            save_user_data(user_data)
        else:
            log_activity(f"Failed to delete user '{username}': {response.json()}")
    except Exception as e:
        log_activity(f"Exception while deleting user '{username}': {str(e)}")

def simulate_user_activity(user_type, user_id):
    # Initial delay to spread out user starts
    delay_start = random.uniform(1, 5)
    log_activity(f"Delaying start of '{user_type}_user_{user_id}' simulation by {delay_start:.2f} seconds.")
    time.sleep(delay_start)
    
    log_activity(f"Starting simulation for '{user_type}_user_{user_id}'...")
    
    # Create and login the user with retries until successful
    create_user(user_type, user_id)
    login_user(user_type, user_id)
    
    # Define available actions with respective weights (for probability)
    actions = [get_user_data, update_user, delete_user]
    action_weights = [0.6, 0.3, 0.1]  # Higher probability for data retrieval, lower for delete
    
    # Activity loop
    while is_running:
        # Select an action based on the defined weights
        action = random.choices(actions, weights=action_weights, k=1)[0]
        
        try:
            log_activity(f"User '{user_type}_user_{user_id}' performing action '{action.__name__}'...")
            action(user_type, user_id)
        except Exception as e:
            log_activity(f"Exception during '{action.__name__}' for user '{user_type}_user_{user_id}': {str(e)}")
            # Add a backoff delay in case of failure
            backoff_delay = random.uniform(10, 30)
            log_activity(f"User '{user_type}_user_{user_id}' will retry action '{action.__name__}' after {backoff_delay:.2f} seconds.")
            time.sleep(backoff_delay)
            continue  # Retry current action after delay

        # Regular delay before the next action
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
