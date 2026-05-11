import uuid
from django.db import models
from apps.core.models import Company
from apps.authentication.models import User


class DashboardWidget(models.Model):
    """Model for storing user-specific dashboard widget configurations."""
    
    WIDGET_TYPES = [
        ('attendance_summary', 'Attendance Summary'),
        ('leave_requests', 'Leave Requests'),
        ('payroll_summary', 'Payroll Summary'),
        ('employee_count', 'Employee Count'),
        ('attendance_trends', 'Attendance Trends'),
        ('leave_patterns', 'Leave Patterns'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPES)
    position = models.IntegerField(default=0)
    size = models.CharField(max_length=20, default='medium')  # small, medium, large
    settings = models.JSONField(default=dict, blank=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ['user', 'widget_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.widget_type}"


class ScheduledReport(models.Model):
    """Model for storing scheduled report configurations."""
    
    REPORT_TYPES = [
        ('attendance', 'Attendance Report'),
        ('leave', 'Leave Report'),
        ('payroll', 'Payroll Report'),
        ('employee', 'Employee Report'),
        ('comprehensive', 'Comprehensive Report'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]

    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_reports')
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    recipients = models.JSONField(default=list)  # List of email addresses
    filters = models.JSONField(default=dict, blank=True)  # Report filters
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"
