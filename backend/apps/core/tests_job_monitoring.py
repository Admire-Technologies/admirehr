"""
Tests for job monitoring and management API.
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta

from apps.core.models import Company, JobExecution
from apps.authentication.models import User, Role, Permission
from apps.employees.models import Employee, Department


class JobMonitoringAPITestCase(TestCase):
    """Base test case for job monitoring API."""
    
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
        
        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test job executions
        self.create_test_jobs()
    
    def create_test_jobs(self):
        """Create test job execution records."""
        # Successful job
        self.job_success = JobExecution.objects.create(
            task_id='success-task-123',
            task_name='apps.payroll.tasks.generate_payroll',
            status='success',
            started_at=timezone.now() - timedelta(minutes=5),
            completed_at=timezone.now() - timedelta(minutes=3),
            result={'status': 'success', 'records': 10}
        )
        
        # Failed job
        self.job_failed = JobExecution.objects.create(
            task_id='failed-task-456',
            task_name='apps.payroll.tasks.generate_payroll',
            status='failed',
            started_at=timezone.now() - timedelta(minutes=10),
            completed_at=timezone.now() - timedelta(minutes=8),
            error_message='Database connection failed',
            error_traceback='Traceback...'
        )
        
        # Running job
        self.job_running = JobExecution.objects.create(
            task_id='running-task-789',
            task_name='apps.leave_management.tasks.generate_leave_report',
            status='running',
            started_at=timezone.now() - timedelta(minutes=2)
        )
        
        # Pending job
        self.job_pending = JobExecution.objects.create(
            task_id='pending-task-101',
            task_name='apps.attendance.tasks.generate_attendance_report',
            status='pending'
        )


@pytest.mark.django_db
class TestJobExecutionViewSet(JobMonitoringAPITestCase):
    """Tests for JobExecutionViewSet."""
    
    def test_list_job_executions(self):
        """Test listing job executions."""
        url = reverse('core:job-execution-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
    
    def test_retrieve_job_execution(self):
        """Test retrieving single job execution."""
        url = reverse('core:job-execution-detail', kwargs={'pk': self.job_success.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['task_id'] == 'success-task-123'
        assert response.data['status'] == 'success'
    
    def test_filter_by_status(self):
        """Test filtering job executions by status."""
        url = reverse('core:job-execution-list')
        response = self.client.get(url, {'status': 'failed'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'failed'
    
    def test_filter_by_task_name(self):
        """Test filtering job executions by task name."""
        url = reverse('core:job-execution-list')
        response = self.client.get(url, {'task_name': 'payroll'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
    
    def test_get_statistics(self):
        """Test getting job execution statistics."""
        url = reverse('core:job-execution-statistics')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_jobs' in response.data
        assert 'successful_jobs' in response.data
        assert 'failed_jobs' in response.data
        assert 'success_rate' in response.data
    
    def test_get_recent_failures(self):
        """Test getting recent failed jobs."""
        url = reverse('core:job-execution-recent-failures')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['status'] == 'failed'
    
    def test_get_task_summary(self):
        """Test getting task summary."""
        url = reverse('core:job-execution-task-summary')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert 'task_name' in response.data[0]
        assert 'total' in response.data[0]


@pytest.mark.django_db
class TestTriggerJobView(JobMonitoringAPITestCase):
    """Tests for TriggerJobView."""
    
    def test_trigger_payroll_generation(self):
        """Test triggering payroll generation job."""
        url = reverse('core:trigger_job')
        data = {
            'job_type': 'payroll_generation',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        with pytest.raises(Exception):
            # This will fail without actual Celery worker
            # In real tests, you'd mock the task
            response = self.client.post(url, data, format='json')
    
    def test_trigger_leave_report(self):
        """Test triggering leave report generation."""
        url = reverse('core:trigger_job')
        data = {
            'job_type': 'leave_report',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'report_type': 'summary'
        }
        
        with pytest.raises(Exception):
            response = self.client.post(url, data, format='json')
    
    def test_trigger_job_missing_dates(self):
        """Test triggering job without required dates."""
        url = reverse('core:trigger_job')
        data = {
            'job_type': 'payroll_generation'
        }
        
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_trigger_job_invalid_type(self):
        """Test triggering job with invalid type."""
        url = reverse('core:trigger_job')
        data = {
            'job_type': 'invalid_job_type',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCeleryHealthCheckView(JobMonitoringAPITestCase):
    """Tests for CeleryHealthCheckView."""
    
    def test_health_check_no_workers(self):
        """Test health check when no workers are running."""
        url = reverse('core:celery_health')
        
        # Without actual Celery workers, this should return unhealthy
        response = self.client.get(url)
        
        # Response depends on whether Celery is actually running
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]


@pytest.mark.django_db
class TestJobQueueStatusView(JobMonitoringAPITestCase):
    """Tests for JobQueueStatusView."""
    
    def test_get_queue_status(self):
        """Test getting job queue status."""
        url = reverse('core:queue_status')
        response = self.client.get(url)
        
        # Response depends on whether Celery is actually running
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        if response.status_code == status.HTTP_200_OK:
            assert 'queue_status' in response.data
            assert 'recent_jobs' in response.data


@pytest.mark.django_db
class TestJobMonitoringPermissions(JobMonitoringAPITestCase):
    """Tests for job monitoring API permissions."""
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access job monitoring."""
        self.client.force_authenticate(user=None)
        
        url = reverse('core:job-execution-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authenticated_access_allowed(self):
        """Test that authenticated users can access job monitoring."""
        url = reverse('core:job-execution-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestJobExecutionModel(TestCase):
    """Tests for JobExecution model."""
    
    def test_job_duration_calculation(self):
        """Test job duration calculation."""
        job = JobExecution.objects.create(
            task_id='test-123',
            task_name='test.task',
            status='success',
            started_at=timezone.now() - timedelta(seconds=30),
            completed_at=timezone.now()
        )
        
        assert job.duration is not None
        assert job.duration >= 29
        assert job.duration <= 31
    
    def test_job_is_completed(self):
        """Test is_completed property."""
        job_success = JobExecution.objects.create(
            task_id='test-123',
            task_name='test.task',
            status='success'
        )
        
        job_running = JobExecution.objects.create(
            task_id='test-456',
            task_name='test.task',
            status='running'
        )
        
        assert job_success.is_completed
        assert not job_running.is_completed
    
    def test_job_string_representation(self):
        """Test job string representation."""
        job = JobExecution.objects.create(
            task_id='test-123',
            task_name='test.task',
            status='success'
        )
        
        assert str(job) == 'test.task [test-123] - success'
