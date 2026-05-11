"""
Serializers for leave management.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime
from .models import LeaveRequest, LeaveType, LeaveBalance


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = [
            'id', 'name', 'description', 'days_allowed', 'is_active',
            'allow_negative_balance', 'requires_approval'
        ]
        read_only_fields = ['id']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    available_days = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'year', 'accrued_days', 'used_days', 'pending_days', 'available_days'
        ]
        read_only_fields = ['id', 'available_days']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approver_name = serializers.CharField(source='approver.full_name', read_only=True, allow_null=True)
    available_balance = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'days_requested', 'reason', 'status',
            'approver', 'approver_name', 'approved_at', 'rejection_reason',
            'cancelled_at', 'cancellation_reason', 'available_balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'approved_at', 'cancelled_at', 'status',
            'approver', 'rejection_reason', 'cancellation_reason', 'employee'
        ]

    def get_available_balance(self, obj):
        """Get available leave balance for the employee and leave type."""
        year = obj.start_date.year if obj.start_date else datetime.now().year
        try:
            balance = LeaveBalance.objects.get(
                employee=obj.employee,
                leave_type=obj.leave_type,
                year=year,
                company=obj.company
            )
            return float(balance.available_days)
        except LeaveBalance.DoesNotExist:
            return float(obj.leave_type.days_allowed)

    def validate(self, data):
        """Validate leave request data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        days_requested = data.get('days_requested')
        leave_type = data.get('leave_type')
        
        # Get employee from context (set in view)
        employee = self.context.get('employee')
        if not employee:
            raise serializers.ValidationError('Employee information is required.')

        # Validate dates
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after or equal to start date.'
                })
            
            # Check if start date is in the past
            if start_date < timezone.now().date():
                raise serializers.ValidationError({
                    'start_date': 'Cannot apply for leave in the past.'
                })
            
            # Check for overlapping leave requests
            overlapping = LeaveRequest.objects.filter(
                employee=employee,
                company=employee.company,
                status__in=['pending', 'approved']
            ).filter(
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Exclude current instance if updating
            if self.instance:
                overlapping = overlapping.exclude(id=self.instance.id)
            
            if overlapping.exists():
                raise serializers.ValidationError({
                    'start_date': 'Leave request overlaps with existing leave.'
                })

        # Validate leave balance
        if employee and leave_type and days_requested:
            year = start_date.year if start_date else datetime.now().year
            balance, created = LeaveBalance.objects.get_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                company=employee.company,
                defaults={'accrued_days': leave_type.days_allowed}
            )

            if not balance.can_apply_leave(days_requested):
                raise serializers.ValidationError({
                    'days_requested': f'Insufficient leave balance. Available: {balance.available_days} days.'
                })

        return data

    def create(self, validated_data):
        """Create leave request and update pending balance."""
        # Get employee from context
        employee = self.context.get('employee')
        validated_data['employee'] = employee
        
        leave_request = super().create(validated_data)
        
        # Update pending days in balance
        year = leave_request.start_date.year
        balance, created = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type,
            year=year,
            company=leave_request.company,
            defaults={'accrued_days': leave_request.leave_type.days_allowed}
        )
        balance.pending_days += leave_request.days_requested
        balance.save()
        
        return leave_request


class LeaveApprovalSerializer(serializers.Serializer):
    """Serializer for approving leave requests."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a leave request.'
            })
        return data


class LeaveCancellationSerializer(serializers.Serializer):
    """Serializer for cancelling leave requests."""
    cancellation_reason = serializers.CharField(required=True)


class LeaveCalendarSerializer(serializers.Serializer):
    """Serializer for leave calendar view."""
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    leave_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.CharField()