"""
API Documentation and Testing Views.
Provides comprehensive API documentation and testing interface.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.conf import settings


class APIInfoView(APIView):
    """
    API Information endpoint providing version, status, and available endpoints.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Core'],
        summary='API Information',
        description='Get API version, status, and available documentation endpoints.',
        responses={
            200: OpenApiResponse(
                description='API information',
                response={
                    'type': 'object',
                    'properties': {
                        'version': {'type': 'string'},
                        'status': {'type': 'string'},
                        'documentation': {'type': 'object'},
                        'endpoints': {'type': 'object'},
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get API information and available endpoints."""
        base_url = request.build_absolute_uri('/')[:-1]
        
        return Response({
            'version': '1.0.0',
            'status': 'operational',
            'title': 'Admire HRMS API',
            'description': 'Comprehensive Human Resource Management System API',
            'documentation': {
                'swagger_ui': f'{base_url}/api/docs/',
                'redoc': f'{base_url}/api/redoc/',
                'openapi_schema': f'{base_url}/api/schema/',
            },
            'endpoints': {
                'authentication': {
                    'login': f'{base_url}/api/v1/auth/login/',
                    'logout': f'{base_url}/api/v1/auth/logout/',
                    'refresh': f'{base_url}/api/v1/auth/token/refresh/',
                    'profile': f'{base_url}/api/v1/auth/profile/',
                },
                'employees': f'{base_url}/api/v1/employees/',
                'attendance': f'{base_url}/api/v1/attendance/',
                'leave': f'{base_url}/api/v1/leave/',
                'payroll': f'{base_url}/api/v1/payroll/',
                'users': f'{base_url}/api/v1/users/',
                'roles': f'{base_url}/api/v1/roles/',
                'departments': f'{base_url}/api/v1/departments/',
                'dashboard': f'{base_url}/api/v1/dashboard/',
            },
            'features': [
                'JWT Authentication',
                'Multi-tenant Support',
                'Role-Based Access Control',
                'Biometric Attendance',
                'Leave Management',
                'Payroll Processing',
                'Real-time WebSocket Updates',
                'Comprehensive Reporting',
            ],
            'rate_limiting': {
                'enabled': True,
                'default_rate': '100/hour',
                'burst_rate': '20/minute',
            }
        })


class APIHealthView(APIView):
    """
    API Health Check endpoint.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Core'],
        summary='Health Check',
        description='Check API health status and dependencies.',
        responses={
            200: OpenApiResponse(
                description='API is healthy',
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string'},
                        'database': {'type': 'string'},
                        'cache': {'type': 'string'},
                        'celery': {'type': 'string'},
                    }
                }
            ),
            503: OpenApiResponse(description='Service unavailable'),
        }
    )
    def get(self, request):
        """Check health of API and its dependencies."""
        health_status = {
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected',
            'celery': 'running',
        }
        
        # Check database connection
        try:
            from django.db import connection
            connection.ensure_connection()
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check Redis/Cache connection
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                raise Exception('Cache read/write failed')
        except Exception as e:
            health_status['cache'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check Celery workers
        try:
            from admire_hrms.celery import app
            inspect = app.control.inspect()
            active_workers = inspect.active()
            if not active_workers:
                health_status['celery'] = 'no workers available'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['celery'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        status_code = status.HTTP_200_OK if health_status['status'] != 'unhealthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=status_code)


class APIMetricsView(APIView):
    """
    API Metrics endpoint providing performance and usage statistics.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Core'],
        summary='API Metrics',
        description='Get API performance metrics and usage statistics (requires authentication).',
        responses={
            200: OpenApiResponse(
                description='API metrics',
                response={
                    'type': 'object',
                    'properties': {
                        'requests': {'type': 'object'},
                        'response_times': {'type': 'object'},
                        'errors': {'type': 'object'},
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get API performance metrics."""
        # This is a placeholder - in production, integrate with monitoring tools
        return Response({
            'requests': {
                'total': 0,
                'success': 0,
                'errors': 0,
                'rate': '0/min',
            },
            'response_times': {
                'avg': 0,
                'p50': 0,
                'p95': 0,
                'p99': 0,
            },
            'errors': {
                '4xx': 0,
                '5xx': 0,
            },
            'note': 'Metrics integration pending - connect to monitoring service'
        })
