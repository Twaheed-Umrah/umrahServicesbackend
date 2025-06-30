# apps/enquiries/permissions.py
from rest_framework.permissions import BasePermission

class HasValidAPIKey(BasePermission):
    """
    Custom permission to check if the request has a valid API key
    """
    def has_permission(self, request, view):
        return hasattr(request, 'auth') and request.auth is not None