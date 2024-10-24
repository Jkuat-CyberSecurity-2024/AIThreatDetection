# detection/views.py

from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ThreatData
from .serializers import ThreatDataSerializer

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
