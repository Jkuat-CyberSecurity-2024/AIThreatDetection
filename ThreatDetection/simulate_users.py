import requests
import random
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

# JSON file to store user data and tokens
USER_DATA_FILE = "user_data.json"

# Sample data template for users
user_template = {
    "admin": {"email": "admin@example.com", "password": "AdminPass123"},
    "patient": {"email": "patient@example.com", "password": "PatientPass123"},
    "provider": {"email": "provider@example.com", "password": "ProviderPass123"},
}

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

# Initialize user data
user_data = load_user_data()
tokens = user_data["tokens"]

def create_user(user_type, user_id):
    """Create a user with a specific type and ID."""
    username = f"{user_type}_user_{user_id}"
    if username in user_data["users"]:
        print(f"{username} already exists. Skipping creation.")
        return

    user_info = {
        "username": username,
        "email": f"{username}@example.com",
        "password1": user_template[user_type]["password"],
        "password2": user_template[user_type]["password"],
        "user_type": user_type
    }
    print(f"Creating {user_type} user {user_id}...")
    response = requests.post(f"{BASE_URL}/register/", data=user_info)
    if response.status_code == 201:
        print(f"{user_type.capitalize()} user {user_id} created successfully.")
        user_data["users"][username] = user_info
        save_user_data(user_data)
    else:
        print(f"Failed to create {user_type} user {user_id}: {response.json()}")
    time.sleep(random.uniform(1, 2))

def login_user(user_type, user_id):
    """Log in a user and store both access and refresh tokens."""
    username = f"{user_type}_user_{user_id}"
    print(f"Logging in {user_type} user {user_id}...")
    response = requests.post(f"{BASE_URL}/login/", data={
        "username": username,
        "password": user_template[user_type]["password"]
    })
    if response.status_code == 200:
        # Store both access and refresh tokens
        tokens[username] = {
            "access": response.json().get("access"),
            "refresh": response.json().get("refresh")
        }
        user_data["tokens"] = tokens
        save_user_data(user_data)
        print(f"{user_type.capitalize()} user {user_id} logged in successfully.")
    else:
        print(f"Failed to log in {user_type} user {user_id}: {response.json()}")
    time.sleep(random.uniform(1, 2))

def refresh_token(user_type, user_id):
    """Refresh an expired token using the stored refresh token."""
    username = f"{user_type}_user_{user_id}"
    refresh_token = tokens.get(username, {}).get("refresh")
    if not refresh_token:
        print(f"No refresh token found for {username}. Cannot refresh.")
        return

    response = requests.post(f"{BASE_URL}/token/refresh/", data={"refresh": refresh_token})
    if response.status_code == 200:
        tokens[username]["access"] = response.json().get("access")
        user_data["tokens"] = tokens
        save_user_data(user_data)
        print(f"Token refreshed for {user_type} user {user_id}")
    else:
        print(f"Failed to refresh token for {user_type} user {user_id}: {response.json()}")

def get_user_data(user_type, user_id):
    """Request user data multiple times."""
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    for _ in range(random.randint(2, 5)):
        print(f"Requesting data for {user_type} user {user_id}...")
        response = requests.get(f"{BASE_URL}/user/", headers=headers)
        if response.status_code == 200:
            print(f"{user_type.capitalize()} user {user_id} data: {response.json()}")
        elif response.status_code == 401 and "token_not_valid" in response.json().get("code", ""):
            refresh_token(user_type, user_id)
        else:
            print(f"Failed to retrieve {user_type} user {user_id} data: {response.json()}")
        time.sleep(random.uniform(1, 3))

def update_user(user_type, user_id):
    """Update user data."""
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    print(f"Updating {user_type} user {user_id}...")
    new_data = {"email": f"updated_{username}@example.com"}
    response = requests.patch(f"{BASE_URL}/user/pk/", headers=headers, data=new_data)
    try:
        if response.status_code == 200:
            print(f"{user_type.capitalize()} user {user_id} updated successfully.")
        else:
            print(f"Failed to update {user_type} user {user_id}: {response.json()}")
    except requests.JSONDecodeError:
        print(f"Non-JSON response received during update for {user_type} user {user_id}")
    time.sleep(random.uniform(1, 2))

def logout_user(user_type, user_id):
    """Log out a user."""
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    print(f"Logging out {user_type} user {user_id}...")
    response = requests.post(f"{BASE_URL}/logout/", headers=headers)
    if response.status_code == 200:
        print(f"{user_type.capitalize()} user {user_id} logged out successfully.")
    else:
        print(f"Failed to log out {user_type} user {user_id}: {response.json()}")
    time.sleep(random.uniform(1, 2))

def delete_user(user_type, user_id):
    """Delete user after a set time to simulate user account deletion."""
    username = f"{user_type}_user_{user_id}"
    headers = {"Authorization": f"Bearer {tokens.get(username, {}).get('access')}"}
    print(f"Deleting {user_type} user {user_id}...")
    response = requests.delete(f"{BASE_URL}/user/", headers=headers)
    if response.status_code == 204:
        print(f"{user_type.capitalize()} user {user_id} deleted successfully.")
        user_data["users"].pop(username, None)
        user_data["tokens"].pop(username, None)
        save_user_data(user_data)
    else:
        print(f"Failed to delete {user_type} user {user_id}: {response.json()}")
    time.sleep(random.uniform(1, 2))

def simulate_user_activity(user_type, user_id):
    """Simulate the entire lifecycle of a user type."""
    create_user(user_type, user_id)
    login_user(user_type, user_id)
    get_user_data(user_type, user_id)
    update_user(user_type, user_id)
    get_user_data(user_type, user_id)
    logout_user(user_type, user_id)

    # Simulate delay before deletion
    delete_after = datetime.now() + timedelta(seconds=random.randint(10, 20))
    while datetime.now() < delete_after:
        time.sleep(1)
    delete_user(user_type, user_id)

if __name__ == "__main__":
    # Simulate traffic for multiple users of each type
    num_users_per_type = 3  # Number of users to simulate per user type
    for user_type in user_template.keys():
        for user_id in range(1, num_users_per_type + 1):
            simulate_user_activity(user_type, user_id)
            time.sleep(random.uniform(2, 5))  # Delay between each user to simulate real network requests
