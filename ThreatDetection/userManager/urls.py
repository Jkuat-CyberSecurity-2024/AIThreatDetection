from django.urls import path,include
from .views import confirm_email, email_confirmation_done
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from .views import (
    CustomUserViewSet, PatientViewSet, 
    ProviderViewSet, AdminViewSet, EmergencyContactViewSet
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'Patients', PatientViewSet)
router.register(r'Providers', ProviderViewSet)
# router.register(r'departments', DepartmentViewSet)
router.register(r'admins', AdminViewSet)
router.register(r'emergency-contacts', EmergencyContactViewSet, basename='emergencycontact')


urlpatterns = [
    path('', include(router.urls)),
    path('register/account-confirm-email/<str:key>/', confirm_email, name='account_confirm_email'),
    path('email-confirmation-done/', email_confirmation_done, name='email_confirmation_done'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
