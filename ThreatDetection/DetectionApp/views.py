# detection/views.py

from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ThreatData
from .serializers import ThreatDataSerializer
from django.http import JsonResponse
from django.views import View
from django.http import HttpResponse
import csv
import json
import os

class ThreatDataViewSet(viewsets.ModelViewSet):
    queryset = ThreatData.objects.all()
    serializer_class = ThreatDataSerializer

    # Adding search and filtering options
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'source_ip']
    ordering_fields = ['timestamp', 'threat_level']

    # Custom action to mark a threat as processed
    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        threat = self.get_object()
        threat.processed = True
        threat.save()
        return Response({'status': 'threat marked as processed'})

    # Filtering unprocessed threats
    def get_queryset(self):
        queryset = ThreatData.objects.all()
        processed = self.request.query_params.get('processed')
        if processed is not None:
            queryset = queryset.filter(processed=processed)
        return queryset
    

CSV_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\access_logs.csv'
FEEDBACK_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\anomaly_feedback.json'

def access_logs_view(request):
    access_logs = []
    anomalies = load_anomalies(FEEDBACK_FILE_PATH)  # Load anomalies from feedback file

    # Read access logs from the CSV file
    try:
        with open(CSV_FILE_PATH, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Check if the row has the expected structure, especially 'ip_address'
                row['anomaly'] = check_for_anomaly(row, anomalies)  # Determine if it's an anomaly
                access_logs.append(row)
    except FileNotFoundError:
        return HttpResponse("Access logs file not found.", status=404)

    # Render access logs to the HTML table instead of printing
    return render(request, 'access_logs.html', {'access_logs': access_logs, 'anomalies': anomalies})

def check_for_anomaly(log_entry, anomalies):
    """Custom logic to determine if a log entry is an anomaly."""
    ip_address = log_entry.get('ip_address')  # Use .get() to avoid KeyError
    if not ip_address:  # Check if ip_address is empty or None
        return False  # Handle missing IP address appropriately

    # Check if the IP address is present in the anomalies list
    return any(anomaly.get('ip_address') == ip_address for anomaly in anomalies)

def load_anomalies(feedback_file):
    """Load anomalies from the feedback file."""
    anomalies = []
    try:
        with open(feedback_file, "r") as f:
            anomalies = [json.loads(line) for line in f.readlines()]
    except FileNotFoundError:
        return anomalies  # Return empty if file not found
    return anomalies

class ReviewAnomaliesView(View):
    template_name = 'review_anomalies.html'

    def get(self, request):
        anomalies = self.load_anomalies(FEEDBACK_FILE_PATH)
        return render(request, self.template_name, {'anomalies': anomalies})

    def post(self, request):
        feedback_data = json.loads(request.body)
        self.review_anomalies(feedback_data, FEEDBACK_FILE_PATH)
        return JsonResponse({'message': 'All anomalies reviewed successfully.'})

    def load_anomalies(self, feedback_file):
        """Load existing anomalies from the feedback file."""
        anomalies = []
        try:
            with open(feedback_file, "r") as f:
                anomalies = [json.loads(line) for line in f.readlines()]
        except FileNotFoundError:
            return anomalies  # Return empty if file not found
        return anomalies

    def review_anomalies(self, feedback_data, feedback_file):
        """Review anomalies based on user feedback."""
        updated_entries = []
        anomalies = self.load_anomalies(feedback_file)

        for anomaly in anomalies:
            if anomaly.get("reviewed", False):
                updated_entries.append(anomaly)
                continue

            feedback = feedback_data.get(anomaly['ip_address'])
            if feedback in ["true_positive", "false_positive"]:
                anomaly["feedback"] = feedback
                anomaly["reviewed"] = True
                updated_entries.append(anomaly)

        # Write updated entries back to the file
        with open(feedback_file, "w") as f:
            for entry in updated_entries:
                json.dump(entry, f)
                f.write("\n")




# # Specify the full paths for the files
# CSV_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\access_logs.csv'
# FEEDBACK_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\anomaly_feedback.json'

# def access_logs_view(request):
#     access_logs = []
#     anomalies = load_anomalies(FEEDBACK_FILE_PATH)  # Load anomalies from feedback file

#     # Read access logs from the CSV file
#     try:
#         with open(CSV_FILE_PATH, 'r') as file:
#             reader = csv.DictReader(file)
#             for row in reader:
#                 print(f"Row data: {row}")  # Debug print to see row contents
#                 row['anomaly'] = check_for_anomaly(row, anomalies)
#                 access_logs.append(row)
#     except FileNotFoundError:
#         return HttpResponse("Access logs file not found.", status=404)

#     return render(request, 'access_logs.html', {'access_logs': access_logs, 'anomalies': anomalies})

# def check_for_anomaly(log_entry, anomalies):
#     """Custom logic to determine if a log entry is an anomaly."""
#     ip_address = log_entry.get('ip_address')  # Use .get() to avoid KeyError
#     if ip_address is None:
#         print("Warning: 'ip_address' not found in log entry.")  # Debug warning
#         return False  # Or however you want to handle it

#     # Check if the IP address is present in the anomalies list
#     return any(anomaly.get('ip_address') == ip_address for anomaly in anomalies)

# def load_anomalies(feedback_file):
#     """Load anomalies from the feedback file."""
#     anomalies = []
#     try:
#         with open(feedback_file, "r") as f:
#             anomalies = [json.loads(line) for line in f.readlines()]
#     except FileNotFoundError:
#         return anomalies  # Return empty if file not found
#     return anomalies

# class ReviewAnomaliesView(View):
#     template_name = 'review_anomalies.html'

#     def get(self, request):
#         anomalies = self.load_anomalies(FEEDBACK_FILE_PATH)
#         return render(request, self.template_name, {'anomalies': anomalies})

#     def post(self, request):
#         feedback_data = json.loads(request.body)
#         self.review_anomalies(feedback_data, FEEDBACK_FILE_PATH)
#         return JsonResponse({'message': 'All anomalies reviewed successfully.'})

#     def load_anomalies(self, feedback_file):
#         """Load existing anomalies from the feedback file."""
#         anomalies = []
#         try:
#             with open(feedback_file, "r") as f:
#                 anomalies = [json.loads(line) for line in f.readlines()]
#         except FileNotFoundError:
#             return anomalies  # Return empty if file not found
#         return anomalies

#     def review_anomalies(self, feedback_data, feedback_file):
#         """Review anomalies based on user feedback."""
#         updated_entries = []
#         anomalies = self.load_anomalies(feedback_file)

#         for anomaly in anomalies:
#             if anomaly.get("reviewed", False):
#                 updated_entries.append(anomaly)
#                 continue

#             feedback = feedback_data.get(anomaly['ip_address'])
#             if feedback in ["true_positive", "false_positive"]:
#                 anomaly["feedback"] = feedback
#                 anomaly["reviewed"] = True
#                 updated_entries.append(anomaly)

#         # Write updated entries back to the file
#         with open(feedback_file, "w") as f:
#             for entry in updated_entries:
#                 json.dump(entry, f)
#                 f.write("\n")

#         print("\nAll anomalies reviewed.")



# # Specify the full paths for the files
# CSV_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\access_logs.csv'
# FEEDBACK_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\anomaly_feedback.json'

# def access_logs_view(request):
#     access_logs = []
#     anomalies = load_anomalies(FEEDBACK_FILE_PATH)  # Load anomalies from feedback file

#     # Read access logs from the CSV file
#     try:
#         with open(CSV_FILE_PATH, 'r') as file:
#             reader = csv.DictReader(file)
#             for row in reader:
#                 print(f"Row data: {row}")  # Debug print to see row contents
#                 row['anomaly'] = check_for_anomaly(row, anomalies)
#                 access_logs.append(row)
#     except FileNotFoundError:
#         return HttpResponse("Access logs file not found.", status=404)

#     return render(request, 'access_logs.html', {'access_logs': access_logs, 'anomalies': anomalies})

# def check_for_anomaly(log_entry, anomalies):
#     """Custom logic to determine if a log entry is an anomaly."""
#     ip_address = log_entry.get('ip_address')  # Use .get() to avoid KeyError
#     if ip_address is None:
#         print("Warning: 'ip_address' not found in log entry.")  # Debug warning
#         return False  # Or however you want to handle it

#     # Check if the IP address is present in the anomalies list
#     return any(anomaly.get('ip_address') == ip_address for anomaly in anomalies)

# def load_anomalies(feedback_file):
#     """Load anomalies from the feedback file."""
#     anomalies = []
#     try:
#         with open(feedback_file, "r") as f:
#             anomalies = [json.loads(line) for line in f.readlines()]
#     except FileNotFoundError:
#         return anomalies  # Return empty if file not found
#     return anomalies

# class ReviewAnomaliesView(View):
#     template_name = 'review_anomalies.html'

#     def get(self, request):
#         anomalies = self.load_anomalies(FEEDBACK_FILE_PATH)
#         return render(request, self.template_name, {'anomalies': anomalies})

#     def post(self, request):
#         feedback_data = json.loads(request.body)
#         self.review_anomalies(feedback_data, FEEDBACK_FILE_PATH)
#         return JsonResponse({'message': 'All anomalies reviewed successfully.'})

#     def load_anomalies(self, feedback_file):
#         """Load existing anomalies from the feedback file."""
#         anomalies = []
#         try:
#             with open(feedback_file, "r") as f:
#                 anomalies = [json.loads(line) for line in f.readlines()]
#         except FileNotFoundError:
#             return anomalies  # Return empty if file not found
#         return anomalies

#     def review_anomalies(self, feedback_data, feedback_file):
#         """Review anomalies based on user feedback."""
#         updated_entries = []
#         anomalies = self.load_anomalies(feedback_file)

#         for anomaly in anomalies:
#             if anomaly.get("reviewed", False):
#                 updated_entries.append(anomaly)
#                 continue

#             feedback = feedback_data.get(anomaly['ip_address'])
#             if feedback in ["true_positive", "false_positive"]:
#                 anomaly["feedback"] = feedback
#                 anomaly["reviewed"] = True
#                 updated_entries.append(anomaly)

#         # Write updated entries back to the file
#         with open(feedback_file, "w") as f:
#             for entry in updated_entries:
#                 json.dump(entry, f)
#                 f.write("\n")

#         print("\nAll anomalies reviewed.")