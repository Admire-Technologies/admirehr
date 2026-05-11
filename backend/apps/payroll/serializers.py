"""
Serializers for payroll management.
"""

from rest_framework import serializers
from .models import PayrollRecord, SalaryRule, EmployeeSalaryStructure
from apps.employees.models import Employee


class SalaryRuleSerializer(serializers.ModelSerializer):
    """Serializer for salary rules."""
    
    class Meta:
        model = SalaryRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'calculation_method',
            'amount', 'is_active', 'applies_to_all', 'specific_employees',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate salary rule data."""
        if data.get('calculation_method') == 'percentage' and data.get('amount', 0) > 100:
            raise serializers.ValidationError({
                'amount': 'Percentage cannot exceed 100%'
            })
        return data


class EmployeeSalaryStructureSerializer(serializers.ModelSerializer):
    """Serializer for employee salary structure."""
    
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    rule_name = serializers.CharField(source='salary_rule.name', read_only=True)
    rule_type = serializers.CharField(source='salary_rule.rule_type', read_only=True)
    
    class Meta:
        model = EmployeeSalaryStructure
        fields = [
            'id', 'employee', 'employee_name', 'salary_rule', 'rule_name',
            'rule_type', 'custom_amount', 'effective_from', 'effective_to',
            'is_active', 'applicable_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applicable_amount', 'created_at', 'updated_at']


class PayrollRecordSerializer(serializers.ModelSerializer):
    """Serializer for payroll records."""
    
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    period_display = serializers.CharField(read_only=True)
    attendance_percentage = serializers.FloatField(read_only=True)
    processed_by_name = serializers.CharField(
        source='processed_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = PayrollRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'department_name',
            'period_start', 'period_end', 'period_display',
            'basic_salary', 'allowances', 'deductions', 'gross_salary', 'net_salary',
            'working_days', 'present_days', 'leave_days', 'absent_days',
            'attendance_percentage', 'is_processed', 'processed_at', 'processed_by',
            'processed_by_name', 'notes', 'breakdown',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'period_display', 'attendance_percentage', 'processed_at',
            'processed_by', 'created_at', 'updated_at'
        ]


class PayrollRecordDetailSerializer(PayrollRecordSerializer):
    """Detailed serializer for payroll records with additional information."""
    
    employee_details = serializers.SerializerMethodField()
    
    class Meta(PayrollRecordSerializer.Meta):
        fields = PayrollRecordSerializer.Meta.fields + ['employee_details']
    
    def get_employee_details(self, obj):
        """Get detailed employee information."""
        return {
            'id': str(obj.employee.id),
            'employee_id': obj.employee.employee_id,
            'full_name': obj.employee.full_name,
            'email': obj.employee.email,
            'department': obj.employee.department.name,
            'position': obj.employee.position,
        }


class PayrollGenerationSerializer(serializers.Serializer):
    """Serializer for payroll generation request."""
    
    period_start = serializers.DateField(required=True)
    period_end = serializers.DateField(required=True)
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="Optional list of employee IDs. If not provided, generates for all active employees."
    )
    
    def validate(self, data):
        """Validate payroll generation data."""
        if data['period_start'] > data['period_end']:
            raise serializers.ValidationError({
                'period_end': 'Period end must be after or equal to period start'
            })
        return data


class BulkPayrollProcessSerializer(serializers.Serializer):
    """Serializer for bulk payroll processing."""
    
    period_start = serializers.DateField(required=True)
    period_end = serializers.DateField(required=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )


class PayrollSummarySerializer(serializers.Serializer):
    """Serializer for payroll summary statistics."""
    
    employee_count = serializers.IntegerField()
    total_basic_salary = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_allowances = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_deductions = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gross_salary = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_net_salary = serializers.DecimalField(max_digits=15, decimal_places=2)