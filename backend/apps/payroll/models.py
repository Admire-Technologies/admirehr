"""
Payroll management models.
"""

from django.db import models
from django.core.exceptions import ValidationError
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
    
    CALCULATION_METHOD_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Basic Salary'),
        ('formula', 'Custom Formula'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    calculation_method = models.CharField(max_length=50, choices=CALCULATION_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    # Optional: Apply rule to specific employees or departments
    applies_to_all = models.BooleanField(default=True)
    specific_employees = models.ManyToManyField(
        Employee, 
        blank=True, 
        related_name='salary_rules'
    )

    class Meta:
        unique_together = ['name', 'company']
        ordering = ['rule_type', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['rule_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.rule_type})"
    
    def clean(self):
        """Validate salary rule."""
        if self.calculation_method == 'percentage' and self.amount > 100:
            raise ValidationError("Percentage cannot exceed 100%")
        
        if self.rule_type == 'basic':
            # Check if another basic salary rule exists for this company
            existing_basic = SalaryRule.objects.filter(
                company=self.company,
                rule_type='basic',
                is_active=True
            ).exclude(id=self.id)
            
            if existing_basic.exists():
                raise ValidationError(
                    "Only one active basic salary rule is allowed per company"
                )


class PayrollRecord(TenantAwareModel):
    """
    Payroll record model for employee salary processing.
    """
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='payroll_records'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Salary components
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Attendance and leave tracking
    working_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    leave_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    absent_days = models.IntegerField(default=0)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payrolls'
    )
    
    # Additional details
    notes = models.TextField(blank=True)
    breakdown = models.JSONField(default=dict, blank=True)  # Detailed breakdown of calculations

    class Meta:
        unique_together = ['employee', 'period_start', 'period_end', 'company']
        ordering = ['-period_start', 'employee__first_name']
        indexes = [
            models.Index(fields=['company', 'period_start', 'period_end']),
            models.Index(fields=['employee', 'period_start']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.period_start} to {self.period_end}"
    
    def clean(self):
        """Validate payroll record."""
        if self.period_start and self.period_end:
            if self.period_start > self.period_end:
                raise ValidationError("Period start must be before or equal to period end")
    
    @property
    def period_display(self):
        """Get formatted period display."""
        return f"{self.period_start.strftime('%b %Y')}"
    
    @property
    def attendance_percentage(self):
        """Calculate attendance percentage."""
        if self.working_days == 0:
            return 0
        return (self.present_days / self.working_days) * 100


class EmployeeSalaryStructure(TenantAwareModel):
    """
    Employee-specific salary structure linking employees to salary rules.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_structure'
    )
    salary_rule = models.ForeignKey(
        SalaryRule,
        on_delete=models.CASCADE
    )
    custom_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override the default rule amount for this employee"
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-effective_from']
        indexes = [
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['effective_from', 'effective_to']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.salary_rule.name}"
    
    @property
    def applicable_amount(self):
        """Get the applicable amount (custom or default)."""
        return self.custom_amount if self.custom_amount else self.salary_rule.amount