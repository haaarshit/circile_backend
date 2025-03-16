from rest_framework import permissions
from .models import SuperAdmin

class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to allow access only to authenticated SuperAdmin users.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated and is a SuperAdmin instance
        return bool(request.user and isinstance(request.user, SuperAdmin) and request.user.is_active)