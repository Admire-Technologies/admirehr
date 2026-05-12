"""
Tests for Celery background job processing.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from celery import states

from apps.core.models import Company, JobExecution
from apps.core.tasks import (
    send_email_task,
    send_notification_email,
    cleanup_old_job_executions,
    health_check_task
)
from apps.authentication.models import User, Role, Permission
from apps.employees.models import Employee, Department


class CeleryTaskTestCase(TestCase):
    """Base test case for Celery tasks."""
    
    def setUp(self):
        """Set up test data."""
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        
        # Create permission and role
        self.permission = Permission.objects.create(
            name="test_permission",
            codename="test_perm"
        )
        
        self.role = Role.objects.create(
            name="Admin",
            company=self.company
        )
        self.role.permissions.add(self.permission)
        
        # Create department
        self.department = Department.objects.create(
            name="IT",
            company=self.company
        )
        
        # Create employee
        self.employee = Employee.objects.create(
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            company=self.company,
            department=self.department,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="testpass123",
            company=self.company,
            role=self.role,
            employee=self.employee
        )


@pytest.mark.django_db
class TestEmailTasks(CeleryTaskTestCase):
    """Tests for email-related tasks."""
    
    @patch('apps.core.tasks.send_mail')
    def test_send_email_task_success(self, mock_send_mail):
        """Test successful email sending."""
        result = send_email_task.apply(kwargs={
            'subject': 'Test Subject',
            'message': 'Test Message',
            'recipient_list': ['test@example.com']
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        assert result.result['recipients'] == ['test@example.com']
        mock_send_mail.assert_called_once()
    
    @patch('apps.core.tasks.send_mail')
    def test_send_email_task_with_html(self, mock_send_mail):
        """Test email sending with HTML content."""
        result = send_email_task.apply(kwargs={
            'subject': 'Test Subject',
            'message': 'Plain text message',
            'recipient_list': ['test@example.com'],
            'html_message': '<p>HTML message</p>'
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
    
    @patch('apps.core.tasks.send_email_task')
    def test_send_notification_email(self, mock_send_email):
        """Test notification email sending."""
        result = send_notification_email.apply(kwargs={
            'user_id': str(self.user.id),
            'notification_type': 'leave_approved',
            'context': {
                'leave_type': 'Annual Leave',
                'start_date': '2024-01-01',
                'end_date': '2024-01-05',
                'days': 5,
                'approver_name': 'Manager'
            }
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        assert result.result['user_id'] == str(self.user.id)
        mock_send_email.delay.assert_called_once()


@pytest.mark.django_db
class TestJobExecutionTracking(CeleryTaskTestCase):
    """Tests for job execution tracking."""
    
    def test_job_execution_creation(self):
        """Test creating job execution record."""
        job = JobExecution.objects.create(
            task_id='test-task-123',
            task_name='apps.core.tasks.test_task',
            status='pending'
        )
        
        assert job.task_id == 'test-task-123'
        assert job.status == 'pending'
        assert not job.is_completed
    
    def test_job_execution_duration(self):
        """Test job duration calculation."""
        job = JobExecution.objects.create(
            task_id='test-task-123',
            task_name='apps.core.tasks.test_task',
            status='success',
            started_at=timezone.now() - timedelta(seconds=30),
            completed_at=timezone.now()
        )
        
        assert job.duration is not None
        assert job.duration >= 29  # Allow for small timing differences
        assert job.is_completed
    
    def test_cleanup_old_job_executions(self):
        """Test cleanup of old job execution records."""
        # Create old job executions
        old_date = timezone.now() - timedelta(days=35)
        for i in range(5):
            job = JobExecution.objects.create(
                task_id=f'old-task-{i}',
                task_name='apps.core.tasks.old_task',
                status='success'
            )
            job.created_at = old_date
            job.save()
        
        # Create recent job executions
        for i in range(3):
            JobExecution.objects.create(
                task_id=f'recent-task-{i}',
                task_name='apps.core.tasks.recent_task',
                status='success'
            )
        
        # Run cleanup
        result = cleanup_old_job_executions.apply(kwargs={'days': 30})
        
        assert result.successful()
        assert result.result['deleted_count'] == 5
        assert JobExecution.objects.count() == 3


@pytest.mark.django_db
class TestHealthCheckTask(CeleryTaskTestCase):
    """Tests for health check task."""
    
    def test_health_check_task(self):
        """Test health check task execution."""
        result = health_check_task.apply()
        
        assert result.successful()
        assert result.result['status'] == 'healthy'
        assert 'timestamp' in result.result
        assert 'worker' in result.result


@pytest.mark.django_db
class TestTaskFailureHandling(CeleryTaskTestCase):
    """Tests for task failure handling."""
    
    @patch('apps.core.tasks.send_mail')
    def test_email_task_retry_on_failure(self, mock_send_mail):
        """Test email task retries on failure."""
        mock_send_mail.side_effect = Exception("SMTP connection failed")
        
        result = send_email_task.apply(kwargs={
            'subject': 'Test',
            'message': 'Test',
            'recipient_list': ['test@example.com']
        })
        
        # Task should fail after retries
        assert result.failed()
    
    def test_job_execution_failure_logging(self):
        """Test that failed tasks are logged in JobExecution."""
        # This would be tested with actual task execution
        # For now, we test the model directly
        job = JobExecution.objects.create(
            task_id='failed-task-123',
            task_name='apps.core.tasks.failing_task',
            status='failed',
            error_message='Task failed due to error',
            error_traceback='Traceback...',
            retry_count=3
        )
        
        assert job.status == 'failed'
        assert job.error_message == 'Task failed due to error'
        assert job.retry_count == 3


@pytest.mark.django_db
class TestTaskCallbacks(CeleryTaskTestCase):
    """Tests for task callback functionality."""
    
    def test_callback_task_on_success(self):
        """Test CallbackTask on_success method."""
        from apps.core.tasks import CallbackTask
        
        task = CallbackTask()
        task.name = 'test_task'
        
        # Should not raise exception
        task.on_success('result', 'task-id-123', [], {})
    
    def test_callback_task_on_failure(self):
        """Test CallbackTask on_failure method."""
        from apps.core.tasks import CallbackTask
        
        task = CallbackTask()
        task.name = 'test_task'
        
        # Should create JobExecution record
        task.on_failure(
            Exception("Test error"),
            'task-id-123',
            [],
            {},
            'Traceback info'
        )
        
        # Check if JobExecution was created
        job = JobExecution.objects.filter(task_id='task-id-123').first()
        assert job is not None
        assert job.status == 'failed'


@pytest.mark.django_db
class TestCeleryConfiguration(TestCase):
    """Tests for Celery configuration."""
    
    def test_celery_app_configuration(self):
        """Test Celery app is properly configured."""
        from admire_hrms.celery import app
        
        assert app.conf.broker_url is not None
        assert app.conf.result_backend is not None
        assert app.conf.task_serializer == 'json'
        assert app.conf.result_serializer == 'json'
    
    def test_celery_beat_schedule_configured(self):
        """Test Celery Beat schedule is configured."""
        from django.conf import settings
        
        assert hasattr(settings, 'CELERY_BEAT_SCHEDULE')
        assert 'monthly-payroll-generation' in settings.CELERY_BEAT_SCHEDULE
        assert 'initialize-annual-leave-balances' in settings.CELERY_BEAT_SCHEDULE
        assert 'health-check' in settings.CELERY_BEAT_SCHEDULE


@pytest.mark.django_db
class TestTaskDiscovery(TestCase):
    """Tests for task discovery and registration."""
    
    def test_tasks_are_discovered(self):
        """Test that tasks are properly discovered by Celery."""
        from admire_hrms.celery import app
        
        # Import tasks to ensure they're registered
        import apps.core.tasks
        import apps.payroll.tasks
        import apps.leave_management.tasks
        import apps.attendance.tasks
        
        # Check if tasks are registered
        registered_tasks = list(app.tasks.keys())
        
        # Core tasks
        assert 'apps.core.tasks.send_email_task' in registered_tasks
        assert 'apps.core.tasks.health_check_task' in registered_tasks
        
        # Payroll tasks
        assert 'apps.payroll.tasks.generate_payroll_for_employee' in registered_tasks
        assert 'apps.payroll.tasks.bulk_generate_payroll' in registered_tasks
        
        # Leave tasks
        assert 'apps.leave_management.tasks.send_leave_approval_notification' in registered_tasks
        
        # Attendance tasks
        assert 'apps.attendance.tasks.generate_attendance_report' in registered_tasks
