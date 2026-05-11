"""
Dashboard and reporting API views.
"""
from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.http import HttpResponse
from django.utils import timezone
from .models import DashboardWidget, ScheduledReport
from .serializers import (
    DashboardWidgetSerializer,
    ScheduledReportSerializer,
    DashboardMetricsSerializer
)
from .services import DashboardMetricsService, ReportGenerationService
from .export_utils import ReportExporter


class DashboardMetricsView(APIView):
    """
    API view for real-time dashboard metrics.
    
    GET /api/v1/dashboard/metrics/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get real-time dashboard metrics."""
        service = DashboardMetricsService(request.user.company)
        metrics = service.get_real_time_metrics()
        serializer = DashboardMetricsSerializer(metrics)
        return Response(serializer.data)


class AttendanceTrendsView(APIView):
    """
    API view for attendance trends data.
    
    GET /api/v1/dashboard/attendance-trends/?days=30
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get attendance trends for specified number of days."""
        days = int(request.query_params.get('days', 30))
        service = DashboardMetricsService(request.user.company)
        trends = service.get_attendance_trends(days)
        return Response({'trends': trends})


class LeavePatternsView(APIView):
    """
    API view for leave patterns data.
    
    GET /api/v1/dashboard/leave-patterns/?months=6
    """
    permission_classes = [permissions.IsAuthenticated]

    
    def get(self, request):
        """Get leave patterns for specified number of months."""
        months = int(request.query_params.get('months', 6))
        service = DashboardMetricsService(request.user.company)
        patterns = service.get_leave_patterns(months)
        return Response({'patterns': patterns})


class PayrollSummaryView(APIView):
    """
    API view for payroll summary data.
    
    GET /api/v1/dashboard/payroll-summary/?period_start=2024-01-01&period_end=2024-01-31
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get payroll summary for specified period."""
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')
        
        if not period_start or not period_end:
            return Response(
                {'error': 'period_start and period_end are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = DashboardMetricsService(request.user.company)
        summary = service.get_payroll_summary(start_date, end_date)
        return Response(summary)


class ReportGenerationView(APIView):
    """
    API view for generating reports with filters.
    
    GET /api/v1/dashboard/reports/generate/?type=attendance&start_date=2024-01-01&end_date=2024-01-31
    """
    permission_classes = [permissions.IsAuthenticated]

    
    def get(self, request):
        """Generate report based on type and filters."""
        report_type = request.query_params.get('type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        department_id = request.query_params.get('department_id')
        employee_id = request.query_params.get('employee_id')
        
        if not report_type or not start_date or not end_date:
            return Response(
                {'error': 'type, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = ReportGenerationService(request.user.company)
        
        if report_type == 'attendance':
            report_data = service.generate_attendance_report(
                start, end, department_id, employee_id
            )
        elif report_type == 'leave':
            leave_status = request.query_params.get('status')
            report_data = service.generate_leave_report(
                start, end, department_id, employee_id, leave_status
            )
        else:
            return Response(
                {'error': f'Invalid report type: {report_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(report_data)


class ReportExportView(APIView):
    """
    API view for exporting reports in various formats.
    
    GET /api/v1/dashboard/reports/export/?type=attendance&format=pdf&start_date=2024-01-01&end_date=2024-01-31
    """
    permission_classes = [permissions.IsAuthenticated]

    
    def get(self, request):
        """Export report in specified format."""
        report_type = request.query_params.get('type')
        export_format = request.query_params.get('format', 'pdf')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        department_id = request.query_params.get('department_id')
        employee_id = request.query_params.get('employee_id')
        
        if not report_type or not start_date or not end_date:
            return Response(
                {'error': 'type, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report data
        service = ReportGenerationService(request.user.company)
        
        if report_type == 'attendance':
            report_data = service.generate_attendance_report(
                start, end, department_id, employee_id
            )
            title = 'Attendance Report'
            headers = ['Employee ID', 'Name', 'Department', 'Days Present', 'Total Hours', 'Avg Hours']
            data = [
                {
                    'Employee ID': emp['employee__employee_id'],
                    'Name': f"{emp['employee__first_name']} {emp['employee__last_name']}",
                    'Department': emp['employee__department__name'],
                    'Days Present': emp['days_present'],
                    'Total Hours': f"{emp['total_hours']:.2f}" if emp['total_hours'] else '0.00',
                    'Avg Hours': f"{emp['avg_hours']:.2f}" if emp['avg_hours'] else '0.00'
                }
                for emp in report_data['employee_data']
            ]
            summary = report_data['summary']
        elif report_type == 'leave':
            leave_status = request.query_params.get('status')
            report_data = service.generate_leave_report(
                start, end, department_id, employee_id, leave_status
            )
            title = 'Leave Report'
            headers = ['Employee ID', 'Name', 'Department', 'Total Requests', 'Approved', 'Total Days']
            data = [
                {
                    'Employee ID': emp['employee__employee_id'],
                    'Name': f"{emp['employee__first_name']} {emp['employee__last_name']}",
                    'Department': emp['employee__department__name'],
                    'Total Requests': emp['total_requests'],
                    'Approved': emp['approved'],
                    'Total Days': emp['total_days']
                }
                for emp in report_data['employee_data']
            ]
            summary = report_data['summary']
        else:
            return Response(
                {'error': f'Invalid report type: {report_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        # Export in requested format
        exporter = ReportExporter()
        
        if export_format == 'csv':
            content = exporter.export_to_csv(data, headers)
            response = HttpResponse(content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
        elif export_format == 'excel':
            content = exporter.export_to_excel(data, headers, f'{report_type.title()} Report')
            response = HttpResponse(
                content.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'
        elif export_format == 'pdf':
            content = exporter.export_to_pdf(title, data, headers, summary)
            response = HttpResponse(content.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'
        else:
            return Response(
                {'error': f'Invalid export format: {export_format}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return response


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard widget configurations.
    
    GET    /api/v1/dashboard/widgets/
    POST   /api/v1/dashboard/widgets/
    PUT    /api/v1/dashboard/widgets/{id}/
    DELETE /api/v1/dashboard/widgets/{id}/
    """
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DashboardWidget.objects.filter(
            user=self.request.user,
            company=self.request.user.company
        )


class ScheduledReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing scheduled reports.
    
    GET    /api/v1/dashboard/scheduled-reports/
    POST   /api/v1/dashboard/scheduled-reports/
    PUT    /api/v1/dashboard/scheduled-reports/{id}/
    DELETE /api/v1/dashboard/scheduled-reports/{id}/
    """
    serializer_class = ScheduledReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ScheduledReport.objects.filter(
            company=self.request.user.company
        )
