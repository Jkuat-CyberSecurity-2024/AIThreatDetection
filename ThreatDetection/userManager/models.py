from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.hashers import make_password
import uuid
import os
from PIL import Image
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError

def user_profile_image_path(instance, filename):
    """
    Generate a unique file path for user profile images.

    Args:
        instance (CustomUser): The instance of the user.
        filename (str): The original filename.

    Returns:
        str: A new file path for the uploaded image.
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.username}_{uuid.uuid4()}.{ext}"
    return os.path.join('users/', filename)

class CustomUser(AbstractUser):
    """
    Custom user model that extends the default Django AbstractUser to include additional fields
    and relationships necessary for a healthcare system.

    Attributes:
        image (ImageField): User profile image, with a default and the ability to upload custom images.
        user_type (CharField): Defines the role of the user in the system (e.g., patient, provider, admin).
        groups (ManyToManyField): Extends the default group system for permissions with a custom relationship.
        user_permissions (ManyToManyField): Custom relationship for managing user permissions.
        is_admin (BooleanField): Flag to identify if a user has admin privileges.
        id (UUIDField): Primary key for the user, using a UUID for security and scalability.
        contact_number (PhoneNumberField): Phone number of the user, ensuring unique entries in the database.
        email (EmailField): Email address for the user, enforced to be unique for every user.
    """
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('provider', 'Provider'),
        ('admin', 'Admin'),
    )
    image = models.ImageField(null=True, blank=True, default='res/default.png', upload_to=user_profile_image_path)
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='patient')
    groups = models.ManyToManyField(Group, related_name='customuser_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='customuser_permissions')
    is_admin = models.BooleanField(default=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact_number = PhoneNumberField(blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)  # Ensure uniqueness in the database

    def save(self, *args, **kwargs):
        """
        Override save method to ensure email uniqueness, hash passwords, and process profile images.

        Raises:
            ValidationError: If the email is already associated with another user.
        """
        # Check for email uniqueness manually
        if CustomUser.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError(f"A user with email {self.email} already exists.")

        # Hash password if not hashed already
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)

        # Process image (resize if necessary)
        if self.image:
            img = Image.open(self.image.path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.thumbnail((300, 300))
            img.save(self.image.path)

        # Call the parent save method
        super().save(*args, **kwargs)


class EmergencyContact(models.Model):
    """
    EmergencyContact model to store emergency contact information for patients.

    Attributes:
        name (CharField): Name of the emergency contact.
        phone_number (PhoneNumberField): Phone number of the contact.
        relationship (CharField): Defines the relationship between the patient and the contact.
        email (EmailField): Email address of the contact.
        Patient (ForeignKey): A reference to the Patient model for the associated patient.
    """
    name = models.CharField(max_length=30)
    phone_number = PhoneNumberField()
    relationship = models.CharField(max_length=20)
    email = models.EmailField()
    Patient = models.ForeignKey(
        'Patient', 
        on_delete=models.CASCADE, 
        related_name='Patient_emergency_contacts'  # Add a unique related_name
    )

    class Meta:
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"

    def __str__(self):
        return f"{self.name} - {self.relationship}"


class Patient(CustomUser):
    """
    Model for Patient users, extending the CustomUser model. 

    Attributes:
        date_of_birth (DateField): Date of birth for the patient.
        emergency_contact (ManyToManyField): Emergency contacts associated with the patient.
        gender (CharField): Gender of the patient, with choices male, female, and other.
        location (CharField): Physical location of the patient.
        vitals (JSONField): A JSON field to store a variety of health data points, including temperature, blood pressure, etc.
        last_vitals_update (DateTimeField): Timestamp of the last time vitals were updated.
    """
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    date_of_birth = models.DateField(blank=False, null=True)
    emergency_contact = models.ManyToManyField(
        EmergencyContact, 
        blank=True,
        related_name='Patients_with_contact'  # Add a unique related_name to avoid future conflicts
    )
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, default='male')
    location = models.CharField(max_length=50, default="N/A")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
    bmi = models.FloatField(blank=True, null=True, verbose_name="bmi")
    smoking_history = models.BooleanField(default=False,)
    heart_disease = models.BooleanField(default=False, null=True,)
    hypertension = models.BooleanField(default=False, null=True)
    
    
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.username} - {self.date_of_birth}"


class Provider(CustomUser):
    """
    Model for Provider users, extending the CustomUser model to include attributes for healthcare providers.

    Attributes:
        status (CharField): Defines whether the provider operates privately or publicly.
        Provider_name (CharField): Name of the provider or healthcare institution.
        address (CharField): Physical address of the provider's location.
        verified (BooleanField): Flag to show if the provider has been verified by the admin.
        location (CharField): Geographical location of the provider.
        patients (ManyToManyField): A list of patients under the care of the provider.
    """
    STATUS_CHOICES = [
        ('Private', 'Private'),
        ('Public', "Public"),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Private")
    Provider_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)
    location = models.CharField(max_length=50, default="Nairobi")
    
    # New fields for providers to manage patients
    patients = models.ManyToManyField(Patient, blank=True, related_name='assigned_providers')
    
    class Meta:
        verbose_name = "Provider"
        verbose_name_plural = "Providers"


class Admin(CustomUser):
    """
    Model for Admin users, extending the CustomUser model.

    Attributes:
        admin_code (UUIDField): A unique identifier for the admin, used for authentication or identification purposes.
        permissions (ManyToManyField): Permissions specific to admin users for managing the system.
    """
    admin_code = models.UUIDField(default=uuid.uuid4, editable=False)
    permissions = models.ManyToManyField(Permission, related_name='admin_permissions')

    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

