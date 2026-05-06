"""
Serializers for attendance management.
"""

from rest_framework import serializers
from .models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'date',
            'check_in', 'check_out', 'working_hours', 'status',
            'biometric_verified', 'notes'
        ]
        read_only_fields = ['id', 'working_hours']