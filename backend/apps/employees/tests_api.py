"""
API tests for employee management.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.models import Company
from apps.authentication.models import Role
from .models import Department, Branch, Employee

User = get_user_model()


class BranchAPITest(TestCase):
    """Test Branch API endpoints."""

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

    def test_list_branches(self):
        """Test listing branches."""
        # Clear any existing branches
        Branch.objects.all().delete()
        
        Branch.objects.create(
            company=self.company,
            name='Main Office',
            code='MAIN'
        )
        Branch.objects.create(
            company=self.company,
            name='Branch Office',
            code='BRANCH'
        )

        response = self.client.get('/api/v1/branches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_create_branch(self):
        """Test creating a branch."""
        data = {
            'name': 'New Branch',
            'code': 'NEW',
            'city': 'New York',
            'country': 'USA',
            'is_active': True
        }
        response = self.client.post('/api/v1/branches/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Branch.objects.count(), 1)
        branch = Branch.objects.first()
        self.assertEqual(branch.name, 'New Branch')
        self.assertEqual(branch.company, self.company)

    def test_update_branch(self):
        """Test updating a branch."""
        branch = Branch.objects.create(
            company=self.company,
            name='Old Name',
            code='OLD'
        )
        data = {
            'name': 'Updated Name',
            'code': 'UPD',
            'is_active': True
        }
        response = self.client.put(f'/api/v1/branches/{branch.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        branch.refresh_from_db()
        self.assertEqual(branch.name, 'Updated Name')

    def test_delete_branch(self):
        """Test deleting a branch."""
        branch = Branch.objects.create(
            company=self.company,
            name='Test Branch',
            code='TEST'
        )
        response = self.client.delete(f'/api/v1/branches/{branch.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Branch.objects.count(), 0)

    def test_branch_hierarchy(self):
        """Test branch hierarchy endpoint."""
        parent = Branch.objects.create(
            company=self.company,
            name='Head Office',
            code='HEAD'
        )
        Branch.objects.create(
            company=self.company,
            name='Regional Office',
            code='REG',
            parent=parent
        )

        response = self.client.get('/api/v1/branches/hierarchy/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]['children']), 1)


class DepartmentAPITest(TestCase):
    """Test Department API endpoints."""

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

    def test_list_departments(self):
        """Test listing departments."""
        # Clear any existing departments
        Department.objects.all().delete()
        
        Department.objects.create(
            company=self.company,
            name='Engineering'
        )
        Department.objects.create(
            company=self.company,
            name='Sales'
        )

        response = self.client.get('/api/v1/departments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_create_department(self):
        """Test creating a department."""
        data = {
            'name': 'Marketing',
            'description': 'Marketing department',
            'is_active': True
        }
        response = self.client.post('/api/v1/departments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Department.objects.count(), 1)
        dept = Department.objects.first()
        self.assertEqual(dept.name, 'Marketing')
        self.assertEqual(dept.company, self.company)

    def test_delete_department_with_employees(self):
        """Test that department with employees cannot be deleted."""
        department = Department.objects.create(
            company=self.company,
            name='IT'
        )
        Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=department,
            hire_date='2024-01-01',
            status='active'
        )

        response = self.client.delete(f'/api/v1/departments/{department.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot delete department', response.data['error'])

    def test_department_hierarchy(self):
        """Test department hierarchy endpoint."""
        parent = Department.objects.create(
            company=self.company,
            name='Engineering'
        )
        Department.objects.create(
            company=self.company,
            name='Backend Team',
            parent=parent
        )

        response = self.client.get('/api/v1/departments/hierarchy/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]['children']), 1)


class EmployeeAPITest(TestCase):
    """Test Employee API endpoints."""

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
        self.department = Department.objects.create(
            company=self.company,
            name='IT'
        )
        self.branch = Branch.objects.create(
            company=self.company,
            name='Main Office',
            code='MAIN'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_employee_with_branch(self):
        """Test creating an employee with branch assignment."""
        data = {
            'employee_id': 'EMP001',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'department': str(self.department.id),
            'branch': str(self.branch.id),
            'hire_date': '2024-01-01',
            'status': 'active'
        }
        response = self.client.post('/api/v1/employees/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        employee = Employee.objects.first()
        self.assertEqual(employee.branch, self.branch)

    def test_filter_employees_by_branch(self):
        """Test filtering employees by branch."""
        # Clear any existing employees
        Employee.objects.all().delete()
        
        branch2 = Branch.objects.create(
            company=self.company,
            name='Branch 2',
            code='BR2'
        )
        
        Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            branch=self.branch,
            hire_date='2024-01-01'
        )
        Employee.objects.create(
            company=self.company,
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            department=self.department,
            branch=branch2,
            hire_date='2024-01-01'
        )

        response = self.client.get(f'/api/v1/employees/?branch={self.branch.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['employee_id'], 'EMP001')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['employee_id'], 'EMP001')
