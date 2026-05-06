"""
Attendance management models.
"""

from django.db import models
from apps.core.models import TenantAwareModel
from apps.employees.models import Employee


class AttendanceRecord(TenantAwareModel):
    """
    Attendance record model for tracking employee check-ins and check-outs.
    """
    ATTENDANCE_STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS_CHOICES, default='present')
    biometric_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date', 'company']
        ordering = ['-date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.status})"