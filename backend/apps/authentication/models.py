"""
Authentication models for the HRMS application.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.core.models import Company


class Permission(models.Model):
    """
    Custom permission model for RBAC system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50)  # e.g., 'employees', 'attendance', 'payroll'
    action = models.CharField(max_length=50)  # e.g., 'view', 'add', 'change', 'delete'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['codename', 'module']
        ordering = ['module', 'action']

    def __str__(self):
        return f"{self.name} ({self.codename})"


class Role(models.Model):
    """
    Role model for RBAC system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    is_system_role = models.BooleanField(default=False)  # For predefined roles
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'company']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    def has_permission(self, permission_codename):
        """
        Check if role has a specific permission.
        """
        return self.permissions.filter(codename=permission_codename).exists()

    def get_permissions_by_module(self):
        """
        Get permissions grouped by module.
        """
        permissions_dict = {}
        for permission in self.permissions.all():
            if permission.module not in permissions_dict:
                permissions_dict[permission.module] = []
            permissions_dict[permission.module].append(permission)
        return permissions_dict


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True)
    employee = models.OneToOneField(
        'employees.Employee', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user_account'
    )
    is_company_admin = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.company.name})"

    def has_permission(self, permission_codename):
        """
        Check if user has a specific permission.
        """
        if self.is_superuser or self.is_company_admin:
            return True
        
        if self.role:
            return self.role.has_permission(permission_codename)
        
        return False

    def get_all_permissions(self):
        """
        Get all permissions for the user.
        """
        if self.is_superuser:
            return Permission.objects.all()
        
        if self.is_company_admin:
            return Permission.objects.all()
        
        if self.role:
            return self.role.permissions.all()
        
        return Permission.objects.none()

    def get_permissions_by_module(self):
        """
        Get user permissions grouped by module.
        """
        permissions = self.get_all_permissions()
        permissions_dict = {}
        for permission in permissions:
            if permission.module not in permissions_dict:
                permissions_dict[permission.module] = []
            permissions_dict[permission.module].append(permission)
        return permissions_dict



class AuditLog(models.Model):
    """
    Audit log model for tracking user activities and data modifications.
    Implements Requirement 10.3: System activity logging and audit trails.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('role_assign', 'Role Assignment'),
        ('permission_change', 'Permission Change'),
        ('access', 'Access'),
        ('export', 'Export'),
        ('import', 'Import'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_logs'
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # Generic foreign key to track any model
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    object_id = models.CharField(max_length=255, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Details about the action
    module = models.CharField(max_length=50)  # e.g., 'users', 'employees', 'attendance'
    description = models.TextField()
    changes = models.JSONField(default=dict, blank=True)  # Store before/after values
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.action} - {self.module} - {self.timestamp}"
    
    @classmethod
    def log_action(cls, user, action, module, description, company=None, 
                   content_object=None, changes=None, request=None):
        """
        Helper method to create audit log entries.
        
        Args:
            user: User performing the action
            action: Action type (from ACTION_CHOICES)
            module: Module name (e.g., 'users', 'employees')
            description: Human-readable description
            company: Company instance (defaults to user's company)
            content_object: The object being acted upon
            changes: Dictionary of changes (before/after values)
            request: HTTP request object for metadata
        """
        if not company and user:
            company = user.company
        
        log_data = {
            'user': user,
            'company': company,
            'action': action,
            'module': module,
            'description': description,
            'changes': changes or {},
        }
        
        if content_object:
            log_data['content_object'] = content_object
        
        if request:
            # Extract IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                log_data['ip_address'] = x_forwarded_for.split(',')[0]
            else:
                log_data['ip_address'] = request.META.get('REMOTE_ADDR')
            
            # Extract user agent
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(**log_data)
