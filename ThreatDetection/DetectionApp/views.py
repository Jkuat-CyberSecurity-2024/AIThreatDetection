from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse, HttpResponse
from django.views import View
import csv
import json
import os
from .models import ThreatData
from .serializers import ThreatDataSerializer
# Define paths
CSV_FILE_PATH = r'C:\Users\karan\OneDrive\Documents\GitHub\AIThreatDetection\ThreatDetection\detected_anomalies.csv'
FEEDBACK_FILE_PATH = r'C:\Users\karan\OneDrive\Documents\GitHub\AIThreatDetection\ThreatDetection\anomaly_feedback.json'


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
        queryset = ThreatData.objects.filter(processed=processed) if processed is not None else ThreatData.objects.all()
        return queryset


def load_anomalies(feedback_file):
    """Load anomalies from JSON feedback file."""
    try:
        with open(feedback_file, "r") as f:
            anomalies = [json.loads(line) for line in f]
        # Use dictionary comprehension for faster lookups
        return {anomaly['ip_address']: anomaly for anomaly in anomalies if 'ip_address' in anomaly}
    except FileNotFoundError:
        return {}


def check_for_anomaly(log_entry, anomalies):
    """Check if a log entry has an anomaly."""
    ip_address = log_entry.get('ip_address')
    return ip_address in anomalies if ip_address else False


def access_logs_view(request):
    """Display access logs with anomalies marked."""
    access_logs = []
    anomalies = load_anomalies(FEEDBACK_FILE_PATH)

    try:
        with open(CSV_FILE_PATH, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Flag anomaly if IP matches
                row['anomaly'] = check_for_anomaly(row, anomalies)
                access_logs.append(row)
    except FileNotFoundError:
        return HttpResponse("Access logs file not found.", status=404)

    return render(request, 'access_logs.html', {'access_logs': access_logs, 'anomalies': anomalies})


class ReviewAnomaliesView(View):
    template_name = 'review_anomalies.html'

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
            # Only update if anomaly has not been reviewed
            if not anomaly.get("reviewed", False):
                feedback = feedback_data.get(ip)
                if feedback in ["true_positive", "false_positive"]:
                    anomaly["feedback"] = feedback
                    anomaly["reviewed"] = True
            updated_entries.append(anomaly)

        # Write back updated anomalies
        with open(FEEDBACK_FILE_PATH, "w") as f:
            for entry in updated_entries:
                json.dump(entry, f)
                f.write("\n")

        return JsonResponse({'message': 'All anomalies reviewed successfully.'})
