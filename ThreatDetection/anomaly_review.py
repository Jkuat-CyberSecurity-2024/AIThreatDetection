import json

def review_anomalies(feedback_file="anomaly_feedback.json"):
    updated_entries = []
    
    # Load existing feedback entries
    with open(feedback_file, "r") as f:
        entries = f.readlines()

    # Review each entry
    for entry in entries:
        anomaly = json.loads(entry)
        
        # Skip already reviewed entries
        if anomaly["reviewed"]:
            updated_entries.append(anomaly)
            continue

        print(f"\nAnomaly detected for IP: {anomaly['ip_address']}")
        print("Anomaly details:", json.dumps(anomaly["anomaly_data"], indent=4))
        
        feedback = input("Is this a true positive? (yes/no): ").strip().lower()
        
        if feedback in ["yes", "y"]:
            anomaly["feedback"] = "true_positive"
        elif feedback in ["no", "n"]:
            anomaly["feedback"] = "false_positive"
        
        anomaly["reviewed"] = True
        updated_entries.append(anomaly)
    
    # Write updated entries back to the file
    with open(feedback_file, "w") as f:
        for entry in updated_entries:
            json.dump(entry, f)
            f.write("\n")

    print("\nAll anomalies reviewed.")

# Run the function if this script is executed directly
if __name__ == "__main__":
    review_anomalies()
