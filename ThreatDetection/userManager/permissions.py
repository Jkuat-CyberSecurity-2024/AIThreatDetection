from rest_framework.permissions import BasePermission, SAFE_METHODS

class CustomUserPermission(BasePermission):
    """
    Custom permission class that grants different access levels to users
    based on their user type: Patient, Provider, or admin.
    """

    def has_permission(self, request, view):
        user = request.user

        # Allow read-only access for unauthenticated users
        if not user.is_authenticated:
            return request.method in SAFE_METHODS
        
        # Admins have full access
        if user.user_type == 'admin':
            return True

        # Define permissions for other user types
        user_permissions = {
            'Patient': self._Patient_permissions,
            'Provider': self._Provider_permissions,
            # 'department': self._department_permissions,  # Uncomment if needed
        }

        # Call the appropriate permission method based on user type
        if user.user_type in user_permissions:
            return user_permissions[user.user_type](request, view)

        # Fallback for unsupported user types
        return False

    def _Patient_permissions(self, request, view):
        """
        Define permissions for Patient users.
        """
        # Read-only access for Patient users
        return request.method in SAFE_METHODS

    def _Provider_permissions(self, request, view):
        """
        Define permissions for Provider users.
        """
        # Allow read access and write access (POST, PUT, PATCH) for Provider users
        return request.method in SAFE_METHODS or request.method in ['POST', 'PUT', 'PATCH']

    # def _department_permissions(self, request, view):
    #     """
    #     Define permissions for department users (if applicable).
    #     """
    #     return request.method in SAFE_METHODS  # Example: read-only access for departments
