"""
Serializers for core models.
"""

from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer for Company model.
    """
    employee_count = serializers.ReadOnlyField()
    can_add_employee = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'code', 'email', 'phone', 'address', 'website', 'logo',
            'timezone', 'date_format', 'currency', 'working_hours_per_day',
            'working_days_per_week', 'annual_leave_days', 'sick_leave_days',
            'grace_period_minutes', 'overtime_threshold_hours', 'subscription_plan',
            'max_employees', 'is_active', 'employee_count', 'can_add_employee',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'employee_count', 'can_add_employee']

    def validate_code(self, value):
        """
        Validate that company code is unique and follows proper format.
        """
        if not value.isalnum():
            raise serializers.ValidationError("Company code must contain only alphanumeric characters.")
        
        if len(value) < 2 or len(value) > 10:
            raise serializers.ValidationError("Company code must be between 2 and 10 characters.")
        
        return value.upper()


class CompanyRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for company registration.
    """
    admin_username = serializers.CharField(write_only=True)
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=8)
    admin_first_name = serializers.CharField(write_only=True)
    admin_last_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Company
        fields = [
            'name', 'code', 'email', 'phone', 'address', 'website',
            'timezone', 'currency', 'working_hours_per_day', 'working_days_per_week',
            'annual_leave_days', 'sick_leave_days', 'grace_period_minutes',
            'overtime_threshold_hours', 'admin_username', 'admin_email',
            'admin_password', 'admin_first_name', 'admin_last_name'
        ]

    def validate_code(self, value):
        """
        Validate that company code is unique and follows proper format.
        """
        if not value.isalnum():
            raise serializers.ValidationError("Company code must contain only alphanumeric characters.")
        
        if len(value) < 2 or len(value) > 10:
            raise serializers.ValidationError("Company code must be between 2 and 10 characters.")
        
        return value.upper()

    def create(self, validated_data):
        """
        Create company and admin user.
        """
        from django.contrib.auth import get_user_model
        from apps.authentication.models import Role
        from django.contrib.auth.models import Permission
        
        User = get_user_model()
        
        # Extract admin user data
        admin_data = {
            'username': validated_data.pop('admin_username'),
            'email': validated_data.pop('admin_email'),
            'password': validated_data.pop('admin_password'),
            'first_name': validated_data.pop('admin_first_name'),
            'last_name': validated_data.pop('admin_last_name'),
        }
        
        # Create company
        company = Company.objects.create(**validated_data)
        
        # Create admin role with all permissions
        admin_role = Role.objects.create(
            name='Company Admin',
            description='Full access to all company features',
            company=company
        )
        
        # Add all permissions to admin role
        all_permissions = Permission.objects.all()
        admin_role.permissions.set(all_permissions)
        
        # Create admin user
        admin_user = User.objects.create_user(
            username=admin_data['username'],
            email=admin_data['email'],
            password=admin_data['password'],
            first_name=admin_data['first_name'],
            last_name=admin_data['last_name'],
            company=company,
            role=admin_role,
            is_company_admin=True
        )
        
        return company


class CompanySettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for company settings management.
    """
    
    class Meta:
        model = Company
        fields = [
            'settings', 'timezone', 'date_format', 'currency',
            'working_hours_per_day', 'working_days_per_week',
            'annual_leave_days', 'sick_leave_days',
            'grace_period_minutes', 'overtime_threshold_hours'
        ]

    def update(self, instance, validated_data):
        """
        Update company settings.
        """
        # Handle settings JSON field updates
        if 'settings' in validated_data:
            current_settings = instance.settings or {}
            new_settings = validated_data.pop('settings')
            current_settings.update(new_settings)
            instance.settings = current_settings
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance