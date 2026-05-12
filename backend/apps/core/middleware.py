"""
Middleware for multi-tenant support and audit logging in the HRMS application.
"""

import threading
import json
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



class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log API requests for audit trail.
    Logs all POST, PUT, PATCH, DELETE requests.
    """
    
    def process_request(self, request):
        """Store request data for later logging."""
        # Store original request body for logging
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                # Store the body for later use
                request._body_for_audit = request.body.decode('utf-8')
            except Exception:
                request._body_for_audit = None
        return None
    
    def process_response(self, request, response):
        """Log the request after processing."""
        # Skip audit logging for certain paths
        skip_paths = [
            '/admin/',
            '/api/schema/',
            '/api/docs/',
            '/api/v1/auth/login/',
            '/api/v1/auth/refresh/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        # Only log state-changing methods
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return response
        
        # Only log if user is authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response
        
        # Import here to avoid circular imports
        from apps.authentication.models import AuditLog
        
        try:
            # Determine action type
            action_map = {
                'POST': 'create',
                'PUT': 'update',
                'PATCH': 'update',
                'DELETE': 'delete',
            }
            action = action_map.get(request.method, 'access')
            
            # Extract module from path
            path_parts = request.path.strip('/').split('/')
            module = path_parts[2] if len(path_parts) > 2 else 'unknown'
            
            # Build description
            description = f"{request.method} {request.path}"
            
            # Extract request data
            changes = {}
            if hasattr(request, '_body_for_audit') and request._body_for_audit:
                try:
                    changes['request_data'] = json.loads(request._body_for_audit)
                except Exception:
                    changes['request_data'] = request._body_for_audit[:500]  # Truncate
            
            # Add response status
            changes['status_code'] = response.status_code
            
            # Create audit log
            AuditLog.log_action(
                user=request.user,
                action=action,
                module=module,
                description=description,
                changes=changes,
                request=request
            )
        
        except Exception as e:
            # Don't fail the request if audit logging fails
            import logging
            logger = logging.getLogger('audit')
            logger.error(f"Failed to create audit log: {str(e)}")
        
        return response


class SecurityMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor security events and detect suspicious activity.
    """
    
    def process_request(self, request):
        """Monitor incoming requests for security threats."""
        # Import here to avoid circular imports
        from apps.core.security_monitor import get_security_monitor
        
        # Skip monitoring for certain paths
        skip_paths = [
            '/admin/',
            '/api/schema/',
            '/api/docs/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Check for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            monitor = get_security_monitor()
            
            # Record API request
            result = monitor.record_api_request(
                user_id=str(request.user.id),
                ip_address=ip_address,
                endpoint=request.path
            )
            
            # Block if rate limit exceeded
            if not result['allowed']:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'requests': result['requests'],
                    'limit': result['limit']
                }, status=429)
            
            # Check for suspicious activity
            suspicious = monitor.detect_suspicious_activity(
                user_id=str(request.user.id),
                ip_address=ip_address
            )
            
            if suspicious['suspicious']:
                monitor.record_security_event(
                    event_type='suspicious_activity',
                    user_id=str(request.user.id),
                    ip_address=ip_address,
                    details={'reasons': suspicious['reasons']}
                )
        
        return None
