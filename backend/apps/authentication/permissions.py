"""
Custom DRF permissions for RBAC system.
"""

from rest_framework import permissions


class HasPermission(permissions.BasePermission):
    """
    Custom permission to check if user has specific permission.
    """
    required_permission = None
    
    def __init__(self, permission_codename):
        self.required_permission = permission_codename
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.has_permission(self.required_permission)


class HasAnyPermission(permissions.BasePermission):
    """
    Custom permission to check if user has any of the specified permissions.
    """
    required_permissions = []
    
    def __init__(self, *permission_codenames):
        self.required_permissions = permission_codenames
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return any(
            request.user.has_permission(permission) 
            for permission in self.required_permissions
        )


class HasAllPermissions(permissions.BasePermission):
    """
    Custom permission to check if user has all specified permissions.
    """
    required_permissions = []
    
    def __init__(self, *permission_codenames):
        self.required_permissions = permission_codenames
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return all(
            request.user.has_permission(permission) 
            for permission in self.required_permissions
        )


class IsCompanyAdmin(permissions.BasePermission):
    """
    Permission to check if user is company admin.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_company_admin
        )


class IsSameCompany(permissions.BasePermission):
    """
    Permission to check if user belongs to the same company as the object.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if object has company attribute
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        
        # Check if object is a user and belongs to same company
        if hasattr(obj, 'company_id'):
            return obj.company_id == request.user.company_id
        
        return False


class CanManageUsers(permissions.BasePermission):
    """
    Permission to check if user can manage other users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_company_admin or 
            request.user.has_permission('manage_users')
        )


class CanManageRoles(permissions.BasePermission):
    """
    Permission to check if user can manage roles.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_company_admin or 
            request.user.has_permission('manage_roles')
        )


class ModulePermission(permissions.BasePermission):
    """
    Permission class for module-based access control.
    """
    module_name = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.module_name:
            return False
        
        # Map HTTP methods to actions
        action_map = {
            'GET': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete'
        }
        
        action = action_map.get(request.method, 'view')
        permission_codename = f"{action}_{self.module_name}"
        
        return request.user.has_permission(permission_codename)


# Module-specific permission classes
class EmployeePermission(ModulePermission):
    module_name = 'employee'


class AttendancePermission(ModulePermission):
    module_name = 'attendance'


class LeavePermission(ModulePermission):
    module_name = 'leave'


class PayrollPermission(ModulePermission):
    module_name = 'payroll'


class ReportPermission(ModulePermission):
    module_name = 'report'