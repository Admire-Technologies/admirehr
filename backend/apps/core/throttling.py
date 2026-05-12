"""
API Rate Limiting and Throttling System.
Implements custom throttling classes for different API endpoints and user types.
"""
from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle, UserRateThrottle
from django.core.cache import cache
from django.conf import settings
import time


class BurstRateThrottle(SimpleRateThrottle):
    """
    Throttle for burst requests - limits rapid successive requests.
    Allows 20 requests per minute.
    """
    scope = 'burst'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class AuthenticationRateThrottle(SimpleRateThrottle):
    """
    Strict throttling for authentication endpoints to prevent brute force attacks.
    Allows 5 login attempts per 15 minutes.
    """
    scope = 'auth'
    rate = '5/15m'
    
    def get_cache_key(self, request, view):
        # Use IP address for authentication throttling
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
    
    def parse_rate(self, rate):
        """
        Override to support custom time periods like '15m' for 15 minutes.
        """
        if rate is None:
            return (None, None)
        
        num, period = rate.split('/')
        num_requests = int(num)
        
        # Parse duration
        if period.endswith('m'):
            # Minutes
            duration = int(period[:-1]) * 60
        elif period.endswith('h'):
            # Hours
            duration = int(period[:-1]) * 3600
        elif period.endswith('d'):
            # Days
            duration = int(period[:-1]) * 86400
        elif period.endswith('s'):
            # Seconds
            duration = int(period[:-1])
        else:
            # Default to seconds
            duration = int(period)
        
        return (num_requests, duration)


class BiometricAPIThrottle(SimpleRateThrottle):
    """
    Throttling for biometric API endpoints.
    Allows 100 requests per hour per device/terminal.
    """
    scope = 'biometric'
    rate = '100/hour'
    
    def get_cache_key(self, request, view):
        # Use device/terminal ID if provided, otherwise use IP
        device_id = request.META.get('HTTP_X_DEVICE_ID')
        if device_id:
            ident = device_id
        elif request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class PayrollAPIThrottle(SimpleRateThrottle):
    """
    Throttling for payroll processing endpoints.
    Allows 10 requests per hour to prevent excessive processing.
    """
    scope = 'payroll'
    rate = '10/hour'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class ReportGenerationThrottle(SimpleRateThrottle):
    """
    Throttling for report generation endpoints.
    Allows 20 reports per hour per user.
    """
    scope = 'reports'
    rate = '20/hour'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class CompanyAdminThrottle(UserRateThrottle):
    """
    Higher rate limits for company administrators.
    Allows 5000 requests per hour.
    """
    def get_rate(self):
        if hasattr(self, 'request') and self.request.user.is_authenticated:
            if getattr(self.request.user, 'is_company_admin', False):
                return '5000/hour'
        return '1000/hour'


class DynamicRateThrottle(SimpleRateThrottle):
    """
    Dynamic throttling based on user role and company settings.
    """
    scope = 'dynamic'
    
    def get_rate(self):
        """
        Get rate limit from company settings or user role.
        """
        if not hasattr(self, 'request') or not self.request.user.is_authenticated:
            return '100/hour'
        
        user = self.request.user
        
        # Check company-specific rate limits
        if hasattr(user, 'company') and user.company:
            company_settings = user.company.settings or {}
            rate_limits = company_settings.get('api_rate_limits', {})
            
            # Check role-specific limits
            if user.role:
                role_limit = rate_limits.get(user.role.name)
                if role_limit:
                    return role_limit
            
            # Check default company limit
            default_limit = rate_limits.get('default')
            if default_limit:
                return default_limit
        
        # Default rate limit
        return '1000/hour'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


def get_throttle_status(user=None, ip_address=None):
    """
    Get current throttle status for a user or IP address.
    
    Args:
        user: User object (optional)
        ip_address: IP address string (optional)
        
    Returns:
        Dictionary with throttle status information
    """
    status = {
        'throttled': False,
        'limits': {},
        'remaining': {},
        'reset_times': {}
    }
    
    # Define scopes to check
    scopes = ['user', 'burst', 'auth', 'biometric', 'payroll', 'reports']
    
    for scope in scopes:
        # Get rate limit for scope
        rate = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {}).get(scope)
        if not rate:
            continue
        
        # Parse rate
        num_requests, duration = rate.split('/')
        num_requests = int(num_requests)
        
        # Build cache key
        if user:
            ident = user.pk
        elif ip_address:
            ident = ip_address
        else:
            continue
        
        cache_key = f'throttle_{scope}_{ident}'
        
        # Get current count from cache
        history = cache.get(cache_key, [])
        now = time.time()
        
        # Filter history to current window
        if duration.endswith('hour'):
            window = 3600
        elif duration.endswith('minute'):
            window = 60
        elif duration.endswith('day'):
            window = 86400
        else:
            window = 3600
        
        history = [timestamp for timestamp in history if timestamp > now - window]
        
        # Calculate remaining requests
        remaining = max(0, num_requests - len(history))
        
        status['limits'][scope] = num_requests
        status['remaining'][scope] = remaining
        
        if history:
            # Calculate reset time (when oldest request expires)
            oldest = min(history)
            reset_time = oldest + window
            status['reset_times'][scope] = reset_time
        
        if remaining == 0:
            status['throttled'] = True
    
    return status


def reset_throttle(user=None, ip_address=None, scope=None):
    """
    Reset throttle limits for a user or IP address.
    
    Args:
        user: User object (optional)
        ip_address: IP address string (optional)
        scope: Specific scope to reset (optional, resets all if None)
    """
    if user:
        ident = user.pk
    elif ip_address:
        ident = ip_address
    else:
        return
    
    if scope:
        scopes = [scope]
    else:
        scopes = ['user', 'burst', 'auth', 'biometric', 'payroll', 'reports']
    
    for s in scopes:
        cache_key = f'throttle_{s}_{ident}'
        cache.delete(cache_key)
