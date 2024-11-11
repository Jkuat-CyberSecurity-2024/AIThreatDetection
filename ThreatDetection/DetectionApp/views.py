from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
import csv
import json
from .models import ThreatData
from .serializers import ThreatDataSerializer
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
import os

# Define paths
CSV_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\detected_anomalies.csv'
FEEDBACK_FILE_PATH = r'D:\Attacho\Hackathon\Cybertec\AIThreatDetection\ThreatDetection\anomaly_feedback.json'

# ThreatData ViewSet
class ThreatDataViewSet(viewsets.ModelViewSet):
    queryset = ThreatData.objects.all()
    serializer_class = ThreatDataSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'source_ip']
    ordering_fields = ['timestamp', 'threat_level']

    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        threat = self.get_object()
        threat.processed = True
        threat.save()
        return Response({'status': 'threat marked as processed'})

    def get_queryset(self):
        processed = self.request.query_params.get('processed')
        if processed is not None:
            return ThreatData.objects.filter(processed=processed)
        return ThreatData.objects.all()

# Utility function to load anomalies
def load_anomalies(feedback_file):
    """Load anomalies from JSON feedback file."""
    anomalies = {}
    try:
        with open(feedback_file, "r") as f:
            for line in f:
                anomaly = json.loads(line)
                if 'ip_address' in anomaly:
                    anomalies[anomaly['ip_address']] = anomaly
    except FileNotFoundError:
        print(f"Feedback file not found: {feedback_file}")
    return anomalies

# Utility function to check for anomalies in logs
def check_for_anomaly(log_entry, anomalies):
    """Check if a log entry has an anomaly."""
    ip_address = log_entry.get('ip_address')
    return ip_address in anomalies if ip_address else False

# View for reviewing anomalies
class ReviewAnomaliesView(View):
    template_name = 'dashboard/anomalies.html'

    def get(self, request):
        """Display anomalies for review."""
        anomalies = load_anomalies(FEEDBACK_FILE_PATH)
        return render(request, self.template_name, {'anomalies': anomalies.values()})

    def post(self, request):
        """Post feedback for anomalies, updating them as reviewed."""
        feedback_data = json.loads(request.body)
        anomalies = load_anomalies(FEEDBACK_FILE_PATH)
        updated_entries = []

        for ip, anomaly in anomalies.items():
            if not anomaly.get("reviewed", False):
                feedback = feedback_data.get(ip)
                if feedback in ["true_positive", "false_positive"]:
                    anomaly["feedback"] = feedback
                    anomaly["reviewed"] = True
            updated_entries.append(anomaly)

        with open(FEEDBACK_FILE_PATH, "w") as f:
            for entry in updated_entries:
                json.dump(entry, f)
                f.write("\n")

        return JsonResponse({'message': 'All anomalies reviewed successfully.'})

# View for accessing logs
def access_logs_view(request):
    """Display access logs with anomalies marked."""
    access_logs = []
    anomalies = load_anomalies(FEEDBACK_FILE_PATH)

    try:
        with open(CSV_FILE_PATH, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['anomaly'] = check_for_anomaly(row, anomalies)
                access_logs.append(row)
    except FileNotFoundError:
        return HttpResponse("Access logs file not found.", status=404)

    return render(request, 'dashboard/logs.html', {'access_logs': access_logs, 'anomalies': anomalies})

# View for generating reports
def report_view(request):
    return render(request, 'dashboard/report.html')

# View for data visualization
def visualization_view(request):
    return render(request, 'dashboard/visualization.html')

def daily_report_view(request):
    # Logic for the daily report
    return render(request, 'reports/daily_report.html')

def weekly_report_view(request):
    # Logic for the weekly report
    return render(request, 'reports/weekly_report.html')

def monthly_report_view(request):
    # Logic for the monthly report
    return render(request, 'reports/monthly_report.html')