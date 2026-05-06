"""
Attendance management views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records.
    """
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AttendanceRecord.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class CheckInView(APIView):
    """
    API view for employee check-in with biometric verification.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # This is a placeholder for biometric check-in logic
        # In a real implementation, this would integrate with Face Plugin SDK
        
        employee_id = request.data.get('employee_id')
        biometric_data = request.data.get('biometric_data')
        
        # TODO: Implement biometric verification logic
        # For now, we'll create a basic attendance record
        
        try:
            from apps.employees.models import Employee
            employee = Employee.objects.get(
                employee_id=employee_id, 
                company=request.user.company
            )
            
            today = timezone.now().date()
            attendance, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                company=request.user.company,
                defaults={
                    'check_in': timezone.now(),
                    'biometric_verified': True,
                    'status': 'present'
                }
            )
            
            if not created and attendance.check_in:
                return Response(
                    {'error': 'Already checked in today'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = AttendanceRecordSerializer(attendance)
            return Response(serializer.data)
            
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CheckOutView(APIView):
    """
    API view for employee check-out.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        employee_id = request.data.get('employee_id')
        
        try:
            from apps.employees.models import Employee
            employee = Employee.objects.get(
                employee_id=employee_id, 
                company=request.user.company
            )
            
            today = timezone.now().date()
            attendance = AttendanceRecord.objects.get(
                employee=employee,
                date=today,
                company=request.user.company
            )
            
            if attendance.check_out:
                return Response(
                    {'error': 'Already checked out today'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            attendance.check_out = timezone.now()
            
            # Calculate working hours
            if attendance.check_in:
                time_diff = attendance.check_out - attendance.check_in
                attendance.working_hours = round(time_diff.total_seconds() / 3600, 2)
            
            attendance.save()
            
            serializer = AttendanceRecordSerializer(attendance)
            return Response(serializer.data)
            
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except AttendanceRecord.DoesNotExist:
            return Response(
                {'error': 'No check-in record found for today'}, 
                status=status.HTTP_404_NOT_FOUND
            )