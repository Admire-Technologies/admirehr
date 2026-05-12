"""
Security monitoring and intrusion detection system.

This module tracks security events, detects suspicious activities,
and implements blocking measures for unauthorized access attempts.
"""

import logging
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """
    Monitors security events and detects potential intrusions.
    """
    
    # Configuration
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW = 300  # 5 minutes in seconds
    BLOCK_DURATION = 1800  # 30 minutes in seconds
    
    MAX_API_REQUESTS = 100
    API_REQUEST_WINDOW = 60  # 1 minute in seconds
    
    def __init__(self):
        """Initialize security monitor."""
        self.logger = logging.getLogger('security')
    
    def record_login_attempt(self, username, ip_address, success=False):
        """
        Record a login attempt and check for suspicious activity.
        
        Args:
            username: Username attempting to login
            ip_address: IP address of the request
            success: Whether the login was successful
        
        Returns:
            dict: {
                'allowed': bool,
                'attempts': int,
                'blocked_until': datetime or None
            }
        """
        cache_key = f"login_attempts:{username}:{ip_address}"
        block_key = f"blocked:{username}:{ip_address}"
        
        # Check if already blocked
        blocked_until = cache.get(block_key)
        if blocked_until:
            self.logger.warning(
                f"Blocked login attempt for {username} from {ip_address}. "
                f"Blocked until {blocked_until}"
            )
            return {
                'allowed': False,
                'attempts': self.MAX_LOGIN_ATTEMPTS,
                'blocked_until': blocked_until
            }
        
        # Get current attempts
        attempts = cache.get(cache_key, 0)
        
        if success:
            # Clear attempts on successful login
            cache.delete(cache_key)
            self.logger.info(f"Successful login for {username} from {ip_address}")
            return {
                'allowed': True,
                'attempts': 0,
                'blocked_until': None
            }
        
        # Increment failed attempts
        attempts += 1
        cache.set(cache_key, attempts, self.LOGIN_ATTEMPT_WINDOW)
        
        self.logger.warning(
            f"Failed login attempt {attempts}/{self.MAX_LOGIN_ATTEMPTS} "
            f"for {username} from {ip_address}"
        )
        
        # Block if max attempts exceeded
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            blocked_until = timezone.now() + timedelta(seconds=self.BLOCK_DURATION)
            cache.set(block_key, blocked_until, self.BLOCK_DURATION)
            
            self.logger.error(
                f"SECURITY ALERT: User {username} blocked from {ip_address} "
                f"due to {attempts} failed login attempts. Blocked until {blocked_until}"
            )
            
            return {
                'allowed': False,
                'attempts': attempts,
                'blocked_until': blocked_until
            }
        
        return {
            'allowed': True,
            'attempts': attempts,
            'blocked_until': None
        }
    
    def is_blocked(self, username, ip_address):
        """
        Check if a username/IP combination is currently blocked.
        
        Args:
            username: Username to check
            ip_address: IP address to check
        
        Returns:
            tuple: (is_blocked: bool, blocked_until: datetime or None)
        """
        block_key = f"blocked:{username}:{ip_address}"
        blocked_until = cache.get(block_key)
        
        if blocked_until:
            return True, blocked_until
        return False, None
    
    def unblock(self, username, ip_address):
        """
        Manually unblock a username/IP combination.
        
        Args:
            username: Username to unblock
            ip_address: IP address to unblock
        """
        cache_key = f"login_attempts:{username}:{ip_address}"
        block_key = f"blocked:{username}:{ip_address}"
        
        cache.delete(cache_key)
        cache.delete(block_key)
        
        self.logger.info(f"Manually unblocked {username} from {ip_address}")
    
    def record_api_request(self, user_id, ip_address, endpoint):
        """
        Record an API request and check for rate limiting.
        
        Args:
            user_id: User ID making the request
            ip_address: IP address of the request
            endpoint: API endpoint being accessed
        
        Returns:
            dict: {
                'allowed': bool,
                'requests': int,
                'limit': int
            }
        """
        cache_key = f"api_requests:{user_id}:{ip_address}"
        
        # Get current request count
        requests = cache.get(cache_key, 0)
        requests += 1
        
        # Set with expiry
        cache.set(cache_key, requests, self.API_REQUEST_WINDOW)
        
        # Check if limit exceeded
        if requests > self.MAX_API_REQUESTS:
            self.logger.warning(
                f"Rate limit exceeded for user {user_id} from {ip_address}. "
                f"Requests: {requests}/{self.MAX_API_REQUESTS} in {self.API_REQUEST_WINDOW}s"
            )
            return {
                'allowed': False,
                'requests': requests,
                'limit': self.MAX_API_REQUESTS
            }
        
        return {
            'allowed': True,
            'requests': requests,
            'limit': self.MAX_API_REQUESTS
        }
    
    def record_security_event(self, event_type, user_id, ip_address, details):
        """
        Record a security event for monitoring and analysis.
        
        Args:
            event_type: Type of security event (e.g., 'unauthorized_access', 'permission_denied')
            user_id: User ID involved in the event
            ip_address: IP address of the request
            details: Additional details about the event
        """
        self.logger.warning(
            f"SECURITY EVENT: {event_type} | User: {user_id} | IP: {ip_address} | "
            f"Details: {details}"
        )
        
        # Store in cache for recent events tracking
        cache_key = f"security_events:{event_type}:{user_id}"
        events = cache.get(cache_key, [])
        events.append({
            'timestamp': timezone.now().isoformat(),
            'ip_address': ip_address,
            'details': details
        })
        
        # Keep only last 10 events
        events = events[-10:]
        cache.set(cache_key, events, 3600)  # 1 hour
    
    def get_security_events(self, event_type, user_id):
        """
        Get recent security events for a user.
        
        Args:
            event_type: Type of security event
            user_id: User ID
        
        Returns:
            list: Recent security events
        """
        cache_key = f"security_events:{event_type}:{user_id}"
        return cache.get(cache_key, [])
    
    def detect_suspicious_activity(self, user_id, ip_address):
        """
        Detect suspicious activity patterns.
        
        Args:
            user_id: User ID to check
            ip_address: IP address to check
        
        Returns:
            dict: {
                'suspicious': bool,
                'reasons': list of reasons
            }
        """
        reasons = []
        
        # Check for multiple failed logins
        cache_key = f"login_attempts:{user_id}:{ip_address}"
        attempts = cache.get(cache_key, 0)
        if attempts >= 3:
            reasons.append(f"Multiple failed login attempts ({attempts})")
        
        # Check for high API request rate
        api_key = f"api_requests:{user_id}:{ip_address}"
        requests = cache.get(api_key, 0)
        if requests > self.MAX_API_REQUESTS * 0.8:  # 80% of limit
            reasons.append(f"High API request rate ({requests}/{self.MAX_API_REQUESTS})")
        
        # Check for recent security events
        for event_type in ['unauthorized_access', 'permission_denied', 'invalid_token']:
            events = self.get_security_events(event_type, user_id)
            if len(events) >= 3:
                reasons.append(f"Multiple {event_type} events ({len(events)})")
        
        return {
            'suspicious': len(reasons) > 0,
            'reasons': reasons
        }


# Singleton instance
_monitor_instance = None


def get_security_monitor():
    """
    Get singleton instance of SecurityMonitor.
    
    Returns:
        SecurityMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SecurityMonitor()
    return _monitor_instance
