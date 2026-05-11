"""
Tests for employee management.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Company
from apps.authentication.models import Role
from .models import Department, Branch, Employee

User = get_user_model()


class BranchModelTest(TestCase):
    """Test Branch model."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )

    def test_create_branch(self):
        """Test creating a branch."""
        branch = Branch.objects.create(
            company=self.company,
            name='Main Office',
            code='MAIN',
            city='New York',
            country='USA'
        )
        self.assertEqual(branch.name, 'Main Office')
        self.assertEqual(branch.code, 'MAIN')
        self.assertTrue(branch.is_active)

    def test_branch_hierarchy(self):
        """Test branch parent-child relationship."""
        parent_branch = Branch.objects.create(
            company=self.company,
            name='Head Office',
            code='HEAD'
        )
        child_branch = Branch.objects.create(
            company=self.company,
            name='Regional Office',
            code='REG',
            parent=parent_branch
        )
        self.assertEqual(child_branch.parent, parent_branch)
        self.assertIn(child_branch, parent_branch.sub_branches.all())

    def test_branch_full_address(self):
        """Test branch full address property."""
        branch = Branch.objects.create(
            company=self.company,
            name='Test Branch',
            code='TEST',
            address='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA'
        )
        full_address = branch.full_address
        self.assertIn('123 Main St', full_address)
        self.assertIn('New York', full_address)
        self.assertIn('USA', full_address)

    def test_branch_employee_count(self):
        """Test branch employee count property."""
        branch = Branch.objects.create(
            company=self.company,
            name='Test Branch',
            code='TEST'
        )
        department = Department.objects.create(
            company=self.company,
            name='IT'
        )
        
        # Create employees
        for i in range(3):
            Employee.objects.create(
                company=self.company,
                employee_id=f'EMP{i:03d}',
                first_name=f'Employee{i}',
                last_name='Test',
                email=f'emp{i}@test.com',
                department=department,
                branch=branch,
                hire_date='2024-01-01',
                status='active'
            )
        
        self.assertEqual(branch.employee_count, 3)


class DepartmentModelTest(TestCase):
    """Test Department model."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            email='test@company.com'
        )

    def test_create_department(self):
        """Test creating a department."""
        department = Department.objects.create(
            company=self.company,
            name='Engineering',
            description='Engineering department'
        )
        self.assertEqual(department.name, 'Engineering')
        self.assertTrue(department.is_active)

    def test_department_hierarchy(self):
        """Test department parent-child relationship."""
        parent_dept = Department.objects.create(
            company=self.company,
            name='Engineering'
        )
        child_dept = Department.objects.create(
            company=self.company,
            name='Backend Team',
            parent=parent_dept
        )
        self.assertEqual(child_dept.parent, parent_dept)


class EmployeeModelTest(TestCase):
    """Test Employee model."""

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
        self.branch = Branch.objects.create(
            company=self.company,
            name='Main Office',
            code='MAIN'
        )

    def test_create_employee(self):
        """Test creating an employee."""
        employee = Employee.objects.create(
            company=self.company,
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            department=self.department,
            branch=self.branch,
            hire_date='2024-01-01'
        )
        self.assertEqual(employee.employee_id, 'EMP001')
        self.assertEqual(employee.full_name, 'John Doe')
        self.assertEqual(employee.status, 'active')

    def test_employee_with_branch(self):
        """Test employee with branch assignment."""
        employee = Employee.objects.create(
            company=self.company,
            employee_id='EMP002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@test.com',
            department=self.department,
            branch=self.branch,
            hire_date='2024-01-01'
        )
        self.assertEqual(employee.branch, self.branch)
