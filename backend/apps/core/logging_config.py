"""
Structured logging configuration for production monitoring
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        """
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'company_id'):
            log_data['company_id'] = record.company_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
        
        return json.dumps(log_data)


class RequestLoggingMiddleware:
    """
    Middleware for logging HTTP requests with structured data
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('admire_hrms.requests')
    
    def __call__(self, request):
        import time
        import uuid
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log request
        extra = {
            'request_id': request_id,
            'method': request.method,
            'endpoint': request.path,
            'ip_address': self.get_client_ip(request),
            'status_code': response.status_code,
            'duration': round(duration, 2),
        }
        
        # Add user info if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            extra['user_id'] = str(request.user.id)
            if hasattr(request.user, 'company'):
                extra['company_id'] = str(request.user.company.id)
        
        # Log based on status code
        if response.status_code >= 500:
            self.logger.error(f"Server error: {request.method} {request.path}", extra=extra)
        elif response.status_code >= 400:
            self.logger.warning(f"Client error: {request.method} {request.path}", extra=extra)
        else:
            self.logger.info(f"Request: {request.method} {request.path}", extra=extra)
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def get_logging_config(log_level='INFO'):
    """
    Get logging configuration for production
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': 'apps.core.logging_config.JSONFormatter',
            },
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'level': log_level,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/application.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
                'level': log_level,
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
                'level': 'ERROR',
            },
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/security.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 20,
                'formatter': 'json',
                'level': 'INFO',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'error_file'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.security': {
                'handlers': ['security_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'admire_hrms': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False,
            },
            'admire_hrms.requests': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'admire_hrms.security': {
                'handlers': ['security_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'celery': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': log_level,
        },
    }
