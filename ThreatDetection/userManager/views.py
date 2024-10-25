from django.shortcuts import render, redirect
from django.urls import reverse
from allauth.account.models import EmailConfirmationHMAC, EmailConfirmation
from rest_framework import viewsets, status, permissions
from .models import CustomUser, Patient, Provider, Admin ,EmergencyContact
from .serializers import (
    CustomUserSerializer, PatientSerializer, 
    ProviderSerializer, AdminSerializer,
    PatientSummarySerializer,ProviderSummarySerializer,
    AdminSummarySerializer,EmergencyContactSerializer
)
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .permissions import CustomUserPermission
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

def confirm_email(request, key):
    """
    View to handle email confirmation from a unique key.
    
    If the key is valid and the confirmation is successful,
    the user is redirected to the 'email_confirmation_done' page.
    """
    try:
        confirmation = EmailConfirmationHMAC.from_key(key)
        if confirmation:
            confirmation.confirm(request)
            return redirect(reverse('email_confirmation_done'))
    except EmailConfirmation.DoesNotExist:
        pass

    return render(request, 'account/confirm_email.html', {'key': key})

def email_confirmation_done(request):
    """
    View to render a success page after email confirmation.
    """
    return render(request, 'account/email_confirmation_done.html')


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    API viewset for viewing and editing CustomUser instances.
    
    Provides GET, HEAD, and OPTIONS methods.
    Users can view their own information.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    http_method_names = ['get', 'head', 'options']

    def get_object(self):
        """
        Returns the CustomUser object of the currently authenticated user.
        """
        return CustomUser.objects.get(id=self.request.user.id)


class PatientViewSet(viewsets.ModelViewSet):
    """
    API viewset for viewing and editing Patient instances.
    
    Provides methods to retrieve and update Patient user details.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']  # Include PATCH method

    def get_queryset(self):
        """
        Filters the Patient queryset based on the user type.
        If the user is a provider, return all patient objects.
        Otherwise, return only the currently authenticated patient's object.
        """
        user = self.request.user

        if user.user_type == 'provider':
            # If the user is a provider, return all patients
            return Patient.objects.all()
        else:
            # If the user is a patient, return only their own data
            return Patient.objects.filter(id=user.id)


    def get_object(self):
        """
        Returns the Patient object of the currently authenticated user.
        If the user is a provider, an exception is raised.
        """
        user = self.request.user

        if user.user_type == 'provider':
            # Optionally, you could raise an error or return something specific for providers
            raise ValidationError("Providers cannot retrieve a specific patient's object.")
        else:
            # Return the currently authenticated patient's object
            return Patient.objects.get(id=user.id)



    def update(self, request, *args, **kwargs):
        """
        Updates the Patient instance for the authenticated user.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially updates the Patient instance for the authenticated user.
        """
        return self.update(request, *args, partial=True, **kwargs)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Custom endpoint to return Patients without the related items.
        """
        Patients = Patient.objects.all()
        serializer = PatientSummarySerializer(Patients, many=True)
        return Response(serializer.data)

class ProviderViewSet(viewsets.ModelViewSet):
    """
    API viewset for viewing and editing Provider instances.
    
    Provides methods to retrieve and update Provider user details.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomUserPermission]
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']  # Include PATCH method

    def get_queryset(self):
        """
        Filters the Provider queryset to the currently authenticated user.
        """
        return Provider.objects.filter(id=self.request.user.id)

    def get_object(self):
        """
        Returns the Provider object of the currently authenticated user.
        """
        return Provider.objects.get(id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        """
        Updates the Provider instance for the authenticated user.
        """
        Provider = self.get_object()
        serializer = self.get_serializer(Provider, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially updates the Provider instance for the authenticated user.
        """
        Provider = self.get_object()
        serializer = self.get_serializer(Provider, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Custom endpoint to return Providers without the related items.
        """
        Providers = Provider.objects.all()
        serializer = ProviderSummarySerializer(Providers, many=True)
        return Response(serializer.data)
class AdminViewSet(viewsets.ModelViewSet):
    """
    API viewset for viewing and editing Admin instances.
    
    Provides methods to retrieve and update admin user details.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomUserPermission]
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']  # Include PATCH method

    def get_queryset(self):
        """
        Filters the Admin queryset to the currently authenticated user.
        """
        return Admin.objects.filter(id=self.request.user.id)

    def get_object(self):
        """
        Returns the Admin object of the currently authenticated user.
        """
        return Admin.objects.get(id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        """
        Updates the admin instance for the authenticated user.
        """
        admin = self.get_object()
        serializer = self.get_serializer(admin, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially updates the admin instance for the authenticated user.
        """
        admin = self.get_object()
        serializer = self.get_serializer(admin, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Custom endpoint to return admins without the related items.
        """
        admins = Admin.objects.all()
        serializer = AdminSummarySerializer(admins, many=True)
        return Response(serializer.data)
class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow users to modify their own emergency contacts.
    """
    def has_object_permission(self, request, view, obj):
        # Ensure the authenticated user is an Patient
        if request.user.user_type != 'patient':
            return False

        # Compare the IDs of the Patient and the authenticated user
        return obj.Patient_id == request.user.id


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions for EmergencyContact.
    Only authenticated users can access it, and users can only modify their own contacts.
    """
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Override get_queryset to return only the contacts for the authenticated user.
        The authenticated user can only see their own emergency contacts.
        """
        user = self.request.user
        # Return the emergency contacts for the authenticated Patient
        return EmergencyContact.objects.filter(Patient=user)

    def perform_create(self, serializer):
        """
        Override perform_create to ensure the authenticated user is an Patient
        before assigning them as the owner of the emergency contact.
        """
        user = self.request.user

        # Check if the user is of type 'Patient' using the user_type field
        if user.user_type == 'patient':
            try:
                # Cast the user to the Patient model
                Patient_user = Patient.objects.get(pk=user.pk)
                serializer.save(Patient=Patient_user)
            except Patient.DoesNotExist:
                raise ValidationError({"detail": "Only Patient users can create emergency contacts."})
        else:
            raise ValidationError({"detail": "Only Patient users can create emergency contacts."})
