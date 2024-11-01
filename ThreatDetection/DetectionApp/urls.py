# detection/urls.py
from django.urls import path
from .views import access_logs_view, ReviewAnomaliesView
from rest_framework.routers import DefaultRouter
from .views import ThreatDataViewSet

router = DefaultRouter()
router.register(r'threats', ThreatDataViewSet)

urlpatterns = router.urls

urlpatterns = [
    path('access-logs/', access_logs_view, name='access_logs'),
    path('review-anomalies/', ReviewAnomaliesView.as_view(), name='review_anomalies'),
]
