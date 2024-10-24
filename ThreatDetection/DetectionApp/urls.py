# detection/urls.py

from rest_framework.routers import DefaultRouter
from .views import ThreatDataViewSet

router = DefaultRouter()
router.register(r'threats', ThreatDataViewSet)

urlpatterns = router.urls
