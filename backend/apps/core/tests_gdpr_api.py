"""
API tests for GDPR compliance endpoints.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.models import Company
from apps.employees.models import Employee, Department
from apps.authentication.models import User, Role, Permission


class GDPRAPITest(TestCase):
    """Test GDPR compliance API endpoints."""
    
    def setUp(self):
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        
        # Create department
        self.department = Department.objects.create(
            name="Engineering",
            company=self.company
        )
        
        # Create employee
        self.employee = Employee.objects.create(
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            phone="1234567890",
            department=self.department,
            company=self.company,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        
        # Create regular user linked to employee
        self.regular_user = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="emppass123",
            company=self.company,
            employee=self.employee
        )
        
        self.client = APIClient()
    
    def test_export_own_data(self):
        """Test employee exporting their own data."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('core:gdpr_export')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('export_date', response.data)
        self.assertIn('personal_information', response.data)
        self.assertEqual(
            response.data['personal_information']['first_name'],
            'John'
        )
    
    def test_export_other_employee_data_forbidden(self):
        """Test that regular users cannot export other employees' data."""
        # Create another employee
        other_employee = Employee.objects.create(
            employee_id="EMP002",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            department=self.department,
            company=self.company,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('core:gdpr_export_employee', kwargs={'employee_id': other_employee.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_export_any_employee_data(self):
        """Test that admins can export any employee's data."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('core:gdpr_export_employee', kwargs={'employee_id': self.employee.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('personal_information', response.data)
    
    def test_delete_employee_data_admin_only(self):
        """Test that only admins can delete employee data."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('core:gdpr_delete', kwargs={'employee_id': self.employee.id})
        response = self.client.post(url, {'anonymize': True})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_anonymize_employee_data(self):
        """Test admin anonymizing employee data."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('core:gdpr_delete', kwargs={'employee_id': self.employee.id})
        response = self.client.post(url, {'anonymize': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertTrue(response.data['summary']['anonymized'])
        
        # Verify employee was anonymized
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.email.startswith('deleted_'))
    
    def test_data_processing_report_admin_only(self):
        """Test that only admins can access data processing report."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('core:gdpr_report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_data_processing_report(self):
        """Test admin accessing data processing report."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('core:gdpr_report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('company', response.data)
        self.assertIn('data_categories', response.data)
        self.assertIn('security_measures', response.data)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access GDPR endpoints."""
        url = reverse('core:gdpr_export')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SecurityEventAPITest(TestCase):
    """Test security event API endpoints."""
    
    def setUp(self):
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="emppass123",
            company=self.company
        )
        
        self.client = APIClient()
    
    def test_list_security_events_admin_only(self):
        """Test that only admins can list security events."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('core:security_events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_list_security_events(self):
        """Test admin listing security events."""
        from apps.core.models import SecurityEvent
        
        # Create some security events
        SecurityEvent.objects.create(
            company=self.company,
            event_type='login_failure',
            severity='medium',
            description='Failed login attempt',
            user=self.regular_user,
            ip_address='192.168.1.100'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('core:security_events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('events', response.data)
        self.assertGreater(response.data['count'], 0)
    
    def test_filter_security_events_by_type(self):
        """Test filtering security events by type."""
        from apps.core.models import SecurityEvent
        
        # Create events of different types
        SecurityEvent.objects.create(
            company=self.company,
            event_type='login_failure',
            severity='medium',
            description='Failed login',
            user=self.regular_user
        )
        SecurityEvent.objects.create(
            company=self.company,
            event_type='unauthorized_access',
            severity='high',
            description='Unauthorized access attempt',
            user=self.regular_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('core:security_events')
        response = self.client.get(url, {'event_type': 'login_failure'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All returned events should be login_failure
        for event in response.data['events']:
            self.assertEqual(event['event_type'], 'login_failure')
