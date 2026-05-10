"""
Permission checking decorators for RBAC system.
"""

from functools import wraps
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse


def require_permission(permission_codename):
    """
    Decorator to check if user has required permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required'}, 
                    status=401
                )
            
            if not request.user.has_permission(permission_codename):
                return JsonResponse(
                    {'error': 'Permission denied'}, 
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*permission_codenames):
    """
    Decorator to check if user has all required permissions.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required'}, 
                    status=401
                )
            
            for permission_codename in permission_codenames:
                if not request.user.has_permission(permission_codename):
                    return JsonResponse(
                        {'error': f'Permission denied: {permission_codename}'}, 
                        status=403
                    )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_codenames):
    """
    Decorator to check if user has any of the required permissions.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required'}, 
                    status=401
                )
            
            has_permission = any(
                request.user.has_permission(permission_codename) 
                for permission_codename in permission_codenames
            )
            
            if not has_permission:
                return JsonResponse(
                    {'error': 'Permission denied'}, 
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class PermissionRequiredMixin:
    """
    Mixin for DRF views to check permissions.
    """
    required_permissions = []
    
    def check_permissions(self, request):
        """
        Check if user has required permissions.
        """
        super().check_permissions(request)
        
        if not self.required_permissions:
            return
        
        for permission_codename in self.required_permissions:
            if not request.user.has_permission(permission_codename):
                self.permission_denied(
                    request,
                    message=f'Permission denied: {permission_codename}'
                )


class RoleBasedPermissionMixin:
    """
    Mixin to check role-based permissions for DRF views.
    """
    required_role = None
    required_permissions = []
    
    def check_permissions(self, request):
        """
        Check role and permissions.
        """
        super().check_permissions(request)
        
        # Check role requirement
        if self.required_role and request.user.role.name != self.required_role:
            self.permission_denied(
                request,
                message=f'Role required: {self.required_role}'
            )
        
        # Check permission requirements
        for permission_codename in self.required_permissions:
            if not request.user.has_permission(permission_codename):
                self.permission_denied(
                    request,
                    message=f'Permission denied: {permission_codename}'
                )