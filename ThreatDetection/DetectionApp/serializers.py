# detection/serializers.py

from rest_framework import serializers
from .models import ThreatData

class ThreatDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThreatData
        fields = '__all__'

    # Custom validation for the 'threat_level'
    def validate_threat_level(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Threat level must be between 0 and 10.")
        return value
