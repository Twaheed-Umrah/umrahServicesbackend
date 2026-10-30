from rest_framework import permissions

class CanCreatePosterPermission(permissions.BasePermission):
    """
    Custom permission to only allow Franchise Admin (Tenant) and SuperAdmin to create posters.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only allow Franchise Admin (Tenant) and SuperAdmin to create/modify
        return request.user.role in ['franchisesadmin', 'superadmin']