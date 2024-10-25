from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account.utils import setup_user_email
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CustomUser, Patient, Provider, Admin, EmergencyContact
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()
class CustomRegisterSerializer(RegisterSerializer):
    """
    Custom serializer for handling user registration.
    Handles the additional fields specific to each user type (Patient, Provider, Admin).
    """
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)
    admin_code = serializers.CharField(required=False, allow_blank=True)
    parent_Provider_id = serializers.IntegerField(required=False)
    Provider_name = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    # New Patient-specific fields
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=Patient.GENDER_CHOICES, required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    
    def get_cleaned_data(self):
        """
        Retrieve cleaned data from the request, including additional custom fields.
        """
        data = super().get_cleaned_data()
        data['user_type'] = self.validated_data.get('user_type', '')
        data['email'] = self.validated_data.get('email', '')
        data['username'] = self.validated_data.get('username', self.generate_username_from_email(data['email']))
        data['date_of_birth'] = self.validated_data.get('date_of_birth', None)
        data['gender'] = self.validated_data.get('gender', '')
        data['location'] = self.validated_data.get('location', '')
        return data

    def generate_username_from_email(self, email):
        """
        Generate a username from the email if a username is not provided.
        """
        return email.split('@')[0]

    def validate_email(self, email):
        """
        Check if the email already exists in the system.
        """
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return email

    def save(self, request):
        """
        Override the save method to create different user types based on request data.
        """
        adapter = get_adapter()
        self.cleaned_data = self.get_cleaned_data()

        # Retrieve additional fields from the request
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        Provider_name = request.data.get('Provider_name', '')
        location = self.cleaned_data.get('location', 'N/A')
        status = request.data.get('status', '')
        address = request.data.get('address', '')
        gender = self.cleaned_data.get('gender', 'male')  # Default gender if not provided
        date_of_birth = self.cleaned_data.get('date_of_birth', None)

        # Validate email before saving
        self.validate_email(self.cleaned_data['email'])

        # Start transaction for atomic save operation
        with transaction.atomic():
            user_type = self.cleaned_data['user_type']
            username = self.cleaned_data['username']
            email = self.cleaned_data['email']

            if user_type == 'patient':
                user = Patient.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=date_of_birth,
                    gender=gender,
                    location=location,
                )
            elif user_type == 'provider':
                Provider_name = Provider_name or first_name  # Use Provider_name or fallback to first_name
                user = Provider.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    Provider_name=Provider_name,
                    address=address,
                    verified=False,
                    location=location,
                    status=status,
                )
            elif user_type == 'admin':
                user = Admin.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    is_superuser=True,
                    is_staff=True,
                    is_admin=True,
                )

            # Save the user via the adapter and complete the registration process
            user = adapter.save_user(request, user, self, commit=False)
            user.user_type = user_type
            user.save()

            self.custom_signup(request, user)
            setup_user_email(request, user, [])

            return user



class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model. Handles the full serialization of all user data, including the email verification status.
    """
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = '__all__'
        extra_kwargs = {
            'password': {'required': False, 'write_only': True},
        }

    def get_email_verified(self, obj):
        """
        Check if the user's primary email has been verified.

        Args:
            obj (CustomUser): The user object.

        Returns:
            bool: True if the email is verified, False otherwise.
        """
        try:
            email_address = EmailAddress.objects.get(user=obj, primary=True)
            return email_address.verified
        except EmailAddress.DoesNotExist:
            return False


class EmergencyContactSerializer(serializers.ModelSerializer):
    """
    Serializer for the EmergencyContact model.
    """

    class Meta:
        model = EmergencyContact
        fields = '__all__'
        read_only_fields = ['Patient']  # Make Patient read-only


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model, including emergency contact information.
    """
    emergency_contact = EmergencyContactSerializer(many=True)

    class Meta:
        model = Patient
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {'required': False},
            'username': {'required': False}
        }

    def create(self, validated_data):
        """
        Create a Patient instance using validated data.
        """
        return Patient.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update the Patient instance with validated data.
        """
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.contact_number = validated_data.get('contact_number', instance.contact_number)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.save()
        return instance


class ProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Provider model.
    """

    class Meta:
        model = Provider
        fields = '__all__'
        extra_kwargs = {
            'password': {'required': False, 'write_only': True},
        }


class AdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Admin model.
    """

    class Meta:
        model = Admin
        fields = '__all__'
        extra_kwargs = {
            'password': {'required': False, 'write_only': True},
        }


class PatientSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for the Patient model. Provides a concise overview with key fields.
    """

    class Meta:
        model = Patient
        fields = ['id', 'username', 'email', 'date_of_birth']


class ProviderSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for the Provider model. Provides a concise overview with key fields.
    """

    class Meta:
        model = Provider
        fields = ['id', 'username', 'email', 'Provider_name', 'location', 'verified', 'status',  'address', 'image', 'status']


class AdminSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for the Admin model. Provides a concise overview with key fields.
    """

    class Meta:
        model = Admin
        fields = ['id', 'username', 'email', 'admin_code']
