import os
import re
import pandas as pd
import time
import json
import joblib
import subprocess
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.exceptions import NotFittedError
import signal
import sys

# Load paths from environment variables for flexibility
MODEL_PATH = os.getenv("MODEL_PATH", "iso_forest_model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "scaler.pkl")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/var/log/nginx/access.log")
ANOMALY_LOG_PATH = os.getenv("ANOMALY_LOG_PATH", "anomaly_feedback.json")
HISTORICAL_DATA_PATH = os.getenv("HISTORICAL_DATA_PATH", "access_logs.csv")

# Initialize model and scaler
iso_forest = None
scaler = None

# Log pattern to parse the NGINX logs
log_pattern = re.compile(
    r'(?P<IP_Address>\S+) - \[(?P<Timestamp>[^\]]+)\] "(?P<Method>\S+) (?P<Resource>\S+) (?P<Protocol>[^\"]+)" '
    r'(?P<Status_Code>\d+) (?P<Bytes_Sent>\d+) "(?P<Referrer>[^\"]*)" "(?P<User_Agent>[^\"]*)" '
    r'(?P<Source_Port>\d+) (?P<Destination_Port>\d+) - "(?P<Origin_Server>[^\"]*)" "(?P<Destination>[^\"]*)" '
    r'"(?P<Response_Code>[^\"]*)" "(?P<Response_Time>[\d.,]*)" (?P<Backend_Time>[\d.,]*)'
)

# Function to preprocess log data
def preprocess_data(data):
    label_encoders = {}
    categorical_columns = ['IP_Address', 'Method', 'Resource', 'User Agent']
    for col in categorical_columns:
        if col in data.columns:
            le = LabelEncoder()
            data[col] = data[col].fillna('Missing')
            data[col] = le.fit_transform(data[col])
            label_encoders[col] = le
        else:
            print(f"Warning: Column '{col}' not found in the dataset.")

    # Convert timestamp to datetime and extract hour, day, weekday
    if 'Timestamp' in data.columns:
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce', format='%d/%b/%Y:%H:%M:%S %z')
        data['Hour'] = data['Timestamp'].dt.hour
        data['Day'] = data['Timestamp'].dt.day
        data['Weekday'] = data['Timestamp'].dt.weekday
        data = data.drop(columns=['Timestamp'], errors='ignore')

    # Drop unnecessary columns
    data = data.drop(columns=['Referrer', 'Origin Server', 'Protocol'], errors='ignore')

    # Convert numeric columns to numeric types and handle missing values
    numerical_columns = ['Bytes Sent', 'Source Port', 'Destination Port', 'Response Time (seconds)', 
                         'Backend Time (seconds)', 'Hour', 'Day', 'Weekday']
    data[numerical_columns] = data[numerical_columns].apply(pd.to_numeric, errors='coerce')
    data[numerical_columns] = data[numerical_columns].fillna(data[numerical_columns].median())

    # Normalize numerical features if scaler is fitted
    try:
        data[numerical_columns] = pd.DataFrame(
            scaler.transform(data[numerical_columns]), columns=numerical_columns
        )
    except NotFittedError:
        data[numerical_columns] = pd.DataFrame(
            scaler.fit_transform(data[numerical_columns]), columns=numerical_columns
        )

    return data[numerical_columns]

# Load or initialize model and scaler
def load_or_initialize_model():
    global iso_forest, scaler
    if Path(MODEL_PATH).exists() and Path(SCALER_PATH).exists():
        iso_forest = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print("Loaded existing model and scaler.")
    else:
        iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        scaler = StandardScaler()
        print("Initializing new model and scaler.")
        if Path(HISTORICAL_DATA_PATH).exists():
            historical_data = pd.read_csv(HISTORICAL_DATA_PATH)
            train_model(historical_data)

# Function to train the model and save it
def train_model(data):
    X = preprocess_data(data)
    iso_forest.fit(X)
    joblib.dump(iso_forest, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("Model trained and saved.")

# Real-time monitoring of NGINX logs
def monitor_nginx_logs():
    with open(LOG_FILE_PATH, 'r') as f:
        f.seek(0, 2)  # Move to the end of the file
        while True:
            line = f.readline()
            if line:
                process_log_entry(line)
            else:
                time.sleep(1)

# Process individual log entries and detect anomalies
def process_log_entry(log_entry):
    match = log_pattern.match(log_entry)
    if not match:
        print(f"Failed to parse log entry: {log_entry}")
        return

    parsed_data = match.groupdict()
    parsed_data['Timestamp'] = datetime.strptime(parsed_data['Timestamp'], "%d/%b/%Y:%H:%M:%S %z")

    df = pd.DataFrame([{
        'IP_Address': parsed_data['IP_Address'],
        'Method': parsed_data['Method'],
        'Resource': parsed_data['Resource'],
        'Bytes Sent': float(parsed_data['Bytes_Sent']),
        'Source Port': int(parsed_data['Source_Port']),
        'Destination Port': int(parsed_data['Destination_Port']),
        'Response Time (seconds)': float(parsed_data['Response_Time']) if parsed_data['Response_Time'] else 0.0,
        'Backend Time (seconds)': float(parsed_data['Backend_Time']) if parsed_data['Backend_Time'] else 0.0,
        'User Agent': parsed_data['User_Agent'],
        'Hour': parsed_data['Timestamp'].hour,
        'Day': parsed_data['Timestamp'].day,
        'Weekday': parsed_data['Timestamp'].weekday()
    }])

    processed_df = preprocess_data(df)
    prediction = iso_forest.predict(processed_df)

    if prediction[0] == -1:
        print(f"Anomaly detected for IP: {parsed_data['IP_Address']}")
        log_anomaly_for_review(parsed_data['IP_Address'], df)

# Log anomalies for review
def log_anomaly_for_review(ip_address, anomaly_data):
    feedback_entry = {
        "ip_address": ip_address,
        "timestamp": datetime.now().isoformat(),
        "anomaly_data": anomaly_data.to_dict(orient="records")[0],
        "reviewed": False,
        "feedback": None
    }
    with open(ANOMALY_LOG_PATH, "a") as feedback_file:
        json.dump(feedback_entry, feedback_file)
        feedback_file.write("\n")
    print(f"Anomaly for IP {ip_address} logged.")

# IP Blocking (optional)
def block_ip(ip_address):
    try:
        subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip_address, "-j", "DROP"], check=True)
        subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
        print(f"Blocked IP: {ip_address}")
    except subprocess.CalledProcessError as e:
        print(f"Error blocking IP {ip_address}: {e}")

# Handle graceful shutdown
def handle_shutdown_signal(signal, frame):
    print("Shutting down gracefully...")
    sys.exit(0)

# Main execution
if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    print("Starting anomaly detection system...")
    load_or_initialize_model()
    monitor_nginx_logs()
