"""
Serializers for employee management.
"""

from rest_framework import serializers
from .models import Employee, Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'parent', 'is_active']
        read_only_fields = ['id']


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'department', 'department_name', 'position',
            'hire_date', 'status', 'date_of_birth', 'address',
            'emergency_contact_name', 'emergency_contact_phone'
        ]
        read_only_fields = ['id', 'full_name']