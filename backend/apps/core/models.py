"""
Core models for the HRMS application.
"""

import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(BaseModel):
    """
    Company model for multi-tenant support.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Configuration settings
    settings = models.JSONField(default=dict, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    currency = models.CharField(max_length=3, default='USD')
    
    # Business settings
    working_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    working_days_per_week = models.IntegerField(default=5)
    
    # Leave policy settings
    annual_leave_days = models.IntegerField(default=21)
    sick_leave_days = models.IntegerField(default=10)
    
    # Attendance settings
    grace_period_minutes = models.IntegerField(default=15)
    overtime_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    
    # System settings
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50, default='basic')
    max_employees = models.IntegerField(default=100)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_setting(self, key, default=None):
        """
        Get a specific setting value from the settings JSON field.
        """
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """
        Set a specific setting value in the settings JSON field.
        """
        if not self.settings:
            self.settings = {}
        self.settings[key] = value

    @property
    def employee_count(self):
        """
        Get the current number of employees in the company.
        """
        return self.employee_set.filter(status='active').count()

    def can_add_employee(self):
        """
        Check if the company can add more employees based on subscription limits.
        """
        return self.employee_count < self.max_employees


class TenantAwareModel(BaseModel):
    """
    Abstract model that includes company for multi-tenant support.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Use the tenant-aware manager
    objects = models.Manager()  # Default manager for admin and migrations
    tenant_objects = None  # Will be set after TenantAwareManager is defined
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Automatically set the company if not already set.
        """
        if not self.company_id:
            from .middleware import get_current_company
            current_company = get_current_company()
            if current_company:
                self.company = current_company
        super().save(*args, **kwargs)


# Set the tenant-aware manager after it's imported
from .middleware import TenantAwareManager
TenantAwareModel.add_to_class('tenant_objects', TenantAwareManager())



class SecurityPolicy(TenantAwareModel):
    """
    Security policy configuration for companies.
    Implements Requirement 10.2: Secure password policies and security configuration.
    """
    POLICY_TYPE_CHOICES = [
        ('password', 'Password Policy'),
        ('session', 'Session Policy'),
        ('access', 'Access Control Policy'),
        ('data', 'Data Protection Policy'),
    ]
    
    name = models.CharField(max_length=255)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Policy configuration (JSON)
    configuration = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    enforced = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Security Policies"
        ordering = ['policy_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.company.name})"
    
    def get_config(self, key, default=None):
        """Get a specific configuration value."""
        return self.configuration.get(key, default)
    
    def set_config(self, key, value):
        """Set a specific configuration value."""
        if not self.configuration:
            self.configuration = {}
        self.configuration[key] = value
    
    @classmethod
    def get_password_policy(cls, company):
        """
        Get active password policy for a company.
        Returns default policy if none exists.
        """
        try:
            return cls.objects.get(
                company=company,
                policy_type='password',
                is_active=True
            )
        except cls.DoesNotExist:
            # Return default password policy
            return cls.get_default_password_policy()
    
    @staticmethod
    def get_default_password_policy():
        """Get default password policy configuration."""
        return {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'password_expiry_days': 90,
            'password_history_count': 5,
            'max_login_attempts': 5,
            'lockout_duration_minutes': 30,
        }
    
    @classmethod
    def get_session_policy(cls, company):
        """Get active session policy for a company."""
        try:
            return cls.objects.get(
                company=company,
                policy_type='session',
                is_active=True
            )
        except cls.DoesNotExist:
            return cls.get_default_session_policy()
    
    @staticmethod
    def get_default_session_policy():
        """Get default session policy configuration."""
        return {
            'session_timeout_minutes': 60,
            'idle_timeout_minutes': 30,
            'max_concurrent_sessions': 3,
            'require_mfa': False,
        }


class DataBackup(TenantAwareModel):
    """
    Data backup tracking and management.
    Implements Requirement 10.6: Encrypted backups and secure data recovery.
    """
    BACKUP_TYPE_CHOICES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
        ('differential', 'Differential Backup'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Backup details
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    encrypted = models.BooleanField(default=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    tables_backed_up = models.JSONField(default=list, blank=True)
    record_counts = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Retention
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.backup_type} backup for {self.company.name} - {self.status}"
    
    @property
    def duration_seconds(self):
        """Calculate backup duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def file_size_mb(self):
        """Get file size in megabytes."""
        if self.file_size_bytes:
            return round(self.file_size_bytes / (1024 * 1024), 2)
        return None


class SecurityEvent(TenantAwareModel):
    """
    Security event logging for monitoring and analysis.
    Implements Requirement 10.4: Security event logging and blocking measures.
    """
    EVENT_TYPE_CHOICES = [
        ('login_success', 'Login Success'),
        ('login_failure', 'Login Failure'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('permission_denied', 'Permission Denied'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('data_export', 'Data Export'),
        ('data_deletion', 'Data Deletion'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    
    # User and request info
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Event details
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Response
    action_taken = models.CharField(max_length=100, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['severity', 'resolved']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.created_at}"
    
    @classmethod
    def log_event(cls, event_type, company, description, user=None, 
                  ip_address=None, user_agent=None, severity='low', details=None):
        """
        Helper method to create security event entries.
        
        Args:
            event_type: Type of security event
            company: Company instance
            description: Human-readable description
            user: User involved (optional)
            ip_address: IP address (optional)
            user_agent: User agent string (optional)
            severity: Event severity level
            details: Additional details dictionary
        """
        return cls.objects.create(
            event_type=event_type,
            company=company,
            description=description,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent or '',
            severity=severity,
            details=details or {}
        )


class JobExecution(models.Model):
    """
    Job execution model for tracking background task execution.
    Implements Requirement 5.6: Job monitoring and failure handling.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    task_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Task details
    args = models.JSONField(default=list, blank=True)
    kwargs = models.JSONField(default=dict, blank=True)
    result = models.JSONField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    worker_name = models.CharField(max_length=255, blank=True)
    queue_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_name', 'status', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.task_name} [{self.task_id}] - {self.status}"
    
    @property
    def duration(self):
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_completed(self):
        """Check if task is completed (success or failed)."""
        return self.status in ['success', 'failed']
