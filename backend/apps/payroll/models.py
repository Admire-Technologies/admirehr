"""
Payroll management models.
"""

from django.db import models
from apps.core.models import TenantAwareModel
from apps.employees.models import Employee


class SalaryRule(TenantAwareModel):
    """
    Salary rule model for flexible payroll calculations.
    """
    RULE_TYPE_CHOICES = [
        ('allowance', 'Allowance'),
        ('deduction', 'Deduction'),
        ('basic', 'Basic Salary'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    calculation_method = models.CharField(max_length=50)  # 'fixed', 'percentage', 'formula'
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['name', 'company']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class PayrollRecord(TenantAwareModel):
    """
    Payroll record model for employee salary processing.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['employee', 'period_start', 'period_end', 'company']
        ordering = ['-period_start', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.full_name} - {self.period_start} to {self.period_end}"