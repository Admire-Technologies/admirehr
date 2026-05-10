"""
Tests for multi-tenant functionality in the core app.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import transaction
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from .models import Company, TenantAwareModel
from .middleware import TenantMiddleware, get_current_company, set_current_company, clear_current_company
from apps.authentication.models import Role
from apps.employees.models import Employee, Department

User = get_user_model()


class CompanyModelTest(TestCase):
    """Test cases for Company model."""
    
    def setUp(self):
        self.company_data = {
            'name': 'Test Company',
            'code': 'TEST001',
            'email': 'test@company.com',
            'phone': '+1234567890',
            'address': '123 Test Street',
            'website': 'https://testcompany.com',
            'timezone': 'UTC',
            'currency': 'USD',
            'working_hours_per_day': 8.0,
            'working_days_per_week': 5,
            'annual_leave_days': 21,
            'sick_leave_days': 10,
            'grace_period_minutes': 15,
            'overtime_threshold_hours': 8.0,
            'max_employees': 100,
        }
    
    def test_company_creation(self):
        """Test company creation with all fields."""
        company = Company.objects.create(**self.company_data)
        
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.code, 'TEST001')
        self.assertEqual(company.email, 'test@company.com')
        self.assertTrue(company.is_active)
        self.assertEqual(company.subscription_plan, 'basic')
        self.assertEqual(company.max_employees, 100)
    
    def test_company_str_representation(self):
        """Test company string representation."""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(str(company), 'Test Company')
    
    def test_company_settings_methods(self):
        """Test company settings get/set methods."""
        company = Company.objects.create(**self.company_data)
        
        # Test setting a custom setting
        company.set_setting('custom_setting', 'custom_value')
        company.save()
        
        # Test getting the custom setting
        self.assertEqual(company.get_setting('custom_setting'), 'custom_value')
        self.assertEqual(company.get_setting('non_existent', 'default'), 'default')
    
    def test_employee_count_property(self):
        """Test employee count property."""
        company = Company.objects.create(**self.company_data)
        
        # Create a role for the company
        role = Role.objects.create(name='Employee', company=company)
        
        # Create a department
        department = Department.objects.create(name='IT', company=company)
        
        # Initially should be 0
        self.assertEqual(company.employee_count, 0)
        
        # Create an employee
        Employee.objects.create(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            department=department,
            hire_date='2024-01-01',
            company=company,
            status='active'
        )
        
        # Should be 1 now
        self.assertEqual(company.employee_count, 1)
    
    def test_can_add_employee(self):
        """Test can_add_employee method."""
        company = Company.objects.create(**self.company_data)
        company.max_employees = 1
        company.save()
        
        # Should be able to add initially
        self.assertTrue(company.can_add_employee())
        
        # Create a role and department
        role = Role.objects.create(name='Employee', company=company)
        department = Department.objects.create(name='IT', company=company)
        
        # Add an employee
        Employee.objects.create(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            department=department,
            hire_date='2024-01-01',
            company=company,
            status='active'
        )
        
        # Should not be able to add more
        self.assertFalse(company.can_add_employee())


class TenantMiddlewareTest(TestCase):
    """Test cases for TenantMiddleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda request: None)
        
        # Create test companies
        self.company1 = Company.objects.create(
            name='Company 1',
            code='COMP1',
            email='company1@test.com'
        )
        self.company2 = Company.objects.create(
            name='Company 2',
            code='COMP2',
            email='company2@test.com'
        )
        
        # Create roles
        self.role1 = Role.objects.create(name='Admin', company=self.company1)
        self.role2 = Role.objects.create(name='Admin', company=self.company2)
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@company1.com',
            password='testpass123',
            company=self.company1,
            role=self.role1
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@company2.com',
            password='testpass123',
            company=self.company2,
            role=self.role2
        )    

    def test_middleware_sets_company_for_authenticated_user(self):
        """Test that middleware sets company for authenticated user."""
        request = self.factory.get('/api/v1/test/')
        request.user = self.user1
        
        # Process request
        response = self.middleware.process_request(request)
        
        # Should not return error response
        self.assertIsNone(response)
        
        # Should set company in request
        self.assertEqual(request.company, self.company1)
        
        # Should set company in thread local
        self.assertEqual(get_current_company(), self.company1)
    
    def test_middleware_skips_auth_paths(self):
        """Test that middleware skips authentication paths."""
        skip_paths = [
            '/admin/',
            '/api/schema/',
            '/api/docs/',
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
            '/api/v1/companies/register/',
        ]
        
        for path in skip_paths:
            request = self.factory.get(path)
            request.user = self.user1
            
            response = self.middleware.process_request(request)
            
            # Should not set company for skip paths
            self.assertIsNone(response)
            self.assertIsNone(get_current_company())
    
    def test_middleware_handles_user_without_company(self):
        """Test middleware handles user without company."""
        # Create a mock user object that simulates a user without company
        from unittest.mock import Mock
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.company = None  # Simulate user without company
        
        request = self.factory.get('/api/v1/test/')
        request.user = mock_user
        
        response = self.middleware.process_request(request)
        
        # Should return error response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)
    
    def test_middleware_clears_company_on_response(self):
        """Test that middleware clears company on response."""
        request = self.factory.get('/api/v1/test/')
        request.user = self.user1
        
        # Set company manually
        set_current_company(self.company1)
        
        # Process response
        response = self.middleware.process_response(request, None)
        
        # Should clear company
        self.assertIsNone(get_current_company())


class TenantAwareManagerTest(TestCase):
    """Test cases for TenantAwareManager."""
    
    def setUp(self):
        # Create test companies
        self.company1 = Company.objects.create(
            name='Company 1',
            code='COMP1',
            email='company1@test.com'
        )
        self.company2 = Company.objects.create(
            name='Company 2',
            code='COMP2',
            email='company2@test.com'
        )
        
        # Create departments for each company
        self.dept1 = Department.objects.create(
            name='IT',
            company=self.company1
        )
        self.dept2 = Department.objects.create(
            name='HR',
            company=self.company2
        )
    
    def test_tenant_aware_filtering(self):
        """Test that tenant-aware manager filters by current company."""
        # Set current company
        set_current_company(self.company1)
        
        # Query should only return company1 departments
        departments = Department.tenant_objects.all()
        self.assertEqual(departments.count(), 1)
        self.assertEqual(departments.first(), self.dept1)
        
        # Switch to company2
        set_current_company(self.company2)
        
        # Query should only return company2 departments
        departments = Department.tenant_objects.all()
        self.assertEqual(departments.count(), 1)
        self.assertEqual(departments.first(), self.dept2)
        
        # Clear company
        clear_current_company()
    
    def test_all_companies_method(self):
        """Test that all_companies method bypasses tenant filtering."""
        set_current_company(self.company1)
        
        # Should return all departments regardless of current company
        all_departments = Department.tenant_objects.all_companies()
        self.assertEqual(all_departments.count(), 2)
        
        clear_current_company()


class CompanyAPITest(APITestCase):
    """Test cases for Company API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test company
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )
        
        # Create admin role
        self.admin_role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='testpass123',
            company=self.company,
            role=self.admin_role,
            is_company_admin=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@company.com',
            password='testpass123',
            company=self.company,
            role=self.admin_role
        )
    
    def test_company_registration(self):
        """Test company registration endpoint."""
        data = {
            'name': 'New Company',
            'code': 'NEW001',
            'email': 'new@company.com',
            'admin_username': 'newadmin',
            'admin_email': 'newadmin@company.com',
            'admin_password': 'newpass123',
            'admin_first_name': 'New',
            'admin_last_name': 'Admin'
        }
        
        response = self.client.post('/api/v1/companies/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('company', response.data)
        
        # Verify company was created
        company = Company.objects.get(code='NEW001')
        self.assertEqual(company.name, 'New Company')
        
        # Verify admin user was created
        admin_user = User.objects.get(username='newadmin')
        self.assertEqual(admin_user.company, company)
        self.assertTrue(admin_user.is_company_admin)
    
    def test_get_company_details(self):
        """Test getting current company details."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/v1/companies/current/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Company')
        self.assertEqual(response.data['code'], 'TEST001')
    
    def test_update_company_details_as_admin(self):
        """Test updating company details as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'name': 'Updated Company Name',
            'phone': '+1234567890'
        }
        
        response = self.client.patch('/api/v1/companies/current/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Company Name')
        self.assertEqual(response.data['phone'], '+1234567890')
    
    def test_update_company_details_as_regular_user(self):
        """Test that regular users cannot update company details."""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'name': 'Updated Company Name'
        }
        
        response = self.client.patch('/api/v1/companies/current/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_company_settings_management(self):
        """Test company settings management."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Update settings
        data = {
            'working_hours_per_day': 7.5,
            'annual_leave_days': 25,
            'settings': {
                'custom_setting': 'custom_value'
            }
        }
        
        response = self.client.patch('/api/v1/companies/settings/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['working_hours_per_day']), 7.5)
        self.assertEqual(response.data['annual_leave_days'], 25)


class DataIsolationTest(TestCase):
    """Test cases for multi-tenant data isolation."""
    
    def setUp(self):
        # Create two companies
        self.company1 = Company.objects.create(
            name='Company 1',
            code='COMP1',
            email='company1@test.com'
        )
        self.company2 = Company.objects.create(
            name='Company 2',
            code='COMP2',
            email='company2@test.com'
        )
        
        # Create departments for each company
        self.dept1_comp1 = Department.objects.create(
            name='IT',
            company=self.company1
        )
        self.dept2_comp1 = Department.objects.create(
            name='HR',
            company=self.company1
        )
        self.dept1_comp2 = Department.objects.create(
            name='IT',
            company=self.company2
        )
        
        # Create employees for each company
        self.emp1_comp1 = Employee.objects.create(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@company1.com',
            department=self.dept1_comp1,
            hire_date='2024-01-01',
            company=self.company1
        )
        self.emp1_comp2 = Employee.objects.create(
            employee_id='EMP001',  # Same ID but different company
            first_name='Jane',
            last_name='Smith',
            email='jane@company2.com',
            department=self.dept1_comp2,
            hire_date='2024-01-01',
            company=self.company2
        )
    
    def test_department_isolation(self):
        """Test that departments are isolated by company."""
        # Set company 1 as current
        set_current_company(self.company1)
        
        departments = Department.tenant_objects.all()
        self.assertEqual(departments.count(), 2)
        self.assertIn(self.dept1_comp1, departments)
        self.assertIn(self.dept2_comp1, departments)
        self.assertNotIn(self.dept1_comp2, departments)
        
        # Switch to company 2
        set_current_company(self.company2)
        
        departments = Department.tenant_objects.all()
        self.assertEqual(departments.count(), 1)
        self.assertIn(self.dept1_comp2, departments)
        self.assertNotIn(self.dept1_comp1, departments)
        self.assertNotIn(self.dept2_comp1, departments)
        
        clear_current_company()
    
    def test_employee_isolation(self):
        """Test that employees are isolated by company."""
        # Set company 1 as current
        set_current_company(self.company1)
        
        employees = Employee.tenant_objects.all()
        self.assertEqual(employees.count(), 1)
        self.assertEqual(employees.first(), self.emp1_comp1)
        
        # Switch to company 2
        set_current_company(self.company2)
        
        employees = Employee.tenant_objects.all()
        self.assertEqual(employees.count(), 1)
        self.assertEqual(employees.first(), self.emp1_comp2)
        
        clear_current_company()
    
    def test_automatic_company_assignment(self):
        """Test that models automatically get assigned to current company."""
        set_current_company(self.company1)
        
        # Create department without explicitly setting company
        dept = Department.objects.create(name='Finance')
        
        # Should automatically be assigned to company1
        self.assertEqual(dept.company, self.company1)
        
        clear_current_company()
    
    def test_cross_company_data_access_prevention(self):
        """Test that cross-company data access is prevented."""
        set_current_company(self.company1)
        
        # Try to access company2's department by ID
        with self.assertRaises(Department.DoesNotExist):
            Department.tenant_objects.get(id=self.dept1_comp2.id)
        
        # But should be able to access company1's department
        dept = Department.tenant_objects.get(id=self.dept1_comp1.id)
        self.assertEqual(dept, self.dept1_comp1)
        
        clear_current_company()