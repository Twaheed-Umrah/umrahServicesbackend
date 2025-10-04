from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'superadmin'

class IsAgencyAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['superadmin', 'agencyadmin']

class IsFranchiseAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['superadmin', 'agencyadmin', 'franchisesadmin']

class IsFreelancer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'freelancer'
    
class IsAgencyAdminOrSuperAdmin(BasePermission):
    """
    Permission class to check if user is Agency Admin or Super Admin
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'user_type') and 
            request.user.user_type in ['agency_admin', 'superadmin']
        )
    
class IsFranchiseOrAgencyAdmin(BasePermission):
    """
    Permission class to check if user is FranchiseAdmin, AgencyAdmin, their accountants, or SuperAdmin
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in ['superadmin', 'agencyadmin', 'franchisesadmin', 'accountant']
        )