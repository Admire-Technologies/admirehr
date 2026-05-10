"""
Authentication models for the HRMS application.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
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