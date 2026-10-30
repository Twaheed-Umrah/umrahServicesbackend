from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'superadmin'

class IsFranchiseAdmin(BasePermission):
    """Permission for Tenant (Franchise Admin) or SuperAdmin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['superadmin', 'franchisesadmin']

class IsTenantOrStaff(BasePermission):
    """
    Permission class for Franchise Admin (Tenant), SuperAdmin, or their team staff
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['superadmin', 'franchisesadmin', 'accountant', 'sells_caller', 'operations']
        )
