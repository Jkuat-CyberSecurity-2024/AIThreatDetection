# detection serializers

from rest_framework import serializers
from .models import ThreatData

class ThreatDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatData
        fields = '__all__'
