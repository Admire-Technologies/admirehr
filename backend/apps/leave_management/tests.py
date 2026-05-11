"""
Tests for leave management system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal

from apps.core.models import Company
from apps.authentication.models import Role
from apps.employees.models import Employee, Department
from .models import LeaveType, LeaveRequest, LeaveBalance

User = get_user_model()


class LeaveTypeTest(TestCase):
    """Test LeaveType model and API."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )
        self.role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            company=self.company,
            role=self.role
        )
        self.client.force_authenticate(user=self.user)

    def test_create_leave_type(self):
        """Test creating a leave type."""
        data = {
            'name': 'Annual Leave',
            'description': 'Annual vacation leave',
            'days_allowed': 21,
            'is_active': True,
            'allow_negative_balance': False,
            'requires_approval': True
        }
        response = self.client.post('/api/v1/leave/types/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LeaveType.objects.count(), 1)
        leave_type = LeaveType.objects.first()
        self.assertEqual(leave_type.name, 'Annual Leave')
        self.assertEqual(leave_type.days_allowed, 21)
        self.assertEqual(leave_type.company, self.company)

    def test_list_leave_types(self):
        """Test listing leave types."""
        LeaveType.objects.create(
            company=self.company,
            name='Annual Leave',
            days_allowed=21
        )
        LeaveType.objects.create(
            company=self.company,
            name='Sick Leave',
            days_allowed=10
        )

        response = self.client.get('/api/v1/leave/types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 2)


class LeaveBalanceTest(TestCase):
    """Test LeaveBalance model and calculations."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )
        self.department = Department.objects.create(
            company=self.company,
            name='IT'
        )
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        self.leave_type = LeaveType.objects.create(
            company=self.company,
            name='Annual Leave',
            days_allowed=21
        )

    def test_create_leave_balance(self):
        """Test creating a leave balance."""
        balance = LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            year=2024,
            accrued_days=21
        )
        self.assertEqual(balance.accrued_days, 21)
        self.assertEqual(balance.used_days, 0)
        self.assertEqual(balance.available_days, 21)

    def test_available_days_calculation(self):
        """Test available days calculation."""
        balance = LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            year=2024,
            accrued_days=21,
            used_days=5,
            pending_days=3
        )
        self.assertEqual(balance.available_days, 13)

    def test_can_apply_leave(self):
        """Test can_apply_leave method."""
        balance = LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            year=2024,
            accrued_days=21,
            used_days=15
        )
        self.assertTrue(balance.can_apply_leave(5))
        self.assertFalse(balance.can_apply_leave(10))

    def test_can_apply_leave_with_negative_balance(self):
        """Test can_apply_leave with negative balance allowed."""
        leave_type = LeaveType.objects.create(
            company=self.company,
            name='Sick Leave',
            days_allowed=10,
            allow_negative_balance=True
        )
        balance = LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=leave_type,
            year=2024,
            accrued_days=10,
            used_days=10
        )
        self.assertTrue(balance.can_apply_leave(5))


class LeaveRequestTest(TestCase):
    """Test LeaveRequest model and API."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )
        self.role = Role.objects.create(
            name='Employee',
            company=self.company
        )
        self.department = Department.objects.create(
            company=self.company,
            name='IT'
        )
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        self.manager = Employee.objects.create(
            company=self.company,
            employee_id='MGR001',
            first_name='Jane',
            last_name='Manager',
            email='jane@test.com',
            department=self.department,
            hire_date='2023-01-01'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            company=self.company,
            role=self.role,
            employee=self.employee
        )
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            company=self.company,
            role=self.role,
            employee=self.manager
        )
        self.leave_type = LeaveType.objects.create(
            company=self.company,
            name='Annual Leave',
            days_allowed=21
        )
        # Initialize leave balance
        LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            year=datetime.now().year,
            accrued_days=21
        )
        self.client.force_authenticate(user=self.user)

    def test_create_leave_request(self):
        """Test creating a leave request."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        end_date = (timezone.now() + timedelta(days=10)).date()
        
        data = {
            'leave_type': str(self.leave_type.id),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days_requested': 4,
            'reason': 'Family vacation'
        }
        response = self.client.post('/api/v1/leave/requests/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LeaveRequest.objects.count(), 1)
        
        leave_request = LeaveRequest.objects.first()
        self.assertEqual(leave_request.employee, self.employee)
        self.assertEqual(leave_request.status, 'pending')
        
        # Check that pending days were updated
        balance = LeaveBalance.objects.get(
            employee=self.employee,
            leave_type=self.leave_type,
            year=start_date.year
        )
        self.assertEqual(balance.pending_days, 4)

    def test_create_leave_request_insufficient_balance(self):
        """Test creating leave request with insufficient balance."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        end_date = (timezone.now() + timedelta(days=30)).date()
        
        data = {
            'leave_type': str(self.leave_type.id),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days_requested': 25,
            'reason': 'Long vacation'
        }
        response = self.client.post('/api/v1/leave/requests/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient leave balance', str(response.data))

    def test_create_leave_request_past_date(self):
        """Test creating leave request with past date."""
        start_date = (timezone.now() - timedelta(days=7)).date()
        end_date = (timezone.now() - timedelta(days=5)).date()
        
        data = {
            'leave_type': str(self.leave_type.id),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days_requested': 3,
            'reason': 'Past leave'
        }
        response = self.client.post('/api/v1/leave/requests/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot apply for leave in the past', str(response.data))

    def test_create_leave_request_invalid_dates(self):
        """Test creating leave request with invalid dates."""
        start_date = (timezone.now() + timedelta(days=10)).date()
        end_date = (timezone.now() + timedelta(days=7)).date()
        
        data = {
            'leave_type': str(self.leave_type.id),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days_requested': 4,
            'reason': 'Invalid dates'
        }
        response = self.client.post('/api/v1/leave/requests/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_leave_request(self):
        """Test approving a leave request."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        leave_request = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Test leave',
            status='pending'
        )
        
        # Update balance with pending days
        balance = LeaveBalance.objects.get(
            employee=self.employee,
            leave_type=self.leave_type,
            year=start_date.year
        )
        balance.pending_days = 4
        balance.save()
        
        # Authenticate as manager
        self.client.force_authenticate(user=self.manager_user)
        
        data = {'action': 'approve'}
        response = self.client.post(
            f'/api/v1/leave/requests/{leave_request.id}/approve_reject/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'approved')
        self.assertEqual(leave_request.approver, self.manager)
        self.assertIsNotNone(leave_request.approved_at)
        
        # Check balance was updated
        balance.refresh_from_db()
        self.assertEqual(balance.pending_days, 0)
        self.assertEqual(balance.used_days, 4)

    def test_reject_leave_request(self):
        """Test rejecting a leave request."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        leave_request = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Test leave',
            status='pending'
        )
        
        # Update balance with pending days
        balance = LeaveBalance.objects.get(
            employee=self.employee,
            leave_type=self.leave_type,
            year=start_date.year
        )
        balance.pending_days = 4
        balance.save()
        
        # Authenticate as manager
        self.client.force_authenticate(user=self.manager_user)
        
        data = {
            'action': 'reject',
            'rejection_reason': 'Not enough coverage'
        }
        response = self.client.post(
            f'/api/v1/leave/requests/{leave_request.id}/approve_reject/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'rejected')
        self.assertEqual(leave_request.rejection_reason, 'Not enough coverage')
        
        # Check pending days were released
        balance.refresh_from_db()
        self.assertEqual(balance.pending_days, 0)
        self.assertEqual(balance.used_days, 0)

    def test_reject_without_reason(self):
        """Test rejecting leave request without reason fails."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        leave_request = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Test leave',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.manager_user)
        
        data = {'action': 'reject'}
        response = self.client.post(
            f'/api/v1/leave/requests/{leave_request.id}/approve_reject/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_leave_request(self):
        """Test cancelling a leave request."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        leave_request = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Test leave',
            status='pending'
        )
        
        # Update balance with pending days
        balance = LeaveBalance.objects.get(
            employee=self.employee,
            leave_type=self.leave_type,
            year=start_date.year
        )
        balance.pending_days = 4
        balance.save()
        
        data = {'cancellation_reason': 'Plans changed'}
        response = self.client.post(
            f'/api/v1/leave/requests/{leave_request.id}/cancel/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'cancelled')
        self.assertIsNotNone(leave_request.cancelled_at)
        
        # Check pending days were released
        balance.refresh_from_db()
        self.assertEqual(balance.pending_days, 0)

    def test_cancel_approved_leave_request(self):
        """Test cancelling an approved leave request."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        leave_request = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Test leave',
            status='approved',
            approver=self.manager
        )
        
        # Update balance with used days
        balance = LeaveBalance.objects.get(
            employee=self.employee,
            leave_type=self.leave_type,
            year=start_date.year
        )
        balance.used_days = 4
        balance.save()
        
        data = {'cancellation_reason': 'Emergency at work'}
        response = self.client.post(
            f'/api/v1/leave/requests/{leave_request.id}/cancel/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'cancelled')
        
        # Check used days were restored
        balance.refresh_from_db()
        self.assertEqual(balance.used_days, 0)

    def test_my_requests(self):
        """Test getting current user's leave requests."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='My leave'
        )
        
        response = self.client.get('/api/v1/leave/requests/my_requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)

    def test_pending_approvals(self):
        """Test getting pending approvals."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Pending leave',
            status='pending'
        )
        
        # Authenticate as manager
        self.client.force_authenticate(user=self.manager_user)
        
        response = self.client.get('/api/v1/leave/requests/pending_approvals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)

    def test_leave_calendar(self):
        """Test leave calendar endpoint."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Calendar test',
            status='approved'
        )
        
        calendar_start = start_date.isoformat()
        calendar_end = (start_date + timedelta(days=30)).isoformat()
        
        response = self.client.get(
            f'/api/v1/leave/requests/calendar/?start_date={calendar_start}&end_date={calendar_end}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['employee_name'], 'John Doe')

    def test_leave_reports(self):
        """Test leave reports endpoint."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='Report test',
            status='approved'
        )
        
        response = self.client.get(f'/api/v1/leave/requests/reports/?year={start_date.year}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('leave_by_type', response.data)
        self.assertEqual(response.data['summary']['total_requests'], 1)
        self.assertEqual(response.data['summary']['approved'], 1)

    def test_overlapping_leave_requests(self):
        """Test that overlapping leave requests are prevented."""
        start_date = (timezone.now() + timedelta(days=7)).date()
        
        # Create first leave request
        LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            days_requested=4,
            reason='First leave',
            status='approved'
        )
        
        # Try to create overlapping leave request
        data = {
            'leave_type': str(self.leave_type.id),
            'start_date': (start_date + timedelta(days=2)).isoformat(),
            'end_date': (start_date + timedelta(days=5)).isoformat(),
            'days_requested': 4,
            'reason': 'Overlapping leave'
        }
        response = self.client.post('/api/v1/leave/requests/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LeaveBalanceAPITest(TestCase):
    """Test LeaveBalance API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )
        self.role = Role.objects.create(
            name='Employee',
            company=self.company
        )
        self.department = Department.objects.create(
            company=self.company,
            name='IT'
        )
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            company=self.company,
            role=self.role,
            employee=self.employee
        )
        self.leave_type = LeaveType.objects.create(
            company=self.company,
            name='Annual Leave',
            days_allowed=21
        )
        self.client.force_authenticate(user=self.user)

    def test_my_balance(self):
        """Test getting current user's leave balance."""
        LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            year=datetime.now().year,
            accrued_days=21,
            used_days=5
        )
        
        response = self.client.get('/api/v1/leave/balances/my_balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]['available_days']), 16.0)

    def test_initialize_balances(self):
        """Test initializing leave balances for all employees."""
        # Create another employee
        Employee.objects.create(
            company=self.company,
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            department=self.department,
            hire_date='2024-01-01',
            status='active'
        )
        
        # Create another leave type
        LeaveType.objects.create(
            company=self.company,
            name='Sick Leave',
            days_allowed=10,
            is_active=True
        )
        
        data = {'year': datetime.now().year}
        response = self.client.post('/api/v1/leave/balances/initialize_balances/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created_count'], 4)  # 2 employees x 2 leave types
