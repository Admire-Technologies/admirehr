"""
Attendance management views.
"""

import logging
from datetime import datetime
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Sum, Avg
from .models import AttendanceRecord
from .serializers import (
    AttendanceRecordSerializer,
    AttendanceManualEntrySerializer,
    AttendanceReportSerializer,
    AttendanceSummarySerializer
)
from .face_plugin_service import get_face_plugin_service, BiometricVerificationError
from .policy import get_attendance_policy
from .export_utils import export_attendance_report
from apps.core.ws_utils import send_attendance_update
from apps.employees.models import Employee

logger = logging.getLogger(__name__)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records.
    Supports CRUD operations, filtering, reporting, and export.
    """
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = AttendanceRecord.objects.filter(company=self.request.user.company)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by employee if provided
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee__employee_id=employee_id)
        
        # Filter by department if provided
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(employee__department__id=department_id)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by biometric verification
        biometric_verified = self.request.query_params.get('biometric_verified')
        if biometric_verified is not None:
            queryset = queryset.filter(biometric_verified=biometric_verified.lower() == 'true')
        
        return queryset.select_related('employee', 'employee__department').order_by('-date', 'employee__first_name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get attendance summary statistics.
        """
        queryset = self.get_queryset()
        
        # Calculate summary statistics
        total_records = queryset.count()
        present_count = queryset.filter(status='present').count()
        late_count = queryset.filter(status='late').count()
        absent_count = queryset.filter(status='absent').count()
        half_day_count = queryset.filter(status='half_day').count()
        
        # Calculate working hours statistics
        records_with_hours = queryset.exclude(working_hours__isnull=True)
        total_working_hours = 0
        total_overtime_hours = 0
        avg_working_hours = 0
        
        if records_with_hours.exists():
            total_hours = sum(float(r.working_hours) for r in records_with_hours)
            total_working_hours = total_hours
            avg_working_hours = total_hours / records_with_hours.count()
            
            # Calculate total overtime
            overtime_threshold = float(request.user.company.overtime_threshold_hours)
            for record in records_with_hours:
                hours = float(record.working_hours)
                if hours > overtime_threshold:
                    total_overtime_hours += (hours - overtime_threshold)
        
        # Get unique employees count
        unique_employees = queryset.values('employee').distinct().count()
        
        # Get date range
        date_range = {}
        if queryset.exists():
            date_range = {
                'start': queryset.order_by('date').first().date.isoformat(),
                'end': queryset.order_by('-date').first().date.isoformat()
            }
        
        summary_data = {
            'total_records': total_records,
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'half_day': half_day_count,
            'average_working_hours': round(avg_working_hours, 2),
            'total_working_hours': round(total_working_hours, 2),
            'total_overtime_hours': round(total_overtime_hours, 2),
            'unique_employees': unique_employees,
            'date_range': date_range
        }
        
        serializer = AttendanceSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'post'])
    def reports(self, request):
        """
        Generate attendance reports with filtering and aggregation.
        Supports export to PDF and Excel formats.
        """
        if request.method == 'POST':
            # Validate report parameters
            report_serializer = AttendanceReportSerializer(data=request.data)
            if not report_serializer.is_valid():
                return Response(report_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            params = report_serializer.validated_data
        else:
            # GET request - use query params
            params = {
                'start_date': request.query_params.get('start_date'),
                'end_date': request.query_params.get('end_date'),
                'employee_id': request.query_params.get('employee_id'),
                'department_id': request.query_params.get('department_id'),
                'status': request.query_params.get('status'),
                'export_format': request.query_params.get('export_format', 'json')
            }
        
        # Build queryset with filters
        queryset = AttendanceRecord.objects.filter(company=request.user.company)
        
        if params.get('start_date'):
            queryset = queryset.filter(date__gte=params['start_date'])
        if params.get('end_date'):
            queryset = queryset.filter(date__lte=params['end_date'])
        if params.get('employee_id'):
            queryset = queryset.filter(employee__employee_id=params['employee_id'])
        if params.get('department_id'):
            queryset = queryset.filter(employee__department__id=params['department_id'])
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])
        
        queryset = queryset.select_related('employee', 'employee__department').order_by('-date', 'employee__first_name')
        
        # Calculate summary statistics
        total_records = queryset.count()
        present_count = queryset.filter(status='present').count()
        late_count = queryset.filter(status='late').count()
        absent_count = queryset.filter(status='absent').count()
        half_day_count = queryset.filter(status='half_day').count()
        
        # Calculate working hours
        records_with_hours = queryset.exclude(working_hours__isnull=True)
        total_working_hours = 0
        total_overtime_hours = 0
        avg_working_hours = 0
        
        if records_with_hours.exists():
            total_hours = sum(float(r.working_hours) for r in records_with_hours)
            total_working_hours = total_hours
            avg_working_hours = total_hours / records_with_hours.count()
            
            # Calculate total overtime
            overtime_threshold = float(request.user.company.overtime_threshold_hours)
            for record in records_with_hours:
                hours = float(record.working_hours)
                if hours > overtime_threshold:
                    total_overtime_hours += (hours - overtime_threshold)
        
        # Get unique employees
        unique_employees = queryset.values('employee').distinct().count()
        
        # Get date range
        date_range = {}
        if queryset.exists():
            date_range = {
                'start': queryset.order_by('date').first().date.isoformat(),
                'end': queryset.order_by('-date').first().date.isoformat()
            }
        
        summary = {
            'total_records': total_records,
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'half_day': half_day_count,
            'average_working_hours': round(avg_working_hours, 2),
            'total_working_hours': round(total_working_hours, 2),
            'total_overtime_hours': round(total_overtime_hours, 2),
            'unique_employees': unique_employees,
            'date_range': date_range
        }
        
        # Handle export formats
        export_format = params.get('export_format', 'json')
        
        if export_format in ['pdf', 'excel']:
            # Export to file
            records_list = list(queryset)
            return export_attendance_report(
                records_list,
                summary,
                request.user.company,
                export_format
            )
        
        # Return JSON response
        return Response({
            'summary': summary,
            'records': AttendanceRecordSerializer(queryset, many=True).data
        })
    
    @action(detail=False, methods=['post'])
    def manual_entry(self, request):
        """
        Create manual attendance entry (without biometric verification).
        Requires appropriate permissions.
        """
        serializer = AttendanceManualEntrySerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            attendance = serializer.save()
            
            # Send WebSocket update
            send_attendance_update(
                str(request.user.company.id),
                {
                    'employee_id': str(attendance.employee.id),
                    'employee_name': attendance.employee.full_name,
                    'action': 'manual_entry',
                    'timestamp': timezone.now().isoformat(),
                    'date': attendance.date.isoformat(),
                    'status': attendance.status,
                    'biometric_verified': False
                }
            )
            
            return Response(
                AttendanceRecordSerializer(attendance).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put', 'patch'])
    def correct(self, request, pk=None):
        """
        Correct/update an existing attendance record.
        Requires appropriate permissions.
        """
        attendance = self.get_object()
        
        serializer = AttendanceManualEntrySerializer(
            attendance,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_attendance = serializer.save()
            
            # Send WebSocket update
            send_attendance_update(
                str(request.user.company.id),
                {
                    'employee_id': str(updated_attendance.employee.id),
                    'employee_name': updated_attendance.employee.full_name,
                    'action': 'correction',
                    'timestamp': timezone.now().isoformat(),
                    'date': updated_attendance.date.isoformat(),
                    'status': updated_attendance.status
                }
            )
            
            return Response(AttendanceRecordSerializer(updated_attendance).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Get real-time dashboard statistics for today.
        """
        today = timezone.now().date()
        company = request.user.company
        
        # Get today's attendance
        today_attendance = AttendanceRecord.objects.filter(
            company=company,
            date=today
        )
        
        # Calculate statistics
        total_employees = Employee.objects.filter(
            company=company,
            status='active'
        ).count()
        
        present_count = today_attendance.filter(
            Q(status='present') | Q(status='late')
        ).count()
        
        late_count = today_attendance.filter(status='late').count()
        absent_count = total_employees - today_attendance.count()
        on_leave_count = 0  # Will be calculated from leave management
        
        # Get recent check-ins (last 10)
        recent_checkins = today_attendance.filter(
            check_in__isnull=False
        ).order_by('-check_in')[:10]
        
        # Calculate average working hours for today
        completed_today = today_attendance.filter(
            check_out__isnull=False,
            working_hours__isnull=False
        )
        
        avg_hours_today = 0
        if completed_today.exists():
            total_hours = sum(float(r.working_hours) for r in completed_today)
            avg_hours_today = total_hours / completed_today.count()
        
        return Response({
            'date': today.isoformat(),
            'total_employees': total_employees,
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'on_leave': on_leave_count,
            'attendance_rate': round((present_count / total_employees * 100) if total_employees > 0 else 0, 1),
            'average_working_hours': round(avg_hours_today, 2),
            'recent_checkins': AttendanceRecordSerializer(recent_checkins, many=True).data
        })


class CheckInView(APIView):
    """
    API view for employee check-in with biometric verification.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Process employee check-in with face recognition.
        
        Expected request data:
        {
            "employee_id": "EMP001",
            "biometric_data": {
                "face_encoding": [...],
                "quality_score": 0.95,
                "capture_timestamp": "2024-01-01T09:00:00Z"
            },
            "terminal_id": "TERMINAL_01" (optional)
        }
        """
        employee_id = request.data.get('employee_id')
        biometric_data = request.data.get('biometric_data')
        terminal_id = request.data.get('terminal_id', 'unknown')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not biometric_data:
            return Response(
                {'error': 'biometric_data is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get employee
            employee = Employee.objects.get(
                employee_id=employee_id, 
                company=request.user.company
            )
            
            # Check if employee has biometric data enrolled
            if not employee.biometric_data:
                return Response(
                    {'error': 'Employee biometric data not enrolled'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get Face Plugin service
            face_service = get_face_plugin_service()
            
            # Process and verify biometric data
            try:
                processed_biometric = face_service.process_face_capture(biometric_data)
                is_match, similarity = face_service.verify_face(
                    processed_biometric,
                    employee.biometric_data
                )
                
                if not is_match:
                    logger.warning(
                        f"Biometric verification failed for employee {employee_id}. "
                        f"Similarity: {similarity}"
                    )
                    return Response(
                        {
                            'error': 'Biometric verification failed',
                            'similarity_score': similarity
                        }, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
            except ValidationError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except BiometricVerificationError as e:
                return Response(
                    {'error': f'Verification error: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get attendance policy
            policy = get_attendance_policy(request.user.company)
            
            # Check for existing attendance today
            today = timezone.now().date()
            existing_attendance = AttendanceRecord.objects.filter(
                employee=employee,
                date=today,
                company=request.user.company
            ).first()
            
            # Validate check-in
            check_in_time = timezone.now()
            is_valid, attendance_status, message = policy.validate_check_in(
                employee,
                check_in_time,
                existing_attendance
            )
            
            if not is_valid:
                # Handle multiple check-in attempt
                if existing_attendance:
                    result = policy.handle_multiple_check_ins(
                        existing_attendance,
                        check_in_time
                    )
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
                return Response(
                    {'error': message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create or update attendance record
            if existing_attendance:
                attendance = existing_attendance
                attendance.check_in = check_in_time
                attendance.status = attendance_status
                attendance.biometric_verified = True
                attendance.save()
            else:
                attendance = AttendanceRecord.objects.create(
                    employee=employee,
                    date=today,
                    check_in=check_in_time,
                    status=attendance_status,
                    biometric_verified=True,
                    company=request.user.company
                )
            
            # Send real-time WebSocket update
            send_attendance_update(
                str(request.user.company.id),
                {
                    'employee_id': str(employee.id),
                    'employee_name': employee.full_name,
                    'action': 'check_in',
                    'timestamp': check_in_time.isoformat(),
                    'location': terminal_id,
                    'status': attendance_status,
                    'biometric_verified': True,
                    'similarity_score': similarity
                }
            )
            
            # Return response with attendance summary
            serializer = AttendanceRecordSerializer(attendance)
            return Response({
                'attendance': serializer.data,
                'message': message,
                'similarity_score': similarity,
                'policy_summary': policy.get_attendance_summary(attendance)
            }, status=status.HTTP_201_CREATED)
            
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Check-in error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckOutView(APIView):
    """
    API view for employee check-out.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Process employee check-out.
        
        Expected request data:
        {
            "employee_id": "EMP001",
            "terminal_id": "TERMINAL_01" (optional)
        }
        """
        employee_id = request.data.get('employee_id')
        terminal_id = request.data.get('terminal_id', 'unknown')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get employee
            employee = Employee.objects.get(
                employee_id=employee_id, 
                company=request.user.company
            )
            
            # Get today's attendance record
            today = timezone.now().date()
            attendance = AttendanceRecord.objects.filter(
                employee=employee,
                date=today,
                company=request.user.company
            ).first()
            
            if not attendance:
                return Response(
                    {'error': 'No check-in record found for today'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get attendance policy
            policy = get_attendance_policy(request.user.company)
            
            # Validate check-out
            check_out_time = timezone.now()
            is_valid, message = policy.validate_check_out(attendance, check_out_time)
            
            if not is_valid:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update attendance record
            attendance.check_out = check_out_time
            
            # Calculate working hours
            attendance.working_hours = policy.calculate_working_hours(
                attendance.check_in,
                attendance.check_out
            )
            
            attendance.save()
            
            # Calculate overtime
            overtime = policy.calculate_overtime(attendance.working_hours)
            
            # Send real-time WebSocket update
            send_attendance_update(
                str(request.user.company.id),
                {
                    'employee_id': str(employee.id),
                    'employee_name': employee.full_name,
                    'action': 'check_out',
                    'timestamp': check_out_time.isoformat(),
                    'location': terminal_id,
                    'working_hours': float(attendance.working_hours),
                    'overtime_hours': float(overtime)
                }
            )
            
            # Return response with attendance summary
            serializer = AttendanceRecordSerializer(attendance)
            return Response({
                'attendance': serializer.data,
                'message': message,
                'working_hours': float(attendance.working_hours),
                'overtime_hours': float(overtime),
                'policy_summary': policy.get_attendance_summary(attendance)
            })
            
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Check-out error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )