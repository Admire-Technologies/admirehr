"""
Caching utilities for Admire HRMS
Implements Redis caching strategies for frequently accessed data
"""

from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a unique cache key based on prefix and arguments
    
    Args:
        prefix: Cache key prefix (e.g., 'employee_list', 'dashboard_metrics')
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
    
    Returns:
        Unique cache key string
    """
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
    return f"{prefix}:{key_hash}"


def cache_result(timeout: int = 300, key_prefix: str = None):
    """
    Decorator to cache function results in Redis
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Custom cache key prefix (default: function name)
    
    Usage:
        @cache_result(timeout=600, key_prefix='employee_list')
        def get_employees(company_id, department_id=None):
            return Employee.objects.filter(company_id=company_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs):
    """
    Invalidate specific cache entry
    
    Args:
        key_prefix: Cache key prefix to invalidate
        *args: Positional arguments used in original cache key
        **kwargs: Keyword arguments used in original cache key
    """
    cache_key = generate_cache_key(key_prefix, *args, **kwargs)
    cache.delete(cache_key)
    logger.info(f"Invalidated cache key: {cache_key}")


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching a pattern
    
    Args:
        pattern: Pattern to match (e.g., 'employee_list:*', 'dashboard:*')
    
    Note: This requires Redis and uses SCAN command for efficiency
    """
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        # Use SCAN to find matching keys (more efficient than KEYS)
        cursor = 0
        deleted_count = 0
        
        while True:
            cursor, keys = redis_conn.scan(cursor, match=pattern, count=100)
            if keys:
                redis_conn.delete(*keys)
                deleted_count += len(keys)
            
            if cursor == 0:
                break
        
        logger.info(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
        
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {str(e)}")


class CacheManager:
    """
    Centralized cache management for common data patterns
    """
    
    # Cache timeouts (in seconds)
    TIMEOUT_SHORT = 60  # 1 minute
    TIMEOUT_MEDIUM = 300  # 5 minutes
    TIMEOUT_LONG = 900  # 15 minutes
    TIMEOUT_VERY_LONG = 3600  # 1 hour
    
    @staticmethod
    def get_employee_list(company_id: str, filters: dict = None) -> Any:
        """Get cached employee list for a company"""
        cache_key = generate_cache_key('employee_list', company_id, **(filters or {}))
        return cache.get(cache_key)
    
    @staticmethod
    def set_employee_list(company_id: str, data: Any, filters: dict = None):
        """Cache employee list for a company"""
        cache_key = generate_cache_key('employee_list', company_id, **(filters or {}))
        cache.set(cache_key, data, CacheManager.TIMEOUT_MEDIUM)
    
    @staticmethod
    def invalidate_employee_cache(company_id: str):
        """Invalidate all employee-related cache for a company"""
        invalidate_cache_pattern(f'employee_list:{company_id}:*')
    
    @staticmethod
    def get_department_structure(company_id: str) -> Any:
        """Get cached department structure"""
        cache_key = f'department_structure:{company_id}'
        return cache.get(cache_key)
    
    @staticmethod
    def set_department_structure(company_id: str, data: Any):
        """Cache department structure"""
        cache_key = f'department_structure:{company_id}'
        cache.set(cache_key, data, CacheManager.TIMEOUT_LONG)
    
    @staticmethod
    def invalidate_department_cache(company_id: str):
        """Invalidate department structure cache"""
        cache_key = f'department_structure:{company_id}'
        cache.delete(cache_key)
    
    @staticmethod
    def get_dashboard_metrics(company_id: str, date: str = None) -> Any:
        """Get cached dashboard metrics"""
        cache_key = generate_cache_key('dashboard_metrics', company_id, date=date)
        return cache.get(cache_key)
    
    @staticmethod
    def set_dashboard_metrics(company_id: str, data: Any, date: str = None):
        """Cache dashboard metrics"""
        cache_key = generate_cache_key('dashboard_metrics', company_id, date=date)
        cache.set(cache_key, data, CacheManager.TIMEOUT_SHORT)
    
    @staticmethod
    def invalidate_dashboard_cache(company_id: str):
        """Invalidate dashboard metrics cache"""
        invalidate_cache_pattern(f'dashboard_metrics:{company_id}:*')
    
    @staticmethod
    def get_attendance_summary(company_id: str, date: str) -> Any:
        """Get cached attendance summary"""
        cache_key = f'attendance_summary:{company_id}:{date}'
        return cache.get(cache_key)
    
    @staticmethod
    def set_attendance_summary(company_id: str, date: str, data: Any):
        """Cache attendance summary"""
        cache_key = f'attendance_summary:{company_id}:{date}'
        cache.set(cache_key, data, CacheManager.TIMEOUT_LONG)
    
    @staticmethod
    def invalidate_attendance_cache(company_id: str, date: str = None):
        """Invalidate attendance cache"""
        if date:
            cache_key = f'attendance_summary:{company_id}:{date}'
            cache.delete(cache_key)
        else:
            invalidate_cache_pattern(f'attendance_summary:{company_id}:*')
    
    @staticmethod
    def get_leave_balance(employee_id: str) -> Any:
        """Get cached leave balance"""
        cache_key = f'leave_balance:{employee_id}'
        return cache.get(cache_key)
    
    @staticmethod
    def set_leave_balance(employee_id: str, data: Any):
        """Cache leave balance"""
        cache_key = f'leave_balance:{employee_id}'
        cache.set(cache_key, data, CacheManager.TIMEOUT_MEDIUM)
    
    @staticmethod
    def invalidate_leave_balance(employee_id: str):
        """Invalidate leave balance cache"""
        cache_key = f'leave_balance:{employee_id}'
        cache.delete(cache_key)
    
    @staticmethod
    def get_user_permissions(user_id: str) -> Any:
        """Get cached user permissions"""
        cache_key = f'user_permissions:{user_id}'
        return cache.get(cache_key)
    
    @staticmethod
    def set_user_permissions(user_id: str, data: Any):
        """Cache user permissions"""
        cache_key = f'user_permissions:{user_id}'
        cache.set(cache_key, data, CacheManager.TIMEOUT_VERY_LONG)
    
    @staticmethod
    def invalidate_user_permissions(user_id: str):
        """Invalidate user permissions cache"""
        cache_key = f'user_permissions:{user_id}'
        cache.delete(cache_key)
