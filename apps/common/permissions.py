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
