"""
Application monitoring and metrics collection
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import psutil
import redis

logger = logging.getLogger('admire_hrms.monitoring')


class PerformanceMonitor:
    """
    Monitor application performance metrics
    """
    
    @staticmethod
    def measure_execution_time(func: Callable) -> Callable:
        """
        Decorator to measure function execution time
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            logger.info(
                f"Function {func.__name__} executed",
                extra={
                    'function': func.__name__,
                    'duration': round(duration, 2),
                    'module': func.__module__,
                }
            )
            
            return result
        return wrapper
    
    @staticmethod
    def get_system_metrics() -> dict:
        """
        Get current system metrics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    @staticmethod
    def get_database_metrics() -> dict:
        """
        Get database connection metrics
        """
        try:
            # Get number of queries
            queries_count = len(connection.queries)
            
            # Test database connection
            from django.db import connections
            db_conn = connections['default']
            
            start_time = time.time()
            db_conn.cursor()
            db_latency = (time.time() - start_time) * 1000
            
            return {
                'queries_count': queries_count,
                'db_latency_ms': round(db_latency, 2),
                'db_connected': True,
            }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {
                'db_connected': False,
                'error': str(e),
            }
    
    @staticmethod
    def get_redis_metrics() -> dict:
        """
        Get Redis connection metrics
        """
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            
            start_time = time.time()
            redis_client.ping()
            redis_latency = (time.time() - start_time) * 1000
            
            info = redis_client.info()
            
            return {
                'redis_connected': True,
                'redis_latency_ms': round(redis_latency, 2),
                'redis_used_memory_mb': info.get('used_memory', 0) / (1024 * 1024),
                'redis_connected_clients': info.get('connected_clients', 0),
            }
        except Exception as e:
            logger.error(f"Error getting Redis metrics: {e}")
            return {
                'redis_connected': False,
                'error': str(e),
            }
    
    @staticmethod
    def get_celery_metrics() -> dict:
        """
        Get Celery worker metrics
        """
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            
            # Get active tasks
            active = inspect.active()
            active_count = sum(len(tasks) for tasks in (active or {}).values())
            
            # Get scheduled tasks
            scheduled = inspect.scheduled()
            scheduled_count = sum(len(tasks) for tasks in (scheduled or {}).values())
            
            # Get registered tasks
            registered = inspect.registered()
            registered_count = sum(len(tasks) for tasks in (registered or {}).values())
            
            return {
                'celery_connected': True,
                'active_tasks': active_count,
                'scheduled_tasks': scheduled_count,
                'registered_tasks': registered_count,
            }
        except Exception as e:
            logger.error(f"Error getting Celery metrics: {e}")
            return {
                'celery_connected': False,
                'error': str(e),
            }


class AlertManager:
    """
    Manage system alerts and notifications
    """
    
    ALERT_THRESHOLDS = {
        'cpu_percent': 80,
        'memory_percent': 85,
        'disk_percent': 90,
        'db_latency_ms': 1000,
        'redis_latency_ms': 100,
    }
    
    @classmethod
    def check_thresholds(cls, metrics: dict) -> list:
        """
        Check if any metrics exceed thresholds
        """
        alerts = []
        
        for metric, threshold in cls.ALERT_THRESHOLDS.items():
            if metric in metrics and metrics[metric] > threshold:
                alert = {
                    'metric': metric,
                    'value': metrics[metric],
                    'threshold': threshold,
                    'severity': cls.get_severity(metric, metrics[metric], threshold),
                    'timestamp': time.time(),
                }
                alerts.append(alert)
                
                # Log alert
                logger.warning(
                    f"Alert: {metric} exceeded threshold",
                    extra=alert
                )
        
        return alerts
    
    @staticmethod
    def get_severity(metric: str, value: float, threshold: float) -> str:
        """
        Determine alert severity
        """
        ratio = value / threshold
        
        if ratio >= 1.5:
            return 'critical'
        elif ratio >= 1.2:
            return 'high'
        elif ratio >= 1.0:
            return 'medium'
        else:
            return 'low'
    
    @classmethod
    def send_alert(cls, alert: dict):
        """
        Send alert notification (email, Slack, etc.)
        """
        # This would integrate with notification services
        logger.critical(
            f"ALERT: {alert['metric']} = {alert['value']} (threshold: {alert['threshold']})",
            extra=alert
        )
        
        # Store alert in cache for dashboard
        cache_key = f"alert:{alert['metric']}:{int(alert['timestamp'])}"
        cache.set(cache_key, alert, timeout=3600)  # Store for 1 hour


def monitor_api_endpoint(func: Callable) -> Callable:
    """
    Decorator to monitor API endpoint performance
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            status = 'success'
            return result
        except Exception as e:
            status = 'error'
            logger.error(
                f"API endpoint error: {func.__name__}",
                extra={
                    'function': func.__name__,
                    'error': str(e),
                },
                exc_info=True
            )
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            
            # Log endpoint metrics
            logger.info(
                f"API endpoint: {func.__name__}",
                extra={
                    'endpoint': func.__name__,
                    'duration': round(duration, 2),
                    'status': status,
                }
            )
            
            # Check for slow endpoints
            if duration > 1000:  # More than 1 second
                logger.warning(
                    f"Slow API endpoint: {func.__name__}",
                    extra={
                        'endpoint': func.__name__,
                        'duration': round(duration, 2),
                    }
                )
    
    return wrapper
