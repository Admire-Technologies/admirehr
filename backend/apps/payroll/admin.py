"""
Admin configuration for payroll app.
"""

from django.contrib import admin
from .models import SalaryRule, PayrollRecord, EmployeeSalaryStructure


@admin.register(SalaryRule)
class SalaryRuleAdmin(admin.ModelAdmin):
    """Admin interface for SalaryRule model."""
    
    list_display = [
        'name', 'rule_type', 'calculation_method', 'amount',
        'is_active', 'company', 'created_at'
    ]
    list_filter = ['rule_type', 'calculation_method', 'is_active', 'company']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'company')
        }),
        ('Rule Configuration', {
            'fields': ('rule_type', 'calculation_method', 'amount', 'is_active')
        }),
        ('Application Scope', {
            'fields': ('applies_to_all', 'specific_employees')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    """Admin interface for PayrollRecord model."""
    
    list_display = [
        'employee', 'period_start', 'period_end', 'net_salary',
        'is_processed', 'processed_at', 'company'
    ]
    list_filter = ['is_processed', 'period_start', 'company']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    readonly_fields = ['id', 'attendance_percentage', 'period_display', 'created_at', 'updated_at']
    date_hierarchy = 'period_start'
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'company', 'period_start', 'period_end', 'period_display')
        }),
        ('Salary Components', {
            'fields': ('basic_salary', 'allowances', 'deductions', 'gross_salary', 'net_salary')
        }),
        ('Attendance Information', {
            'fields': ('working_days', 'present_days', 'leave_days', 'absent_days', 'attendance_percentage')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processed_at', 'processed_by')
        }),
        ('Additional Details', {
            'fields': ('notes', 'breakdown'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmployeeSalaryStructure)
class EmployeeSalaryStructureAdmin(admin.ModelAdmin):
    """Admin interface for EmployeeSalaryStructure model."""
    
    list_display = [
        'employee', 'salary_rule', 'applicable_amount',
        'effective_from', 'effective_to', 'is_active', 'company'
    ]
    list_filter = ['is_active', 'effective_from', 'company']
    search_fields = ['employee__first_name', 'employee__last_name', 'salary_rule__name']
    readonly_fields = ['id', 'applicable_amount', 'created_at', 'updated_at']
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'salary_rule', 'company')
        }),
        ('Amount Configuration', {
            'fields': ('custom_amount', 'applicable_amount')
        }),
        ('Effective Period', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )