from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Patient, Provider, Admin, EmergencyContact

class CustomUserAdmin(UserAdmin):
    """
    CustomUserAdmin class to manage CustomUser model in the admin interface.
    """
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_admin']
    list_filter = ['user_type', 'is_admin', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['email']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'contact_number', 'image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

class PatientAdmin(admin.ModelAdmin):
    """
    PatientAdmin class to manage Patient model in the admin interface.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_of_birth', 'contact_number']
    search_fields = ['username', 'email', 'first_name', 'last_name']

class ProviderAdmin(admin.ModelAdmin):
    """
    ProviderAdmin class to manage Provider model in the admin interface.
    """
    list_display = ['username', 'email', 'Provider_name', 'verified', 'location']
    search_fields = ['username', 'email', 'Provider_name', 'location']
    list_filter = ['verified', 'status']

class AdminAdmin(admin.ModelAdmin):
    """
    AdminAdmin class to manage Admin model in the admin interface.
    """
    list_display = ['username', 'email', 'admin_code', 'is_admin']
    search_fields = ['username', 'email', 'admin_code']

class EmergencyContactAdmin(admin.ModelAdmin):
    """
    EmergencyContactAdmin class to manage EmergencyContact model in the admin interface.
    """
    list_display = ['name', 'phone_number', 'relationship', 'email']
    search_fields = ['name', 'phone_number', 'email']

# Register the models in the Django admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(Admin, AdminAdmin)
admin.site.register(EmergencyContact, EmergencyContactAdmin)
