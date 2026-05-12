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



# GDPR Compliance Views

class GDPRDataExportView(APIView):
    """
    API view for GDPR data export (Right to Access).
    Allows employees to export all their personal data.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(description="Employee data exported successfully"),
            404: OpenApiResponse(description="Employee not found"),
        },
        description="Export all employee data for GDPR compliance"
    )
    def get(self, request, employee_id=None):
        """
        Export all data for an employee.
        Users can only export their own data unless they are admins.
        """
        from apps.employees.models import Employee
        from apps.core.gdpr import get_gdpr_compliance
        
        # Determine which employee to export
        if employee_id:
            # Check permissions
            if not request.user.is_company_admin and not request.user.is_superuser:
                # Check if user is requesting their own data
                try:
                    employee = Employee.objects.get(id=employee_id, company=request.user.company)
                    if not hasattr(request.user, 'employee') or request.user.employee.id != employee.id:
                        return Response({
                            'error': 'You can only export your own data'
                        }, status=status.HTTP_403_FORBIDDEN)
                except Employee.DoesNotExist:
                    return Response({
                        'error': 'Employee not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                try:
                    employee = Employee.objects.get(id=employee_id, company=request.user.company)
                except Employee.DoesNotExist:
                    return Response({
                        'error': 'Employee not found'
                    }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Export current user's employee data
            if not hasattr(request.user, 'employee') or not request.user.employee:
                return Response({
                    'error': 'No employee record associated with your account'
                }, status=status.HTTP_404_NOT_FOUND)
            employee = request.user.employee
        
        # Export data
        gdpr = get_gdpr_compliance()
        data = gdpr.export_employee_data(employee)
        
        # Log the export
        from apps.authentication.models import AuditLog
        AuditLog.log_action(
            user=request.user,
            action='export',
            module='gdpr',
            description=f'GDPR data export for employee {employee.employee_id}',
            content_object=employee,
            request=request
        )
        
        return Response(data, status=status.HTTP_200_OK)


class GDPRDataDeletionView(APIView):
    """
    API view for GDPR data deletion (Right to be Forgotten).
    Allows deletion or anonymization of employee data.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(description="Employee data deleted/anonymized successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Employee not found"),
        },
        description="Delete or anonymize employee data for GDPR compliance"
    )
    def post(self, request, employee_id):
        """
        Delete or anonymize employee data.
        Only company admins can perform this action.
        """
        from apps.employees.models import Employee
        from apps.core.gdpr import get_gdpr_compliance
        
        # Check permissions
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can delete employee data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get employee
        try:
            employee = Employee.objects.get(id=employee_id, company=request.user.company)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get anonymize flag (default to True for safety)
        anonymize = request.data.get('anonymize', True)
        
        # Delete/anonymize data
        gdpr = get_gdpr_compliance()
        summary = gdpr.delete_employee_data(employee, anonymize=anonymize)
        
        # Log the deletion
        from apps.authentication.models import AuditLog
        AuditLog.log_action(
            user=request.user,
            action='delete',
            module='gdpr',
            description=f'GDPR data {"anonymization" if anonymize else "deletion"} for employee {employee.employee_id}',
            changes=summary,
            request=request
        )
        
        return Response({
            'message': f'Employee data {"anonymized" if anonymize else "deleted"} successfully',
            'summary': summary
        }, status=status.HTTP_200_OK)


class GDPRDataProcessingReportView(APIView):
    """
    API view for GDPR data processing report.
    Provides information about data processing activities.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(description="Data processing report generated"),
            403: OpenApiResponse(description="Permission denied"),
        },
        description="Generate GDPR data processing report"
    )
    def get(self, request):
        """
        Generate data processing report for the company.
        Only company admins can access this report.
        """
        from apps.core.gdpr import get_gdpr_compliance
        
        # Check permissions
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can access data processing reports'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate report
        gdpr = get_gdpr_compliance()
        report = gdpr.generate_data_processing_report(request.user.company)
        
        return Response(report, status=status.HTTP_200_OK)


# Security Management Views

class SecurityEventListView(APIView):
    """
    API view for listing security events.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(description="Security events retrieved"),
            403: OpenApiResponse(description="Permission denied"),
        },
        description="List security events for the company"
    )
    def get(self, request):
        """
        List security events.
        Only company admins can access security events.
        """
        from apps.core.models import SecurityEvent
        
        # Check permissions
        if not request.user.is_company_admin and not request.user.is_superuser:
            return Response({
                'error': 'Only company administrators can access security events'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        event_type = request.query_params.get('event_type')
        severity = request.query_params.get('severity')
        resolved = request.query_params.get('resolved')
        
        # Build query
        queryset = SecurityEvent.objects.filter(company=request.user.company)
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if resolved is not None:
            queryset = queryset.filter(resolved=resolved.lower() == 'true')
        
        # Limit to recent events
        queryset = queryset.order_by('-created_at')[:100]
        
        # Serialize
        events = [
            {
                'id': str(event.id),
                'event_type': event.event_type,
                'severity': event.severity,
                'description': event.description,
                'user': event.user.username if event.user else None,
                'ip_address': event.ip_address,
                'created_at': event.created_at.isoformat(),
                'resolved': event.resolved,
            }
            for event in queryset
        ]
        
        return Response({
            'count': len(events),
            'events': events
        }, status=status.HTTP_200_OK)
