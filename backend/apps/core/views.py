"""
Core views for the HRMS application.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Company
from .serializers import (
    CompanySerializer, 
    CompanyRegistrationSerializer, 
    CompanySettingsSerializer
)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
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
@permission_classes([permissions.IsAuthenticated])
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


class CompanyRegistrationView(APIView):
    """
    API view for company registration.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=CompanyRegistrationSerializer,
        responses={
            201: OpenApiResponse(description="Company registered successfully"),
            400: OpenApiResponse(description="Validation error"),
        },
        description="Register a new company with admin user"
    )
    def post(self, request):
        """
        Register a new company with an admin user.
        """
        serializer = CompanyRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    company = serializer.save()
                    
                return Response({
                    'message': 'Company registered successfully',
                    'company': {
                        'id': str(company.id),
                        'name': company.name,
                        'code': company.code
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': 'Failed to register company',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailView(RetrieveUpdateAPIView):
    """
    API view for retrieving and updating company details.
    """
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the current user's company.
        """
        return self.request.user.company
    
    @extend_schema(
        responses={
            200: CompanySerializer,
            403: OpenApiResponse(description="Permission denied"),
        },
        description="Get current company details"
    )
    def get(self, request, *args, **kwargs):
        """
        Get current company details.
        """
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        request=CompanySerializer,
        responses={
            200: CompanySerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
        },
        description="Update current company details"
    )
    def put(self, request, *args, **kwargs):
        """
        Update current company details.
        """
        # Only company admins can update company details
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can update company details'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().put(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        """
        Partially update current company details.
        """
        # Only company admins can update company details
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can update company details'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().patch(request, *args, **kwargs)


class CompanySettingsView(RetrieveUpdateAPIView):
    """
    API view for managing company settings.
    """
    serializer_class = CompanySettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the current user's company.
        """
        return self.request.user.company
    
    @extend_schema(
        responses={
            200: CompanySettingsSerializer,
            403: OpenApiResponse(description="Permission denied"),
        },
        description="Get current company settings"
    )
    def get(self, request, *args, **kwargs):
        """
        Get current company settings.
        """
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        request=CompanySettingsSerializer,
        responses={
            200: CompanySettingsSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
        },
        description="Update current company settings"
    )
    def put(self, request, *args, **kwargs):
        """
        Update current company settings.
        """
        # Only company admins can update settings
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can update company settings'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().put(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        """
        Partially update current company settings.
        """
        # Only company admins can update settings
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can update company settings'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().patch(request, *args, **kwargs)