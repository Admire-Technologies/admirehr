"""
Serializers for attendance management.
"""

from rest_framework import serializers
from .models import AttendanceRecord
from apps.employees.models import Employee
from decimal import Decimal


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    overtime_hours = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'department_name',
            'date', 'check_in', 'check_out', 'working_hours', 'status',
            'biometric_verified', 'notes', 'overtime_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'working_hours', 'created_at', 'updated_at']

    def get_overtime_hours(self, obj):
        """Calculate overtime hours based on company policy."""
        if not obj.working_hours:
            return 0.0
        
        # Get company's overtime threshold
        overtime_threshold = obj.company.overtime_threshold_hours
        if obj.working_hours > overtime_threshold:
            return float(obj.working_hours - overtime_threshold)
        return 0.0


class AttendanceManualEntrySerializer(serializers.ModelSerializer):
    """Serializer for manual attendance entry and corrections."""
    employee_id_input = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_id_input', 'date', 'check_in', 
            'check_out', 'status', 'notes', 'biometric_verified'
        ]
        read_only_fields = ['id', 'biometric_verified']
        extra_kwargs = {
            'employee': {'required': False}  # Make employee optional since we use employee_id_input
        }
    
    def validate(self, data):
        """Validate manual entry data."""
        # Handle employee_id_input if provided
        if 'employee_id_input' in data:
            employee_id = data.pop('employee_id_input')
            try:
                company = self.context['request'].user.company
                employee = Employee.objects.get(employee_id=employee_id, company=company)
                data['employee'] = employee
            except Employee.DoesNotExist:
                raise serializers.ValidationError({
                    'employee_id_input': 'Employee not found'
                })
        
        # Ensure employee is set (either from employee_id_input or direct employee field)
        if 'employee' not in data and not self.instance:
            raise serializers.ValidationError({
                'employee': 'Employee is required'
            })
        
        # Validate check_out is after check_in
        check_in = data.get('check_in', self.instance.check_in if self.instance else None)
        check_out = data.get('check_out', self.instance.check_out if self.instance else None)
        
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError({
                    'check_out': 'Check-out time must be after check-in time'
                })
        
        return data
    
    def create(self, validated_data):
        """Create manual attendance entry."""
        # Set biometric_verified to False for manual entries
        validated_data['biometric_verified'] = False
        validated_data['company'] = self.context['request'].user.company
        
        # Calculate working hours if both check_in and check_out are provided
        if validated_data.get('check_in') and validated_data.get('check_out'):
            from .policy import get_attendance_policy
            policy = get_attendance_policy(validated_data['company'])
            validated_data['working_hours'] = policy.calculate_working_hours(
                validated_data['check_in'],
                validated_data['check_out']
            )
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update attendance record (correction)."""
        # Recalculate working hours if times are updated
        check_in = validated_data.get('check_in', instance.check_in)
        check_out = validated_data.get('check_out', instance.check_out)
        
        if check_in and check_out:
            from .policy import get_attendance_policy
            policy = get_attendance_policy(instance.company)
            validated_data['working_hours'] = policy.calculate_working_hours(
                check_in,
                check_out
            )
        
        return super().update(instance, validated_data)


class AttendanceReportSerializer(serializers.Serializer):
    """Serializer for attendance report parameters."""
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    employee_id = serializers.CharField(required=False, allow_blank=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['present', 'absent', 'late', 'half_day'],
        required=False,
        allow_blank=True
    )
    export_format = serializers.ChoiceField(
        choices=['json', 'pdf', 'excel'],
        default='json'
    )
    
    def validate(self, data):
        """Validate report parameters."""
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # Limit date range to 1 year
        date_diff = (data['end_date'] - data['start_date']).days
        if date_diff > 365:
            raise serializers.ValidationError({
                'date_range': 'Date range cannot exceed 1 year'
            })
        
        return data


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer for attendance summary statistics."""
    total_records = serializers.IntegerField()
    present = serializers.IntegerField()
    late = serializers.IntegerField()
    absent = serializers.IntegerField()
    half_day = serializers.IntegerField()
    average_working_hours = serializers.FloatField()
    total_working_hours = serializers.FloatField()
    total_overtime_hours = serializers.FloatField()
    unique_employees = serializers.IntegerField()
    date_range = serializers.DictField()