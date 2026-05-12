"""
Enhanced logging utilities for Admire HRMS
Provides specialized loggers for audit, performance, and security events
"""

import logging
from typing import Dict, Any
from datetime import datetime


class AuditLogger:
    """
    Specialized logger for audit trail events
    """
    
    def __init__(self):
        self.logger = logging.getLogger('admire_hrms.audit')
    
    def log_action(self, action: str, user, resource_type: str, resource_id: str, 
                   details: Dict[str, Any] = None, company=None):
        """
        Log an audit trail event
        
        Args:
            action: Action performed (create, update, delete, view, etc.)
            user: User who performed the action
            resource_type: Type of resource (employee, attendance, leave, etc.)
            resource_id: ID of the resource
            details: Additional details about the action
            company: Company context
        """
        log_data = {
            'action': action,
            'user': str(user),
            'user_id': str(user.id) if hasattr(user, 'id') else None,
            'resource_type': resource_type,
            'resource_id': str(resource_id),
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if company:
            log_data['company_id'] = str(company.id)
        
        self.logger.info(f"Audit: {action} {resource_type}", extra=log_data)
    
    def log_login(self, user, success: bool, ip_address: str = None, details: Dict = None):
        """Log user login attempt"""
        log_data = {
            'action': 'login',
            'user': str(user) if user else 'unknown',
            'success': success,
            'ip_address': ip_address,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if success:
            self.logger.info(f"Login successful: {user}", extra=log_data)
        else:
            self.logger.warning(f"Login failed: {user}", extra=log_data)
    
    def log_permission_check(self, user, permission: str, granted: bool, resource=None):
        """Log permission check"""
        log_data = {
            'action': 'permission_check',
            'user': str(user),
            'permission': permission,
            'granted': granted,
            'resource': str(resource) if resource else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if not granted:
            self.logger.warning(f"Permission denied: {permission} for {user}", extra=log_data)
        else:
            self.logger.debug(f"Permission granted: {permission} for {user}", extra=log_data)


class PerformanceLogger:
    """
    Logger for performance metrics and monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger('admire_hrms.performance')
    
    def log_query_performance(self, operation: str, query_count: int, duration_ms: float, 
                             details: Dict = None):
        """Log database query performance"""
        log_data = {
            'operation': operation,
            'query_count': query_count,
            'duration_ms': round(duration_ms, 2),
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Warn on excessive queries (N+1 problem)
        if query_count > 10:
            self.logger.warning(
                f"High query count detected: {operation}",
                extra={**log_data, 'potential_n_plus_1': True}
            )
        elif duration_ms > 100:
            self.logger.warning(f"Slow operation: {operation}", extra=log_data)
        else:
            self.logger.debug(f"Query performance: {operation}", extra=log_data)
    
    def log_cache_hit(self, cache_key: str, hit: bool):
        """Log cache hit/miss"""
        log_data = {
            'cache_key': cache_key,
            'hit': hit,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.debug(f"Cache {'hit' if hit else 'miss'}: {cache_key}", extra=log_data)
    
    def log_background_job(self, job_name: str, duration_ms: float, success: bool, 
                          details: Dict = None):
        """Log background job execution"""
        log_data = {
            'job_name': job_name,
            'duration_ms': round(duration_ms, 2),
            'success': success,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if success:
            self.logger.info(f"Background job completed: {job_name}", extra=log_data)
        else:
            self.logger.error(f"Background job failed: {job_name}", extra=log_data)


class SecurityLogger:
    """
    Logger for security-related events
    """
    
    def __init__(self):
        self.logger = logging.getLogger('admire_hrms.security')
    
    def log_security_event(self, event_type: str, severity: str, details: Dict, 
                          user=None, ip_address: str = None):
        """
        Log security event
        
        Args:
            event_type: Type of security event (failed_login, permission_denied, etc.)
            severity: Severity level (low, medium, high, critical)
            details: Event details
            user: User involved (if applicable)
            ip_address: IP address (if applicable)
        """
        log_data = {
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'user': str(user) if user else None,
            'ip_address': ip_address,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if severity in ['high', 'critical']:
            self.logger.error(f"Security event: {event_type}", extra=log_data)
        elif severity == 'medium':
            self.logger.warning(f"Security event: {event_type}", extra=log_data)
        else:
            self.logger.info(f"Security event: {event_type}", extra=log_data)
    
    def log_failed_authentication(self, username: str, ip_address: str, reason: str):
        """Log failed authentication attempt"""
        self.log_security_event(
            event_type='failed_authentication',
            severity='medium',
            details={'username': username, 'reason': reason},
            ip_address=ip_address
        )
    
    def log_suspicious_activity(self, activity: str, user, details: Dict):
        """Log suspicious activity"""
        self.log_security_event(
            event_type='suspicious_activity',
            severity='high',
            details={'activity': activity, **details},
            user=user
        )


# Global logger instances
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
