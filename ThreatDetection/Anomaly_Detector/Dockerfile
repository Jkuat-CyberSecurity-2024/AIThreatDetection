FROM python:3.12.4-slim

WORKDIR /app

# Install necessary packages
RUN pip install pandas scikit-learn joblib

# Copy your anomaly detection script into the container
COPY anomaly_detection.py /app/anomaly_detection.py

# Set environment variables (optional)
ENV MODEL_PATH=/app/iso_forest_model.pkl
ENV SCALER_PATH=/app/scaler.pkl
ENV LOG_FILE_PATH=/var/log/nginx/access.log
ENV ANOMALY_LOG_PATH=/app/anomaly_feedback.json

# Start the anomaly detection script
CMD ["python", "anomaly_detection.py"]