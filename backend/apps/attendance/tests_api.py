"""
API tests for biometric attendance endpoints.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.models import Company
from apps.employees.models import Employee, Department
from apps.attendance.models import AttendanceRecord
from apps.attendance.face_plugin_service import FacePluginService
from apps.authentication.models import Role, Permission

User = get_user_model()


class AttendanceAPITest(TestCase):
    """Test attendance API endpoints."""
    
    def setUp(self):
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            grace_period_minutes=15,
            working_hours_per_day=Decimal('8.0'),
            overtime_threshold_hours=Decimal('8.0')
        )
        
        # Create role and permissions
        self.role = Role.objects.create(
            name='Admin',
            company=self.company,
            is_system_role=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Engineering',
            company=self.company
        )
        
        # Create employee with biometric data
        face_service = FacePluginService()
        sample_biometric = {
            'face_encoding': [0.1] * 128,
            'quality_score': 0.95,
            'capture_timestamp': timezone.now().isoformat()
        }
        encrypted_biometric = face_service.enroll_face(sample_biometric)
        
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            company=self.company,
            hire_date=timezone.now().date(),
            biometric_data=encrypted_biometric
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            company=self.company,
            role=self.role,
            employee=self.employee
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_check_in_success(self):
        """Test successful check-in with biometric verification."""
        data = {
            'employee_id': 'EMP001',
            'biometric_data': {
                'face_encoding': [0.1] * 128,
                'quality_score': 0.95,
                'capture_timestamp': timezone.now().isoformat()
            },
            'terminal_id': 'TERMINAL_01'
        }
        
        response = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('attendance', response.data)
        self.assertIn('message', response.data)
        self.assertIn('similarity_score', response.data)
        self.assertTrue(response.data['attendance']['biometric_verified'])
    
    def test_check_in_missing_employee_id(self):
        """Test check-in without employee ID."""
        data = {
            'biometric_data': {
                'face_encoding': [0.1] * 128,
                'quality_score': 0.95
            }
        }
        
        response = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_check_in_missing_biometric_data(self):
        """Test check-in without biometric data."""
        data = {
            'employee_id': 'EMP001'
        }
        
        response = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_check_in_employee_not_found(self):
        """Test check-in with non-existent employee."""
        data = {
            'employee_id': 'INVALID',
            'biometric_data': {
                'face_encoding': [0.1] * 128,
                'quality_score': 0.95
            }
        }
        
        response = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_check_in_low_quality_biometric(self):
        """Test check-in with low quality biometric data."""
        data = {
            'employee_id': 'EMP001',
            'biometric_data': {
                'face_encoding': [0.1] * 128,
                'quality_score': 0.5  # Below threshold
            }
        }
        
        response = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_check_in_biometric_mismatch(self):
        """Test check-in with non-matching biometric data."""
        data = {
            'employee_id': 'EMP001',
            'biometric_data': {
                'face_encoding': [-x for x in [0.1] * 128],  # Negated encoding for mismatch
                'quality_score': 0.95
            }
        }
        
        response = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_check_in_already_checked_in(self):
        """Test check-in when already checked in."""
        # First check-in
        data = {
            'employee_id': 'EMP001',
            'biometric_data': {
                'face_encoding': [0.1] * 128,
                'quality_score': 0.95
            }
        }
        
        response1 = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second check-in attempt
        response2 = self.client.post('/api/v1/attendance/check-in/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_check_out_success(self):
        """Test successful check-out."""
        # First check in
        today = timezone.now().date()
        AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            biometric_verified=True,
            company=self.company
        )
        
        # Check out
        data = {
            'employee_id': 'EMP001',
            'terminal_id': 'TERMINAL_01'
        }
        
        response = self.client.post('/api/v1/attendance/check-out/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('attendance', response.data)
        self.assertIn('working_hours', response.data)
        self.assertIn('overtime_hours', response.data)
        self.assertIsNotNone(response.data['attendance']['check_out'])
    
    def test_check_out_no_check_in(self):
        """Test check-out without check-in."""
        data = {
            'employee_id': 'EMP001'
        }
        
        response = self.client.post('/api/v1/attendance/check-out/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_check_out_already_checked_out(self):
        """Test check-out when already checked out."""
        # Create completed attendance record
        today = timezone.now().date()
        AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now().replace(hour=9),
            check_out=timezone.now().replace(hour=17),
            working_hours=Decimal('8.0'),
            status='present',
            biometric_verified=True,
            company=self.company
        )
        
        data = {
            'employee_id': 'EMP001'
        }
        
        response = self.client.post('/api/v1/attendance/check-out/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_attendance_records(self):
        """Test retrieving attendance records."""
        # Create some attendance records
        today = timezone.now().date()
        AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            company=self.company
        )
        
        response = self.client.get('/api/v1/attendance/records/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_get_attendance_records_filtered_by_employee(self):
        """Test retrieving attendance records filtered by employee."""
        # Create attendance record
        today = timezone.now().date()
        AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            company=self.company
        )
        
        response = self.client.get('/api/v1/attendance/records/', {'employee_id': 'EMP001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_get_attendance_reports(self):
        """Test retrieving attendance reports."""
        # Create some attendance records
        today = timezone.now().date()
        AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now().replace(hour=9),
            check_out=timezone.now().replace(hour=17),
            working_hours=Decimal('8.0'),
            status='present',
            company=self.company
        )
        
        response = self.client.get('/api/v1/attendance/records/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('records', response.data)
        self.assertIn('total_records', response.data['summary'])
        self.assertIn('present', response.data['summary'])
        self.assertIn('average_working_hours', response.data['summary'])
    
    def test_unauthorized_access(self):
        """Test API access without authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/v1/attendance/records/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
