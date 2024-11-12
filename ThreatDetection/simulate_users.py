import requests
import random
import json
import time
import os
from datetime import datetime
from pathlib import Path
from multiprocessing import Process, Lock, Manager
from requests.exceptions import RequestException

# Constants
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8010/secure/470cf4e9-a5f9-4098-834b-17886328e173/")
REGISTER_URL = f"{BASE_URL}register/"
LOGIN_URL = f"{BASE_URL}login/"
USER_DATA_URL = f"{BASE_URL}users/pk/"
PATCH_USER_URL = f"{BASE_URL}users/pk/"
LOGOUT_URL = f"{BASE_URL}logout/"
DELETE_USER_URL = f"{BASE_URL}users/pk/"
USER_DATA_FILE = "user_data.json"
LOG_FILE = "user_registration_log.txt"
RETRY_LIMIT = 3

# User template with example credentials
user_template = {
    "admin": {"email": "admin@example.com", "password": "AdminPass123"},
    "patient": {"email": "patient@example.com", "password": "PatientPass123"},
    "provider": {"email": "provider@example.com", "password": "ProviderPass123"},
}

file_lock = Lock()

# Function to log messages
def log_activity(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry + "\n")

# Helper function to make HTTP requests with retries
def make_request(url, method='get', data=None):
    for attempt in range(RETRY_LIMIT):
        try:
            if method.lower() == 'post':
                response = requests.post(url, json=data)
            elif method.lower() == 'patch':
                response = requests.patch(url, json=data)
            else:
                response = requests.get(url)
            
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            log_activity(f"Error during {method.upper()} request to '{url}': {str(e)}")
            time.sleep(2 ** attempt)
    return None

# Function to load user data from file
def load_user_data():
    if Path(USER_DATA_FILE).exists():
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {"users": {}, "tokens": {}}

# Function to save user data to file
def save_user_data(data):
    with file_lock:
        with open(USER_DATA_FILE, "w") as file:
            json.dump(data, file, indent=4)

# Function to create a user
def create_user(user_data, user_type):
    username = f"{user_type}_user_{len(user_data['users']) + 1}"
    email = f"{username}_{random.randint(1000, 9999)}@example.com"
    password = user_template[user_type]["password"]

    user_info = {
        "username": username,
        "email": email,
        "password1": password,
        "password2": password,
        "user_type": user_type
    }

    try:
        response = make_request(REGISTER_URL, method='post', data=user_info)

        if response and 'user' in response:
            log_activity(f"User '{username}' created successfully.")
            user_data["users"][username] = user_info
            save_user_data(user_data)  # Save immediately after creation
            return username
        else:
            error_message = response.get('text', 'Unknown error') if response else 'No response'
            log_activity(f"Failed to create user '{username}': {error_message}")
            return None
    except Exception as e:
        log_activity(f"Error during registration of '{username}': {str(e)}")
        return None

# Function to login a user and store tokens
def login_user(user_data, username):
    if username not in user_data["users"]:
        log_activity(f"User '{username}' not found in user data.")
        return None
    
    password = user_data["users"][username]["password1"]
    login_info = {
        "username": username,
        "password": password
    }

    try:
        response = make_request(LOGIN_URL, method='post', data=login_info)
        if response and 'access' in response:
            tokens = response
            user_data["tokens"][username] = {
                "access": tokens.get("access"),
                "refresh": tokens.get("refresh")
            }
            save_user_data(user_data)  # Update user tokens in the file
            log_activity(f"User '{username}' logged in successfully. Tokens stored.")
            return tokens.get("access")
        else:
            log_activity(f"Failed to log in user '{username}': {response.get('text', 'Unknown error')}")
            return None
    except Exception as e:
        log_activity(f"Error during login of '{username}': {str(e)}")
        return None

# Function to simulate random API traffic (e.g., get data, update data, etc.)
def simulate_traffic(username, user_data):
    access_token = login_user(user_data, username)
    if access_token is None:
        return

    # Random wait time before starting interactions
    time.sleep(random.uniform(5, 15))

    while True:
        action = random.choices(
            ["get_user_data", "update_user_data", "logout", "delete_user"],
            weights=[0.6, 0.3, 0.05, 0.05],
            k=1
        )[0]

        if action == "get_user_data":
            get_user_data(username, access_token)
        elif action == "update_user_data":
            update_user_data(username, access_token)
        elif action == "logout":
            logout_user(username, access_token)
            break
        elif action == "delete_user":
            delete_user(username, access_token)
            break

        # Randomized delay between actions
        delay = random.uniform(2, 10)
        log_activity(f"User '{username}' waiting for {delay:.2f} seconds before next action...")
        time.sleep(delay)

        # Random deletion after a certain period
        if random.random() < 0.01:  # 1% chance of deletion at each action
            delete_user(username, access_token)
            break

# Function to get user data
def get_user_data(username, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(USER_DATA_URL, headers=headers)
        if response.status_code == 200:
            log_activity(f"User '{username}' fetched data successfully.")
        else:
            log_activity(f"Failed to fetch data for user '{username}': {response.text}")
    except Exception as e:
        log_activity(f"Error fetching data for '{username}': {str(e)}")

# Function to update user data
def update_user_data(username, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    new_data = {"email": f"updated_{username}@example.com"}
    try:
        response = requests.patch(PATCH_USER_URL, headers=headers, json=new_data)
        if response.status_code == 200:
            log_activity(f"User '{username}' updated data successfully.")
        else:
            log_activity(f"Failed to update data for user '{username}': {response.text}")
    except Exception as e:
        log_activity(f"Error updating data for '{username}': {str(e)}")

# Function to logout a user
def logout_user(username, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.post(LOGOUT_URL, headers=headers)
        if response.status_code == 200:
            log_activity(f"User '{username}' logged out successfully.")
        user_data = load_user_data()
        if username in user_data["tokens"]:
            del user_data["tokens"][username]
        else:
            log_activity(f"Failed to logout user '{username}': {response.text}")
    except Exception as e:
        log_activity(f"Error logging out '{username}': {str(e)}")

# Function to delete a user
def delete_user(username, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.delete(DELETE_USER_URL, headers=headers)
        if response.status_code == 204:
            log_activity(f"User '{username}' deleted successfully.")
            user_data = load_user_data()
            if username in user_data["users"]:
                del user_data["users"][username]
            if username in user_data["tokens"]:
                del user_data["tokens"][username]
            save_user_data(user_data)  # Save after deletion
        else:
            log_activity(f"Failed to delete user '{username}': {response.text}")
    except Exception as e:
        log_activity(f"Error deleting '{username}': {str(e)}")

# Function to manage user creation and traffic simulation for multiple users
def manage_traffic():
    user_data = load_user_data()

    while True:
        user_data = load_user_data()

        # Simulate user creation with random delays
        user_type = random.choice(list(user_template.keys()))
        username = create_user(user_data, user_type)
        if username:
            p = Process(target=simulate_traffic, args=(username, user_data))
            p.start()

        # Random delay before creating the next user
        time.sleep(random.uniform(5, 15))

if __name__ == "__main__":
    log_activity("Starting traffic generation...")
    manage_traffic()
    log_activity("Traffic generation completed.")
