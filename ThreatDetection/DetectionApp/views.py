from django.shortcuts import render

# Create your views here.

# detection views

from rest_framework import viewsets
from .models import ThreatData
from .serializers import ThreatDataSerializer

class ThreatDataViewSet(viewsets.ModelViewSet):
    queryset = ThreatData.objects.all()
    serializer_class = ThreatDataSerializer
