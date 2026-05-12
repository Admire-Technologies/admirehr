"""
API Throttling Management Views.
Provides endpoints to monitor and manage API rate limiting.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .throttling import get_throttle_status, reset_throttle
from apps.authentication.permissions import IsCompanyAdmin


class ThrottleStatusView(APIView):
    """
    Get current throttle status for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Core'],
        summary='Get Throttle Status',
        description='Get current API rate limit status for the authenticated user.',
        responses={
            200: OpenApiResponse(
                description='Throttle status',
                response={
                    'type': 'object',
                    'properties': {
                        'throttled': {'type': 'boolean'},
                        'limits': {'type': 'object'},
                        'remaining': {'type': 'object'},
                        'reset_times': {'type': 'object'},
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get throttle status for current user."""
        throttle_status = get_throttle_status(user=request.user)
        return Response(throttle_status)


class ThrottleResetView(APIView):
    """
    Reset throttle limits for a user (admin only).
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    @extend_schema(
        tags=['Core'],
        summary='Reset Throttle Limits',
        description='Reset API rate limit counters for a specific user (admin only).',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'format': 'uuid'},
                    'scope': {'type': 'string', 'nullable': True},
                }
            }
        },
        responses={
            200: OpenApiResponse(description='Throttle limits reset successfully'),
            400: OpenApiResponse(description='Bad request'),
            404: OpenApiResponse(description='User not found'),
        }
    )
    def post(self, request):
        """Reset throttle limits for a user."""
        user_id = request.data.get('user_id')
        scope = request.data.get('scope')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user from same company
        from apps.authentication.models import User
        try:
            user = User.objects.get(id=user_id, company=request.user.company)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Reset throttle
        reset_throttle(user=user, scope=scope)
        
        return Response({
            'message': f'Throttle limits reset for user {user.username}',
            'scope': scope or 'all'
        })


class RateLimitConfigView(APIView):
    """
    Get and update rate limit configuration (admin only).
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    @extend_schema(
        tags=['Core'],
        summary='Get Rate Limit Configuration',
        description='Get current API rate limit configuration for the company.',
        responses={
            200: OpenApiResponse(
                description='Rate limit configuration',
                response={
                    'type': 'object',
                    'properties': {
                        'default': {'type': 'string'},
                        'roles': {'type': 'object'},
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get rate limit configuration."""
        company = request.user.company
        settings = company.settings or {}
        rate_limits = settings.get('api_rate_limits', {
            'default': '1000/hour',
            'roles': {}
        })
        
        return Response(rate_limits)

    @extend_schema(
        tags=['Core'],
        summary='Update Rate Limit Configuration',
        description='Update API rate limit configuration for the company.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'default': {'type': 'string'},
                    'roles': {'type': 'object'},
                }
            }
        },
        responses={
            200: OpenApiResponse(description='Configuration updated successfully'),
            400: OpenApiResponse(description='Bad request'),
        }
    )
    def put(self, request):
        """Update rate limit configuration."""
        company = request.user.company
        settings = company.settings or {}
        
        # Validate rate limit format
        default_limit = request.data.get('default')
        role_limits = request.data.get('roles', {})
        
        if default_limit:
            # Validate format: number/period (e.g., "1000/hour")
            try:
                num, period = default_limit.split('/')
                int(num)
                if period not in ['second', 'minute', 'hour', 'day']:
                    raise ValueError()
            except (ValueError, AttributeError):
                return Response(
                    {'error': 'Invalid rate limit format. Use: number/period (e.g., "1000/hour")'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update settings
        settings['api_rate_limits'] = {
            'default': default_limit or '1000/hour',
            'roles': role_limits
        }
        company.settings = settings
        company.save()
        
        return Response({
            'message': 'Rate limit configuration updated successfully',
            'config': settings['api_rate_limits']
        })
