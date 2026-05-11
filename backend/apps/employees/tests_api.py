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

    def test_search_employees(self):
        """Test searching employees by name, email, or ID."""
        Employee.objects.all().delete()
        
        Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        Employee.objects.create(
            company=self.company,
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )

        # Search by first name
        response = self.client.get('/api/v1/employees/?search=John')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['first_name'], 'John')

        # Search by email
        response = self.client.get('/api/v1/employees/?search=jane.smith')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['email'], 'jane.smith@test.com')

        # Search by employee ID
        response = self.client.get('/api/v1/employees/?search=EMP002')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['employee_id'], 'EMP002')

    def test_filter_employees_by_status(self):
        """Test filtering employees by status."""
        Employee.objects.all().delete()
        
        Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            hire_date='2024-01-01',
            status='active'
        )
        Employee.objects.create(
            company=self.company,
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            department=self.department,
            hire_date='2024-01-01',
            status='inactive'
        )

        response = self.client.get('/api/v1/employees/?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'active')

    def test_filter_employees_by_position(self):
        """Test filtering employees by position."""
        Employee.objects.all().delete()
        
        Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            position='Software Engineer',
            hire_date='2024-01-01'
        )
        Employee.objects.create(
            company=self.company,
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            department=self.department,
            position='Project Manager',
            hire_date='2024-01-01'
        )

        response = self.client.get('/api/v1/employees/?position=Engineer')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertIn('Engineer', results[0]['position'])

    def test_export_employees(self):
        """Test exporting employees to CSV."""
        Employee.objects.all().delete()
        
        Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )

        response = self.client.get('/api/v1/employees/export_employees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Employee ID', content)
        self.assertIn('EMP001', content)
        self.assertIn('John', content)

    def test_import_employees_success(self):
        """Test importing employees from CSV successfully."""
        import io
        
        csv_content = """employee_id,first_name,last_name,email,department_name,position,hire_date,status
EMP003,Alice,Johnson,alice@test.com,IT,Developer,2024-01-15,active
EMP004,Bob,Williams,bob@test.com,IT,Designer,2024-01-20,active"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'employees.csv'
        
        response = self.client.post('/api/v1/employees/import_employees/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_count'], 2)
        self.assertEqual(len(response.data['errors']), 0)
        
        # Verify employees were created
        self.assertTrue(Employee.objects.filter(employee_id='EMP003').exists())
        self.assertTrue(Employee.objects.filter(employee_id='EMP004').exists())

    def test_import_employees_with_errors(self):
        """Test importing employees with validation errors."""
        import io
        
        csv_content = """employee_id,first_name,last_name,email,department_name,position,hire_date,status
EMP005,Charlie,Brown,charlie@test.com,NonExistentDept,Manager,2024-01-15,active"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'employees.csv'
        
        response = self.client.post('/api/v1/employees/import_employees/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['created_count'], 0)
        self.assertGreater(len(response.data['errors']), 0)
        self.assertIn('not found', response.data['errors'][0])

    def test_import_employees_duplicate_id(self):
        """Test importing employees with duplicate employee IDs."""
        import io
        
        # Create existing employee
        Employee.objects.create(
            company=self.company,
            employee_id='EMP006',
            first_name='Existing',
            last_name='Employee',
            email='existing@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        
        csv_content = """employee_id,first_name,last_name,email,department_name,position,hire_date,status
EMP006,Duplicate,User,duplicate@test.com,IT,Developer,2024-01-15,active"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'employees.csv'
        
        response = self.client.post('/api/v1/employees/import_employees/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['created_count'], 0)
        self.assertGreater(len(response.data['errors']), 0)
        self.assertIn('already exists', response.data['errors'][0])

    def test_validate_unique_employee_id(self):
        """Test that employee_id must be unique within company."""
        Employee.objects.create(
            company=self.company,
            employee_id='EMP007',
            first_name='First',
            last_name='Employee',
            email='first@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        
        data = {
            'employee_id': 'EMP007',
            'first_name': 'Second',
            'last_name': 'Employee',
            'email': 'second@test.com',
            'department': str(self.department.id),
            'hire_date': '2024-01-01',
            'status': 'active'
        }
        response = self.client.post('/api/v1/employees/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee_id', response.data)

    def test_validate_unique_email(self):
        """Test that email must be unique within company."""
        Employee.objects.create(
            company=self.company,
            employee_id='EMP008',
            first_name='First',
            last_name='Employee',
            email='duplicate@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        
        data = {
            'employee_id': 'EMP009',
            'first_name': 'Second',
            'last_name': 'Employee',
            'email': 'duplicate@test.com',
            'department': str(self.department.id),
            'hire_date': '2024-01-01',
            'status': 'active'
        }
        response = self.client.post('/api/v1/employees/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_update_employee_with_all_fields(self):
        """Test updating employee with all optional fields."""
        employee = Employee.objects.create(
            company=self.company,
            employee_id='EMP010',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            hire_date='2024-01-01'
        )
        
        data = {
            'employee_id': 'EMP010',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'phone': '+1234567890',
            'department': str(self.department.id),
            'branch': str(self.branch.id),
            'position': 'Senior Developer',
            'hire_date': '2024-01-01',
            'status': 'active',
            'date_of_birth': '1990-05-15',
            'address': '123 Main St, City, State',
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '+0987654321'
        }
        response = self.client.put(f'/api/v1/employees/{employee.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        employee.refresh_from_db()
        self.assertEqual(employee.phone, '+1234567890')
        self.assertEqual(employee.position, 'Senior Developer')
        self.assertEqual(employee.emergency_contact_name, 'Jane Doe')

