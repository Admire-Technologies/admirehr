from django.contrib import admin
from .models import Employee, Department, Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'parent', 'city', 'is_active']
    list_filter = ['company', 'is_active', 'city', 'country']
    search_fields = ['name', 'code', 'city']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'parent', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'email', 'department', 'branch', 'status', 'hire_date']
    list_filter = ['status', 'department', 'branch', 'company', 'hire_date']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']