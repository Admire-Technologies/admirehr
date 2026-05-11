"""
Leave management models.
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from apps.core.models import TenantAwareModel
from apps.employees.models import Employee


class LeaveType(TenantAwareModel):
    """
    Leave type model for different types of leave.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    days_allowed = models.IntegerField()
    is_active = models.BooleanField(default=True)
    allow_negative_balance = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)

    class Meta:
        unique_together = ['name', 'company']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class LeaveBalance(TenantAwareModel):
    """
    Leave balance tracking for employees.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField()
    accrued_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pending_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year', 'company']
        ordering = ['-year', 'leave_type__name']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.year})"

    @property
    def available_days(self):
        """Calculate available leave days."""
        return self.accrued_days - self.used_days - self.pending_days

    def can_apply_leave(self, days):
        """Check if employee can apply for leave."""
        if self.leave_type.allow_negative_balance:
            return True
        return self.available_days >= days


class LeaveRequest(TenantAwareModel):
    """
    Leave request model for employee leave applications.
    """
    LEAVE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=LEAVE_STATUS_CHOICES, default='pending')
    approver = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.status})"

    def clean(self):
        """Validate leave request."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("Start date must be before or equal to end date.")
            
            # Check for overlapping leave requests
            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                company=self.company,
                status__in=['pending', 'approved']
            ).exclude(id=self.id).filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            
            if overlapping.exists():
                raise ValidationError("Leave request overlaps with existing leave.")

    def approve(self, approver):
        """Approve the leave request."""
        if self.status != 'pending':
            raise ValidationError("Only pending requests can be approved.")
        
        self.status = 'approved'
        self.approver = approver
        self.approved_at = timezone.now()
        self.save()
        
        # Update leave balance
        self._update_leave_balance()

    def reject(self, approver, reason):
        """Reject the leave request."""
        if self.status != 'pending':
            raise ValidationError("Only pending requests can be rejected.")
        
        self.status = 'rejected'
        self.approver = approver
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Release pending days
        self._release_pending_days()

    def cancel(self, reason):
        """Cancel the leave request."""
        if self.status not in ['pending', 'approved']:
            raise ValidationError("Only pending or approved requests can be cancelled.")
        
        old_status = self.status
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()
        
        # Update leave balance based on old status
        if old_status == 'approved':
            self._restore_leave_balance()
        elif old_status == 'pending':
            self._release_pending_days()

    def _update_leave_balance(self):
        """Update leave balance when request is approved."""
        year = self.start_date.year
        balance, created = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            leave_type=self.leave_type,
            year=year,
            company=self.company,
            defaults={'accrued_days': self.leave_type.days_allowed}
        )
        
        # Move from pending to used
        balance.pending_days -= self.days_requested
        balance.used_days += self.days_requested
        balance.save()

    def _release_pending_days(self):
        """Release pending days when request is rejected or cancelled."""
        year = self.start_date.year
        try:
            balance = LeaveBalance.objects.get(
                employee=self.employee,
                leave_type=self.leave_type,
                year=year,
                company=self.company
            )
            balance.pending_days -= self.days_requested
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass

    def _restore_leave_balance(self):
        """Restore leave balance when approved request is cancelled."""
        year = self.start_date.year
        try:
            balance = LeaveBalance.objects.get(
                employee=self.employee,
                leave_type=self.leave_type,
                year=year,
                company=self.company
            )
            balance.used_days -= self.days_requested
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass