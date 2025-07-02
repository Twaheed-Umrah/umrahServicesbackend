from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """
    Permission to check if user is authenticated and is superadmin.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'superadmin'
        )


class HasValidSecretKey(BasePermission):
    """
    Permission to allow only requests with valid secret key in headers.
    """
    SECRET_KEY = 'hajj-umrah-services-9211948377-tawheed'

    def has_permission(self, request, view):
        secret_key = request.META.get('HTTP_X_SECRET_KEY')
        return secret_key == self.SECRET_KEY
