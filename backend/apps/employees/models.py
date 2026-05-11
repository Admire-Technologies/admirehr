"""
Employee management models.
"""

from django.db import models
from apps.core.models import TenantAwareModel


class Branch(TenantAwareModel):
    """
    Branch model for multi-location organizational structure.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_branches')
    is_active = models.BooleanField(default=True)
    
    # Location details
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ['code', 'company']
        ordering = ['name']
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    @property
    def employee_count(self):
        """Get the number of employees in this branch."""
        return self.employee_set.filter(status='active').count()

    @property
    def full_address(self):
        """Get the complete formatted address."""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(filter(None, parts))


class Department(TenantAwareModel):
    """
    Department model for organizational structure.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['name', 'company']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Employee(TenantAwareModel):
    """
    Employee model with comprehensive information.
    """
    EMPLOYEE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ]

    employee_id = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS_CHOICES, default='active')
    biometric_data = models.JSONField(null=True, blank=True)
    
    # Personal information
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ['employee_id', 'company']
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"