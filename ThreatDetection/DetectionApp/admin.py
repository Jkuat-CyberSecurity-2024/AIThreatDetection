from django.contrib import admin

# Register your models here.
# detection/admin.py

from django.contrib import admin
from .models import ThreatData

# Register the ThreatData model
@admin.register(ThreatData)
class ThreatDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'threat_level', 'description', 'source_ip', 'processed')
    search_fields = ('description', 'source_ip')
    list_filter = ('threat_level', 'processed')
