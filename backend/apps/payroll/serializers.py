"""
Serializers for payroll management.
"""

from rest_framework import serializers
from .models import PayrollRecord, SalaryRule


class SalaryRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'calculation_method',
            'amount', 'is_active'
        ]
        read_only_fields = ['id']


class PayrollRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)

    class Meta:
        model = PayrollRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'period_start', 'period_end', 'basic_salary', 'allowances',
            'deductions', 'gross_salary', 'net_salary', 'is_processed',
            'processed_at'
        ]
        read_only_fields = ['id', 'processed_at']