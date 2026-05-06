from django.contrib import admin
from .models import SalaryRule, PayrollRecord


@admin.register(SalaryRule)
class SalaryRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'calculation_method', 'amount', 'company', 'is_active']
    list_filter = ['rule_type', 'company', 'is_active']
    search_fields = ['name']


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'period_start', 'period_end', 'net_salary', 'is_processed']
    list_filter = ['is_processed', 'company', 'period_start']
    search_fields = ['employee__first_name', 'employee__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'period_start'