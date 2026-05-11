"""
Serializers for employee management.
"""

from rest_framework import serializers
from .models import Employee, Department, Branch


class BranchSerializer(serializers.ModelSerializer):
    employee_count = serializers.IntegerField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'code', 'address', 'phone', 'email', 
            'parent', 'parent_name', 'is_active', 'city', 'state', 
            'country', 'postal_code', 'employee_count', 'full_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'parent', 'parent_name', 'is_active', 'employee_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.employee_set.filter(status='active').count()


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'department', 'department_name', 'branch', 
            'branch_name', 'position', 'hire_date', 'status', 'date_of_birth', 
            'address', 'emergency_contact_name', 'emergency_contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'full_name', 'created_at', 'updated_at']

    def validate_employee_id(self, value):
        """Validate employee_id is unique within company."""
        company = self.context['request'].user.company
        queryset = Employee.objects.filter(employee_id=value, company=company)
        
        # Exclude current instance when updating
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError("Employee ID already exists in your company.")
        
        return value

    def validate_email(self, value):
        """Validate email is unique within company."""
        company = self.context['request'].user.company
        queryset = Employee.objects.filter(email=value, company=company)
        
        # Exclude current instance when updating
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError("Email already exists in your company.")
        
        return value