"""
Comprehensive error handling for Admire HRMS
Provides standardized error responses and exception handling
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.http import Http404
import logging
import traceback
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HRMSException(Exception):
    """Base exception for HRMS operations"""
    default_message = "An error occurred in the HRMS system"
    default_code = "hrms_error"
    default_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, message: str = None, code: str = None, status_code: int = None, details: Dict = None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status
        self.details = details or {}
        super().__init__(self.message)


class BiometricVerificationError(HRMSException):
    """Raised when biometric verification fails"""
    default_message = "Biometric verification failed"
    default_code = "biometric_verification_failed"
    default_status = status.HTTP_422_UNPROCESSABLE_ENTITY


class PayrollCalculationError(HRMSException):
    """Raised when payroll calculation encounters errors"""
    default_message = "Payroll calculation failed"
    default_code = "payroll_calculation_error"
    default_status = status.HTTP_422_UNPROCESSABLE_ENTITY


class AttendanceValidationError(HRMSException):
    """Raised when attendance validation fails"""
    default_message = "Attendance validation failed"
    default_code = "attendance_validation_error"
    default_status = status.HTTP_400_BAD_REQUEST


class LeaveBalanceError(HRMSException):
    """Raised when leave balance is insufficient"""
    default_message = "Insufficient leave balance"
    default_code = "insufficient_leave_balance"
    default_status = status.HTTP_400_BAD_REQUEST


class TenantIsolationError(HRMSException):
    """Raised when tenant isolation is violated"""
    default_message = "Tenant isolation violation detected"
    default_code = "tenant_isolation_error"
    default_status = status.HTTP_403_FORBIDDEN


class RateLimitExceededError(HRMSException):
    """Raised when rate limit is exceeded"""
    default_message = "Rate limit exceeded"
    default_code = "rate_limit_exceeded"
    default_status = status.HTTP_429_TOO_MANY_REQUESTS


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF
    Returns structured error responses with consistent format
    
    Error Response Format:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable error message",
            "details": {...},  # Optional additional details
            "timestamp": "ISO datetime",
            "path": "/api/v1/endpoint"
        }
    }
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request information
    request = context.get('view').request if context.get('view') else None
    path = request.path if request else "unknown"
    
    # Handle custom HRMS exceptions
    if isinstance(exc, HRMSException):
        error_response = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "path": path
            }
        }
        
        # Log the error
        logger.error(
            f"HRMS Exception: {exc.code} - {exc.message}",
            extra={
                "path": path,
                "details": exc.details,
                "user": getattr(request, 'user', None)
            }
        )
        
        return Response(error_response, status=exc.status_code)
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        error_response = {
            "error": {
                "code": "validation_error",
                "message": "Validation failed",
                "details": exc.message_dict if hasattr(exc, 'message_dict') else {"detail": str(exc)},
                "path": path
            }
        }
        
        logger.warning(f"Validation Error: {str(exc)}", extra={"path": path})
        
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle permission denied
    if isinstance(exc, PermissionDenied):
        error_response = {
            "error": {
                "code": "permission_denied",
                "message": "You do not have permission to perform this action",
                "details": {"detail": str(exc)},
                "path": path
            }
        }
        
        logger.warning(
            f"Permission Denied: {str(exc)}",
            extra={
                "path": path,
                "user": getattr(request, 'user', None)
            }
        )
        
        return Response(error_response, status=status.HTTP_403_FORBIDDEN)
    
    # Handle 404 errors
    if isinstance(exc, (Http404, ObjectDoesNotExist)):
        error_response = {
            "error": {
                "code": "not_found",
                "message": "The requested resource was not found",
                "details": {"detail": str(exc)},
                "path": path
            }
        }
        
        logger.info(f"Not Found: {str(exc)}", extra={"path": path})
        
        return Response(error_response, status=status.HTTP_404_NOT_FOUND)
    
    # If response is already set by DRF, enhance it with our format
    if response is not None:
        error_response = {
            "error": {
                "code": "api_error",
                "message": response.data.get('detail', 'An error occurred'),
                "details": response.data,
                "path": path
            }
        }
        response.data = error_response
        
        logger.error(
            f"API Error: {response.status_code}",
            extra={
                "path": path,
                "status_code": response.status_code,
                "details": response.data
            }
        )
        
        return response
    
    # Handle unexpected errors
    error_response = {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": {"detail": str(exc)} if logger.level == logging.DEBUG else {},
            "path": path
        }
    }
    
    # Log the full traceback for unexpected errors
    logger.error(
        f"Unexpected Error: {str(exc)}",
        extra={
            "path": path,
            "traceback": traceback.format_exc(),
            "user": getattr(request, 'user', None)
        }
    )
    
    return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ErrorHandlingMiddleware:
    """
    Middleware for handling errors at the Django level
    Catches errors that occur outside of DRF views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            logger.error(
                f"Middleware caught exception: {str(exc)}",
                extra={
                    "path": request.path,
                    "method": request.method,
                    "traceback": traceback.format_exc()
                }
            )
            
            # Return JSON error response
            from django.http import JsonResponse
            return JsonResponse(
                {
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred",
                        "path": request.path
                    }
                },
                status=500
            )
    
    def process_exception(self, request, exception):
        """Process exceptions that occur during request processing"""
        logger.error(
            f"Exception during request processing: {str(exception)}",
            extra={
                "path": request.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )
        return None


def retry_on_db_error(max_retries: int = 3, delay: float = 0.5):
    """
    Decorator to retry database operations on transient errors
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    
    Usage:
        @retry_on_db_error(max_retries=3)
        def save_attendance_record(data):
            return AttendanceRecord.objects.create(**data)
    """
    from functools import wraps
    import time
    from django.db import OperationalError, InterfaceError
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, InterfaceError) as e:
                    last_exception = e
                    logger.warning(
                        f"Database error on attempt {attempt + 1}/{max_retries}: {str(e)}"
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(
                            f"Max retries exceeded for {func.__name__}",
                            extra={"exception": str(e)}
                        )
            
            # If all retries failed, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator
