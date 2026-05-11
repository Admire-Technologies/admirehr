"""
Tests for attendance management, reporting, and export functionality.
"""

import pytest
from datetime import datetime, timedelta, time
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.core.models import Company
from apps.employees.models import Employee, Department
from apps.attendance.models import AttendanceRecord
from apps.attendance.policy import AttendancePolicy

User = get_user_model()


@pytest.fixture
def company():
    """Create a test company."""
    return Company.objects.create(
        name='Test Company',
        code='TEST001',
        email='test@company.com',
        working_hours_per_day=Decimal('8.0'),
        grace_period_minutes=15,
        overtime_threshold_hours=Decimal('8.0')
    )


@pytest.fixture
def department(company):
    """Create a test department."""
    return Department.objects.create(
        name='Engineering',
        company=company
    )


@pytest.fixture
def user(company):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        company=company
    )


@pytest.fixture
def employee(company, department):
    """Create a test employee."""
    return Employee.objects.create(
        employee_id='EMP001',
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        department=department,
        company=company,
        hire_date=timezone.now().date(),
        status='active'
    )


@pytest.fixture
def api_client(user):
    """Create an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestAttendanceFiltering:
    """Test attendance record filtering."""
    
    def test_filter_by_date_range(self, api_client, employee):
        """Test filtering attendance records by date range."""
        # Create attendance records for different dates
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        
        AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            company=employee.company
        )
        AttendanceRecord.objects.create(
            employee=employee,
            date=yesterday,
            check_in=timezone.now(),
            status='present',
            company=employee.company
        )
        AttendanceRecord.objects.create(
            employee=employee,
            date=two_days_ago,
            check_in=timezone.now(),
            status='late',
            company=employee.company
        )
        
        # Filter by date range
        response = api_client.get(
            '/api/v1/attendance/records/',
            {'start_date': yesterday.isoformat(), 'end_date': today.isoformat()}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_by_status(self, api_client, employee):
        """Test filtering attendance records by status."""
        today = timezone.now().date()
        
        AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            company=employee.company
        )
        AttendanceRecord.objects.create(
            employee=employee,
            date=today - timedelta(days=1),
            check_in=timezone.now(),
            status='late',
            company=employee.company
        )
        
        # Filter by status
        response = api_client.get(
            '/api/v1/attendance/records/',
            {'status': 'late'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'late'
    
    def test_filter_by_biometric_verified(self, api_client, employee):
        """Test filtering by biometric verification status."""
        today = timezone.now().date()
        
        AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            biometric_verified=True,
            company=employee.company
        )
        AttendanceRecord.objects.create(
            employee=employee,
            date=today - timedelta(days=1),
            check_in=timezone.now(),
            status='present',
            biometric_verified=False,
            company=employee.company
        )
        
        # Filter by biometric verified
        response = api_client.get(
            '/api/v1/attendance/records/',
            {'biometric_verified': 'true'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['biometric_verified'] is True


@pytest.mark.django_db
class TestAttendanceSummary:
    """Test attendance summary statistics."""
    
    def test_summary_statistics(self, api_client, employee, company):
        """Test calculation of summary statistics."""
        today = timezone.now().date()
        
        # Create various attendance records
        AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            check_out=timezone.now() + timedelta(hours=8),
            working_hours=Decimal('8.0'),
            status='present',
            company=company
        )
        AttendanceRecord.objects.create(
            employee=employee,
            date=today - timedelta(days=1),
            check_in=timezone.now(),
            check_out=timezone.now() + timedelta(hours=9),
            working_hours=Decimal('9.0'),
            status='late',
            company=company
        )
        
        response = api_client.get('/api/v1/attendance/records/summary/')
        
        assert response.status_code == 200
        assert response.data['total_records'] == 2
        assert response.data['present'] == 1
        assert response.data['late'] == 1
        assert response.data['average_working_hours'] == 8.5
        assert response.data['total_working_hours'] == 17.0
        assert response.data['total_overtime_hours'] == 1.0  # 9 - 8 = 1


@pytest.mark.django_db
class TestManualAttendanceEntry:
    """Test manual attendance entry functionality."""
    
    def test_create_manual_entry(self, api_client, employee):
        """Test creating a manual attendance entry."""
        today = timezone.now().date()
        check_in_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        check_out_time = check_in_time + timedelta(hours=8)
        
        data = {
            'employee_id_input': employee.employee_id,
            'date': today.isoformat(),
            'check_in': check_in_time.isoformat(),
            'check_out': check_out_time.isoformat(),
            'status': 'present',
            'notes': 'Manual entry for testing'
        }
        
        response = api_client.post('/api/v1/attendance/records/manual_entry/', data)
        
        assert response.status_code == 201
        assert response.data['biometric_verified'] is False
        assert response.data['status'] == 'present'
        assert response.data['notes'] == 'Manual entry for testing'
        assert response.data['working_hours'] == '8.00'
    
    def test_manual_entry_calculates_working_hours(self, api_client, employee):
        """Test that manual entry automatically calculates working hours."""
        today = timezone.now().date()
        check_in_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        check_out_time = check_in_time + timedelta(hours=7, minutes=30)
        
        data = {
            'employee_id_input': employee.employee_id,
            'date': today.isoformat(),
            'check_in': check_in_time.isoformat(),
            'check_out': check_out_time.isoformat(),
            'status': 'present'
        }
        
        response = api_client.post('/api/v1/attendance/records/manual_entry/', data)
        
        assert response.status_code == 201
        assert float(response.data['working_hours']) == 7.5
    
    def test_manual_entry_validation(self, api_client, employee):
        """Test validation for manual entry."""
        today = timezone.now().date()
        check_in_time = timezone.now().replace(hour=17, minute=0, second=0, microsecond=0)
        check_out_time = check_in_time - timedelta(hours=8)  # Invalid: check_out before check_in
        
        data = {
            'employee_id_input': employee.employee_id,
            'date': today.isoformat(),
            'check_in': check_in_time.isoformat(),
            'check_out': check_out_time.isoformat(),
            'status': 'present'
        }
        
        response = api_client.post('/api/v1/attendance/records/manual_entry/', data)
        
        assert response.status_code == 400
        assert 'check_out' in response.data


@pytest.mark.django_db
class TestAttendanceCorrection:
    """Test attendance record correction functionality."""
    
    def test_correct_attendance_record(self, api_client, employee):
        """Test correcting an existing attendance record."""
        today = timezone.now().date()
        check_in_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Create initial record
        record = AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=check_in_time,
            status='present',
            company=employee.company
        )
        
        # Correct the record
        new_check_in = check_in_time.replace(hour=10, minute=0)
        new_check_out = new_check_in + timedelta(hours=8)
        
        data = {
            'date': today.isoformat(),
            'check_in': new_check_in.isoformat(),
            'check_out': new_check_out.isoformat(),
            'status': 'late',
            'notes': 'Corrected time'
        }
        
        response = api_client.put(f'/api/v1/attendance/records/{record.id}/correct/', data)
        
        assert response.status_code == 200
        assert response.data['status'] == 'late'
        assert response.data['notes'] == 'Corrected time'
        assert response.data['working_hours'] == '8.00'
    
    def test_correction_recalculates_working_hours(self, api_client, employee):
        """Test that correction recalculates working hours."""
        today = timezone.now().date()
        
        record = AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            check_out=timezone.now() + timedelta(hours=8),
            working_hours=Decimal('8.0'),
            status='present',
            company=employee.company
        )
        
        # Correct with new times
        new_check_in = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        new_check_out = new_check_in + timedelta(hours=10)
        
        data = {
            'check_in': new_check_in.isoformat(),
            'check_out': new_check_out.isoformat()
        }
        
        response = api_client.patch(f'/api/v1/attendance/records/{record.id}/correct/', data)
        
        assert response.status_code == 200
        assert float(response.data['working_hours']) == 10.0


@pytest.mark.django_db
class TestAttendanceReports:
    """Test attendance report generation."""
    
    def test_generate_report(self, api_client, employee):
        """Test generating an attendance report."""
        today = timezone.now().date()
        start_date = today - timedelta(days=7)
        
        # Create attendance records
        for i in range(5):
            date = start_date + timedelta(days=i)
            AttendanceRecord.objects.create(
                employee=employee,
                date=date,
                check_in=timezone.now(),
                check_out=timezone.now() + timedelta(hours=8),
                working_hours=Decimal('8.0'),
                status='present',
                company=employee.company
            )
        
        response = api_client.get(
            '/api/v1/attendance/records/reports/',
            {
                'start_date': start_date.isoformat(),
                'end_date': today.isoformat()
            }
        )
        
        assert response.status_code == 200
        assert 'summary' in response.data
        assert 'records' in response.data
        assert response.data['summary']['total_records'] == 5
        assert len(response.data['records']) == 5


@pytest.mark.django_db
class TestDashboardStats:
    """Test dashboard statistics."""
    
    def test_dashboard_stats_today(self, api_client, employee, company):
        """Test dashboard statistics for today."""
        today = timezone.now().date()
        
        # Create today's attendance
        AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            company=company
        )
        
        # Create another employee without attendance
        Employee.objects.create(
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            department=employee.department,
            company=company,
            hire_date=today,
            status='active'
        )
        
        response = api_client.get('/api/v1/attendance/records/dashboard_stats/')
        
        assert response.status_code == 200
        assert response.data['total_employees'] == 2
        assert response.data['present'] == 1
        assert response.data['absent'] == 1
        assert response.data['date'] == today.isoformat()


@pytest.mark.django_db
class TestOvertimeCalculation:
    """Test overtime calculation logic."""
    
    def test_overtime_calculation(self, company):
        """Test overtime is calculated correctly."""
        policy = AttendancePolicy(company)
        
        # Test no overtime
        working_hours = Decimal('8.0')
        overtime = policy.calculate_overtime(working_hours)
        assert overtime == Decimal('0.0')
        
        # Test with overtime
        working_hours = Decimal('10.0')
        overtime = policy.calculate_overtime(working_hours)
        assert overtime == Decimal('2.0')
        
        # Test with partial overtime
        working_hours = Decimal('8.5')
        overtime = policy.calculate_overtime(working_hours)
        assert overtime == Decimal('0.5')
    
    def test_working_hours_calculation(self, company):
        """Test working hours calculation."""
        policy = AttendancePolicy(company)
        
        check_in = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        check_out = check_in + timedelta(hours=8, minutes=30)
        
        working_hours = policy.calculate_working_hours(check_in, check_out)
        assert working_hours == Decimal('8.50')


@pytest.mark.django_db
class TestAttendanceStatusDetermination:
    """Test attendance status determination logic."""
    
    def test_on_time_check_in(self, company):
        """Test on-time check-in status."""
        policy = AttendancePolicy(company)
        
        # Check in at 9:00 AM (on time)
        check_in_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        status = policy._determine_check_in_status(check_in_time)
        assert status == 'present'
    
    def test_late_check_in_within_grace(self, company):
        """Test check-in within grace period."""
        policy = AttendancePolicy(company)
        
        # Check in at 9:10 AM (within 15 min grace period)
        check_in_time = timezone.now().replace(hour=9, minute=10, second=0, microsecond=0)
        status = policy._determine_check_in_status(check_in_time)
        assert status == 'present'
    
    def test_late_check_in_after_grace(self, company):
        """Test late check-in after grace period."""
        policy = AttendancePolicy(company)
        
        # Check in at 9:30 AM (after grace period)
        check_in_time = timezone.now().replace(hour=9, minute=30, second=0, microsecond=0)
        status = policy._determine_check_in_status(check_in_time)
        assert status == 'late'
    
    def test_very_late_check_in(self, company):
        """Test very late check-in (half day)."""
        policy = AttendancePolicy(company)
        
        # Check in at 11:30 AM (more than 2 hours late)
        check_in_time = timezone.now().replace(hour=11, minute=30, second=0, microsecond=0)
        status = policy._determine_check_in_status(check_in_time)
        assert status == 'half_day'
