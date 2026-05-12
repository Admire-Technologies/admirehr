"""
Health check and monitoring endpoints
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from apps.core.monitoring import PerformanceMonitor, AlertManager
import logging

logger = logging.getLogger('admire_hrms.health')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return Response({
        'status': 'healthy',
        'service': 'admire-hrms-backend',
        'version': '1.0.0',
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_detailed(request):
    """
    Detailed health check with dependency status
    """
    health_status = {
        'status': 'healthy',
        'service': 'admire-hrms-backend',
        'version': '1.0.0',
        'checks': {}
    }
    
    overall_healthy = True
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check Redis/Cache
    try:
        cache.set('health_check', 'ok', timeout=10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
        else:
            raise Exception('Cache read/write failed')
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache connection failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check Celery
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            health_status['checks']['celery'] = {
                'status': 'healthy',
                'message': f'Celery workers active: {len(stats)}'
            }
        else:
            health_status['checks']['celery'] = {
                'status': 'degraded',
                'message': 'No Celery workers found'
            }
    except Exception as e:
        health_status['checks']['celery'] = {
            'status': 'unhealthy',
            'message': f'Celery check failed: {str(e)}'
        }
        overall_healthy = False
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration
    Returns 200 when service is ready to accept traffic
    """
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache
        cache.set('readiness_check', 'ok', timeout=10)
        
        return Response({
            'status': 'ready',
            'message': 'Service is ready to accept traffic'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'not_ready',
            'message': f'Service is not ready: {str(e)}'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    Returns 200 if service is alive (even if not ready)
    """
    return Response({
        'status': 'alive',
        'message': 'Service is alive'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def metrics_endpoint(request):
    """
    Metrics endpoint for monitoring systems
    Requires authentication
    """
    try:
        # Collect all metrics
        system_metrics = PerformanceMonitor.get_system_metrics()
        db_metrics = PerformanceMonitor.get_database_metrics()
        redis_metrics = PerformanceMonitor.get_redis_metrics()
        celery_metrics = PerformanceMonitor.get_celery_metrics()
        
        # Combine all metrics
        all_metrics = {
            'timestamp': cache.get('metrics_timestamp') or 'N/A',
            'system': system_metrics,
            'database': db_metrics,
            'redis': redis_metrics,
            'celery': celery_metrics,
        }
        
        # Check for alerts
        alerts = AlertManager.check_thresholds({
            **system_metrics,
            **db_metrics,
            **redis_metrics,
        })
        
        if alerts:
            all_metrics['alerts'] = alerts
        
        return Response(all_metrics, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}", exc_info=True)
        return Response({
            'error': 'Failed to collect metrics',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def system_status(request):
    """
    Comprehensive system status endpoint
    Requires authentication
    """
    try:
        # Get all metrics
        system_metrics = PerformanceMonitor.get_system_metrics()
        db_metrics = PerformanceMonitor.get_database_metrics()
        redis_metrics = PerformanceMonitor.get_redis_metrics()
        celery_metrics = PerformanceMonitor.get_celery_metrics()
        
        # Determine overall status
        overall_status = 'healthy'
        
        if not db_metrics.get('db_connected'):
            overall_status = 'critical'
        elif not redis_metrics.get('redis_connected'):
            overall_status = 'degraded'
        elif not celery_metrics.get('celery_connected'):
            overall_status = 'degraded'
        elif system_metrics.get('cpu_percent', 0) > 90:
            overall_status = 'degraded'
        elif system_metrics.get('memory_percent', 0) > 90:
            overall_status = 'degraded'
        
        return Response({
            'status': overall_status,
            'timestamp': cache.get('status_timestamp') or 'N/A',
            'components': {
                'database': 'healthy' if db_metrics.get('db_connected') else 'unhealthy',
                'cache': 'healthy' if redis_metrics.get('redis_connected') else 'unhealthy',
                'celery': 'healthy' if celery_metrics.get('celery_connected') else 'unhealthy',
                'system': 'healthy' if system_metrics.get('cpu_percent', 0) < 80 else 'degraded',
            },
            'metrics': {
                'system': system_metrics,
                'database': db_metrics,
                'redis': redis_metrics,
                'celery': celery_metrics,
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        return Response({
            'status': 'unknown',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
