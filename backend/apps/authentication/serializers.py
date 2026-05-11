"""
Serializers for authentication app.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, Permission
from apps.core.models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'code']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'description', 'module', 'action']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions', 'permission_ids',
            'is_system_role', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_system_role']
    
    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role
    
    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)
        
        return instance


class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    role_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'company', 'role', 'role_id', 'is_company_admin', 'last_login',
            'date_joined', 'permissions'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined']
    
    def get_permissions(self, obj):
        """Get user permissions grouped by module."""
        permissions_by_module = obj.get_permissions_by_module()
        # Convert Permission objects to serialized data
        result = {}
        for module, perms in permissions_by_module.items():
            result[module] = [PermissionSerializer(perm).data for perm in perms]
        return result
    
    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if role_id is not None:
            if role_id:
                try:
                    role = Role.objects.get(id=role_id, company=instance.company)
                    instance.role = role
                except Role.DoesNotExist:
                    raise serializers.ValidationError("Invalid role ID")
            else:
                instance.role = None
        
        instance.save()
        return instance


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'role_id', 'is_company_admin'
        ]
    
    def validate_password(self, value):
        validate_password(value)
        return value
    
    def create(self, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            company=self.context['request'].user.company,
            **validated_data
        )
        
        if role_id:
            try:
                role = Role.objects.get(id=role_id, company=user.company)
                user.role = role
                user.save()
            except Role.DoesNotExist:
                raise serializers.ValidationError("Invalid role ID")
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserPermissionsSerializer(serializers.Serializer):
    """Serializer for user permissions response."""
    permissions = serializers.DictField()
    role = RoleSerializer(read_only=True)
    is_company_admin = serializers.BooleanField()
    
    def to_representation(self, instance):
        """Custom representation to handle Permission objects."""
        data = super().to_representation(instance)
        
        # Convert Permission objects to dictionaries
        if 'permissions' in data and isinstance(data['permissions'], dict):
            serialized_permissions = {}
            for module, perms in data['permissions'].items():
                if hasattr(perms, '__iter__') and not isinstance(perms, str):
                    # Convert Permission objects to dictionaries
                    serialized_permissions[module] = [
                        PermissionSerializer(perm).data if hasattr(perm, 'id') else perm
                        for perm in perms
                    ]
                else:
                    serialized_permissions[module] = perms
            data['permissions'] = serialized_permissions
        
        return data



class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for audit log entries.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        from .models import AuditLog
        model = AuditLog
        fields = [
            'id', 'user', 'user_username', 'user_email', 'action', 
            'module', 'description', 'changes', 'ip_address', 
            'user_agent', 'timestamp'
        ]
        read_only_fields = fields
