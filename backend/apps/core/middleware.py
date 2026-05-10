"""
Middleware for multi-tenant support in the HRMS application.
"""

import threading
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import Company


# Thread-local storage for current company
_thread_locals = threading.local()


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to automatically set the current company/tenant based on the authenticated user.
    """
    
    def process_request(self, request):
        """
        Set the current company in thread-local storage based on the authenticated user.
        """
        # Clear any existing tenant data
        clear_current_company()
        
        # Skip tenant scoping for certain paths
        skip_paths = [
            '/admin/',
            '/api/schema/',
            '/api/docs/',
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
            '/api/v1/companies/register/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Set company from authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                set_current_company(request.user.company)
                request.company = request.user.company
            else:
                # User doesn't have a company assigned
                return JsonResponse({
                    'error': 'User not associated with any company',
                    'code': 'NO_COMPANY_ASSIGNED'
                }, status=400)
        
        return None

    def process_response(self, request, response):
        """
        Clear the current company from thread-local storage after request processing.
        """
        clear_current_company()
        return response


def get_current_company():
    """
    Get the current company from thread-local storage.
    """
    return getattr(_thread_locals, 'company', None)


def set_current_company(company):
    """
    Set the current company in thread-local storage.
    """
    _thread_locals.company = company


def clear_current_company():
    """
    Clear the current company from thread-local storage.
    """
    if hasattr(_thread_locals, 'company'):
        delattr(_thread_locals, 'company')


# Import models here to avoid circular imports
from django.db import models


class TenantAwareManager(models.Manager):
    """
    Manager that automatically filters queries by the current company.
    """
    
    def get_queryset(self):
        """
        Return a queryset filtered by the current company.
        """
        queryset = super().get_queryset()
        current_company = get_current_company()
        
        if current_company:
            return queryset.filter(company=current_company)
        
        return queryset
    
    def all_companies(self):
        """
        Return a queryset with all companies (bypass tenant filtering).
        """
        return super().get_queryset()