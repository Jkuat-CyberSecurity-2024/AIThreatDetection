import requests
import random
import json
import time
import os
from datetime import datetime
from pathlib import Path
from multiprocessing import Process, Lock
from requests.exceptions import RequestException

# Constants
BASE_URL = os.getenv("BASE_URL", "http://localhost:80/")  # Base URL for API
REGISTER_URL = f"{BASE_URL}register/"  # Registration endpoint
LOGIN_URL = f"{BASE_URL}login/"  # Login endpoint
USER_DATA_URL = f"{BASE_URL}users/pk/"  # User data retrieval endpoint
PATCH_USER_URL = f"{BASE_URL}users/pk/"  # Endpoint for patching user data
LOGOUT_URL = f"{BASE_URL}logout/"  # Logout endpoint
DELETE_USER_URL = f"{BASE_URL}users/pk/"  # Delete user endpoint
USER_DATA_FILE = "user_data.json"
LOG_FILE = "user_registration_log.txt"
MAX_USERS_PER_TYPE = int(os.getenv("MAX_USERS_PER_TYPE", 3))  # Max users per type, configurable
RETRY_LIMIT = 3  # Number of retries for HTTP requests

# User template with example credentials
user_template = {
    "admin": {"email": "admin@example.com", "password": "AdminPass123"},
    "patient": {"email": "patient@example.com", "password": "PatientPass123"},
    "provider": {"email": "provider@example.com", "password": "ProviderPass123"},
}

# Initialize user data storage
file_lock = Lock()  # Lock for synchronized file access

# Function to log messages
def log_activity(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)  # Print to console for live monitoring
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry + "\n")

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
    username = f"{user_type}_user_{len(user_data['users']) + 1}"  # Generate a unique username
    email = f"{username}@example.com"
    password = user_template[user_type]["password"]
    
    # Registration payload with all required fields
    user_info = {
        "username": username,
        "email": email,
        "password1": password,
        "password2": password,
        "user_type": user_type
    }

    # Simulate registration
    try:
        response = make_request(REGISTER_URL, method='post', data=user_info)
        if response and response.get("status_code") == 201:
            log_activity(f"User '{username}' created successfully.")
            user_data["users"][username] = user_info
            save_user_data(user_data)
            return username  # Return the created username for login
        else:
            log_activity(f"Failed to create user '{username}': {response.get('text', 'Unknown error')}")
            return None
    except Exception as e:
        log_activity(f"Error during registration of '{username}': {str(e)}")
        return None

# Function to login a user and store tokens
def login_user(user_data, username):
    # Ensure username exists in user_data
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
        if response and response.get("status_code") == 200:
            tokens = response
            user_data["tokens"][username] = {
                "access": tokens.get("access"),
                "refresh": tokens.get("refresh")
            }
            save_user_data(user_data)
            log_activity(f"User '{username}' logged in successfully. Tokens stored.")
            return tokens.get("access")  # Return access token
        else:
            log_activity(f"Failed to log in user '{username}': {response.get('text', 'Unknown error')}")
            return None
    except Exception as e:
        log_activity(f"Error during login of '{username}': {str(e)}")
        return None

# Function to simulate user actions
def simulate_user_activity(username, user_data):
    access_token = login_user(user_data, username)
    if access_token is None:
        return  # Exit if login fails

    while True:
        action = random.choices(
            ["get_user_data", "update_user_data", "logout", "delete_user"],
            weights=[0.6, 0.3, 0.05, 0.05],  # Weighting for actions
            k=1
        )[0]

        if action == "get_user_data":
            get_user_data(username, access_token)

        elif action == "update_user_data":
            update_user_data(username, access_token)

        elif action == "logout":
            logout_user(username, access_token)
            break  # Exit loop after logging out

        elif action == "delete_user":
            delete_user(username, access_token)
            break  # Exit loop after deletion

        # Random delay before the next action
        delay = random.uniform(5, 15)
        log_activity(f"User '{username}' waiting for {delay:.2f} seconds before next action...")
        time.sleep(delay)

# Function to get user data
def get_user_data(username, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(USER_DATA_URL, headers=headers)
        if response.status_code == 200:
            log_activity(f"User '{username}' fetched data successfully: {response.json()}")
        else:
            log_activity(f"Failed to fetch data for user '{username}': {response.text}")
    except Exception as e:
        log_activity(f"Error fetching data for '{username}': {str(e)}")

# Function to update user data
def update_user_data(username, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    new_data = {
        "email": f"updated_{username}@example.com",  # Simulate an update
    }
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
        else:
            log_activity(f"Failed to delete user '{username}': {response.text}")
    except Exception as e:
        log_activity(f"Error deleting '{username}': {str(e)}")

# Helper function to make HTTP requests with retries
def make_request(url, method='get', data=None):
    for attempt in range(RETRY_LIMIT):  # Retry up to RETRY_LIMIT times
        try:
            if method.lower() == 'post':
                response = requests.post(url, json=data)
            elif method.lower() == 'patch':
                response = requests.patch(url, json=data)
            else:
                response = requests.get(url)
            
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()  # Return the JSON response
        except RequestException as e:
            log_activity(f"Error during {method.upper()} request to '{url}': {str(e)}")
            time.sleep(2 ** attempt)  # Exponential backoff
    return None  # Return None if all retries fail

# Main function to register users and log them in
def register_and_login_users():
    user_data = load_user_data()  # Load existing user data

    # Only create new users if there are no existing users
    if len(user_data["users"]) == 0:
        for user_type in user_template.keys():
            for _ in range(MAX_USERS_PER_TYPE):  # Create users for each user type
                username = create_user(user_data, user_type)
                if username:  # If user creation was successful
                    # Start user simulation immediately after creation
                    p = Process(target=simulate_user_activity, args=(username, user_data,))
                    p.start()  # Start a new process for each user
                # Stagger the creation of users by waiting for a random period between 10 to 40 seconds
                delay = random.uniform(10, 40)
                log_activity(f"Waiting for {delay:.2f} seconds before creating the next user...")
                time.sleep(delay)

    # Continuously simulate user activity for existing users
    while True:
        user_data = load_user_data()  # Reload user data to check for existing users
        processes = []
        for username in user_data["users"].keys():
            p = Process(target=simulate_user_activity, args=(username, user_data,))
            p.start()  # Start a new process for each user
            processes.append(p)

        for p in processes:
            p.join()  # Wait for all user processes to finish

        # Check if there are any users left
        if not user_data["users"]:
            log_activity("All users have been deleted. Exiting the simulation.")
            break  # Exit loop if no users are left

if __name__ == "__main__":
    log_activity("Starting user registration and login...")
    register_and_login_users()
    log_activity("User registration and login completed.")
