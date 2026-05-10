"""
Core models for the HRMS application.
"""

import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(BaseModel):
    """
    Company model for multi-tenant support.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Configuration settings
    settings = models.JSONField(default=dict, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    currency = models.CharField(max_length=3, default='USD')
    
    # Business settings
    working_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    working_days_per_week = models.IntegerField(default=5)
    
    # Leave policy settings
    annual_leave_days = models.IntegerField(default=21)
    sick_leave_days = models.IntegerField(default=10)
    
    # Attendance settings
    grace_period_minutes = models.IntegerField(default=15)
    overtime_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    
    # System settings
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50, default='basic')
    max_employees = models.IntegerField(default=100)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_setting(self, key, default=None):
        """
        Get a specific setting value from the settings JSON field.
        """
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """
        Set a specific setting value in the settings JSON field.
        """
        if not self.settings:
            self.settings = {}
        self.settings[key] = value

    @property
    def employee_count(self):
        """
        Get the current number of employees in the company.
        """
        return self.employee_set.filter(status='active').count()

    def can_add_employee(self):
        """
        Check if the company can add more employees based on subscription limits.
        """
        return self.employee_count < self.max_employees


class TenantAwareModel(BaseModel):
    """
    Abstract model that includes company for multi-tenant support.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Use the tenant-aware manager
    objects = models.Manager()  # Default manager for admin and migrations
    tenant_objects = None  # Will be set after TenantAwareManager is defined
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Automatically set the company if not already set.
        """
        if not self.company_id:
            from .middleware import get_current_company
            current_company = get_current_company()
            if current_company:
                self.company = current_company
        super().save(*args, **kwargs)


# Set the tenant-aware manager after it's imported
from .middleware import TenantAwareManager
TenantAwareModel.add_to_class('tenant_objects', TenantAwareManager())