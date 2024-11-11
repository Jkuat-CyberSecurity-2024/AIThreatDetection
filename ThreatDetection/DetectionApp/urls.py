from django.urls import path
from . import views
from .views import (
    ReviewAnomaliesView, 
    access_logs_view, 
    report_view, 
    visualization_view,
    ThreatDataViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'threat-data', ThreatDataViewSet)

urlpatterns = [
    path('review-anomalies/', ReviewAnomaliesView.as_view(), name='review_anomalies'),
    path('access-logs/', access_logs_view, name='access_logs'),
    path('report/', report_view, name='report'),
    path('visualization/', visualization_view, name='visualization'),
    path('report/daily/', views.daily_report_view, name='daily_report'),
    path('report/weekly/', views.weekly_report_view, name='weekly_report'),
    path('report/monthly/', views.monthly_report_view, name='monthly_report'),
]

urlpatterns += router.urls
