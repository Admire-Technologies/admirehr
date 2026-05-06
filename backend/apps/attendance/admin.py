from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'working_hours', 'status']
    list_filter = ['status', 'date', 'biometric_verified', 'company']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'