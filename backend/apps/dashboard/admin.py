"""
Admin configuration for dashboard app.
"""
from django.contrib import admin
from .models import DashboardWidget, ScheduledReport


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'widget_type', 'position', 'is_visible', 'created_at']
    list_filter = ['widget_type', 'is_visible', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['user', 'position']


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'format', 'is_active', 'last_run', 'next_run']
    list_filter = ['report_type', 'frequency', 'format', 'is_active']
    search_fields = ['name', 'created_by__username']
    ordering = ['-created_at']
