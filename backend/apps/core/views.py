"""
Core views for the HRMS application.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Health check endpoint for the API.
    """
    return Response({
        'status': 'healthy',
        'message': 'Admire HRMS API is running',
        'user': request.user.username,
        'company': request.user.company.name
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for the current user's company.
    """
    # This is a placeholder for dashboard statistics
    # In a real implementation, this would calculate actual metrics
    
    return Response({
        'total_employees': 0,
        'present_today': 0,
        'on_leave': 0,
        'pending_leave_requests': 0,
        'recent_activities': []
    })