"""
Comprehensive tests for payroll management system.
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.core.models import Company
from apps.employees.models import Employee, Department
from apps.attendance.models import AttendanceRecord
from apps.leave_management.models import LeaveType, LeaveRequest, LeaveBalance
from .models import SalaryRule, PayrollRecord, EmployeeSalaryStructure
from .services import PayrollCalculationService, PayrollCalculationError

User = get_user_model()


class SalaryRuleModelTest(TestCase):
    """Test cases for SalaryRule model."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
    
    def test_create_salary_rule(self):
        """Test creating a salary rule."""
        rule = SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00")
        )
        
        self.assertEqual(rule.name, "Basic Salary")
        self.assertEqual(rule.rule_type, "basic")
        self.assertEqual(rule.amount, Decimal("5000.00"))
        self.assertTrue(rule.is_active)
    
    def test_salary_rule_string_representation(self):
        """Test string representation of salary rule."""
        rule = SalaryRule.objects.create(
            company=self.company,
            name="Housing Allowance",
            rule_type="allowance",
            calculation_method="fixed",
            amount=Decimal("1000.00")
        )
        
        self.assertEqual(str(rule), "Housing Allowance (allowance)")
    
    def test_percentage_validation(self):
        """Test that percentage rules cannot exceed 100%."""
        from django.core.exceptions import ValidationError
        
        rule = SalaryRule(
            company=self.company,
            name="Invalid Percentage",
            rule_type="allowance",
            calculation_method="percentage",
            amount=Decimal("150.00")
        )
        
        with self.assertRaises(ValidationError):
            rule.clean()


class PayrollRecordModelTest(TestCase):
    """Test cases for PayrollRecord model."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.department = Department.objects.create(
            company=self.company,
            name="Engineering"
        )
        
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
    
    def test_create_payroll_record(self):
        """Test creating a payroll record."""
        payroll = PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            gross_salary=Decimal("6000.00"),
            net_salary=Decimal("5500.00"),
            working_days=22,
            present_days=20,
            is_processed=True
        )
        
        self.assertEqual(payroll.employee, self.employee)
        self.assertEqual(payroll.net_salary, Decimal("5500.00"))
        self.assertTrue(payroll.is_processed)
    
    def test_payroll_record_period_display(self):
        """Test period display property."""
        payroll = PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            gross_salary=Decimal("5000.00"),
            net_salary=Decimal("5000.00")
        )
        
        self.assertEqual(payroll.period_display, "Jan 2024")
    
    def test_attendance_percentage_calculation(self):
        """Test attendance percentage calculation."""
        payroll = PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            gross_salary=Decimal("5000.00"),
            net_salary=Decimal("5000.00"),
            working_days=22,
            present_days=20
        )
        
        expected_percentage = (20 / 22) * 100
        self.assertAlmostEqual(payroll.attendance_percentage, expected_percentage, places=2)


class PayrollCalculationServiceTest(TestCase):
    """Test cases for PayrollCalculationService."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            working_days_per_week=5
        )
        
        self.department = Department.objects.create(
            company=self.company,
            name="Engineering"
        )
        
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        # Create salary rules
        self.basic_rule = SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00"),
            is_active=True
        )
        
        self.allowance_rule = SalaryRule.objects.create(
            company=self.company,
            name="Housing Allowance",
            rule_type="allowance",
            calculation_method="fixed",
            amount=Decimal("1000.00"),
            is_active=True
        )
        
        self.deduction_rule = SalaryRule.objects.create(
            company=self.company,
            name="Tax",
            rule_type="deduction",
            calculation_method="percentage",
            amount=Decimal("10.00"),
            is_active=True
        )
        
        self.service = PayrollCalculationService(self.company)
    
    def test_calculate_basic_salary(self):
        """Test basic salary calculation."""
        basic_salary = self.service._calculate_basic_salary(
            SalaryRule.objects.filter(company=self.company)
        )
        
        self.assertEqual(basic_salary, Decimal("5000.00"))
    
    def test_calculate_allowances(self):
        """Test allowances calculation."""
        salary_rules = SalaryRule.objects.filter(company=self.company)
        basic_salary = Decimal("5000.00")
        
        allowances = self.service._calculate_allowances(salary_rules, basic_salary)
        
        self.assertEqual(allowances, Decimal("1000.00"))
    
    def test_calculate_deductions(self):
        """Test deductions calculation."""
        salary_rules = SalaryRule.objects.filter(company=self.company)
        basic_salary = Decimal("5000.00")
        attendance_data = {
            'present_days': 20,
            'total_working_days': 22,
            'absent_days': 2
        }
        leave_data = {
            'approved_leave_days': 0,
            'unpaid_leave_days': 0
        }
        
        deductions = self.service._calculate_deductions(
            salary_rules, basic_salary, attendance_data, leave_data
        )
        
        # Tax deduction: 10% of 5000 = 500
        # Absent days deduction: (5000/22) * 2 = 454.55
        expected_deduction = Decimal("500.00") + (basic_salary / Decimal("22") * Decimal("2"))
        self.assertAlmostEqual(float(deductions), float(expected_deduction), places=2)
    
    def test_generate_payroll_record(self):
        """Test generating a complete payroll record."""
        period_start = date(2024, 1, 1)
        period_end = date(2024, 1, 31)
        
        # Create some attendance records
        for day in range(1, 21):  # 20 present days
            AttendanceRecord.objects.create(
                company=self.company,
                employee=self.employee,
                date=date(2024, 1, day),
                check_in=timezone.now(),
                check_out=timezone.now(),
                status='present'
            )
        
        payroll_record = self.service.generate_payroll_record(
            self.employee, period_start, period_end
        )
        
        self.assertIsNotNone(payroll_record)
        self.assertEqual(payroll_record.employee, self.employee)
        self.assertEqual(payroll_record.basic_salary, Decimal("5000.00"))
        self.assertTrue(payroll_record.is_processed)
    
    def test_duplicate_payroll_generation_raises_error(self):
        """Test that generating duplicate payroll raises an error."""
        period_start = date(2024, 1, 1)
        period_end = date(2024, 1, 31)
        
        # Generate first payroll
        self.service.generate_payroll_record(self.employee, period_start, period_end)
        
        # Attempt to generate duplicate
        with self.assertRaises(PayrollCalculationError):
            self.service.generate_payroll_record(self.employee, period_start, period_end)
    
    def test_bulk_generate_payroll(self):
        """Test bulk payroll generation."""
        # Create another employee
        employee2 = Employee.objects.create(
            company=self.company,
            employee_id="EMP002",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        period_start = date(2024, 1, 1)
        period_end = date(2024, 1, 31)
        
        results = self.service.bulk_generate_payroll(period_start, period_end)
        
        self.assertEqual(results['total'], 2)
        self.assertEqual(results['successful'], 2)
        self.assertEqual(results['failed'], 0)
    
    def test_payroll_summary(self):
        """Test payroll summary generation."""
        period_start = date(2024, 1, 1)
        period_end = date(2024, 1, 31)
        
        # Create a payroll record
        PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=period_start,
            period_end=period_end,
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            gross_salary=Decimal("6000.00"),
            net_salary=Decimal("5500.00")
        )
        
        summary = self.service.get_payroll_summary(period_start, period_end)
        
        self.assertEqual(summary['employee_count'], 1)
        self.assertEqual(summary['total_basic_salary'], Decimal("5000.00"))
        self.assertEqual(summary['total_net_salary'], Decimal("5500.00"))


class PayrollAPITest(APITestCase):
    """Test cases for Payroll API endpoints."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.department = Department.objects.create(
            company=self.company,
            name="Engineering"
        )
        
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            company=self.company
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create basic salary rule
        SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00"),
            is_active=True
        )
    
    def test_list_salary_rules(self):
        """Test listing salary rules."""
        url = '/api/v1/payroll/salary-rules/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_salary_rule(self):
        """Test creating a salary rule."""
        url = '/api/v1/payroll/salary-rules/'
        data = {
            'name': 'Transport Allowance',
            'rule_type': 'allowance',
            'calculation_method': 'fixed',
            'amount': '500.00',
            'is_active': True,
            'applies_to_all': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Transport Allowance')
    
    def test_list_payroll_records(self):
        """Test listing payroll records."""
        # Create a payroll record
        PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            gross_salary=Decimal("5000.00"),
            net_salary=Decimal("5000.00")
        )
        
        url = '/api/v1/payroll/records/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_payroll_by_employee(self):
        """Test filtering payroll records by employee."""
        PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            gross_salary=Decimal("5000.00"),
            net_salary=Decimal("5000.00")
        )
        
        url = f'/api/v1/payroll/records/?employee_id={self.employee.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_generate_payroll(self):
        """Test payroll generation endpoint."""
        url = '/api/v1/payroll/generate/'
        data = {
            'period_start': '2024-01-01',
            'period_end': '2024-01-31'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('results', response.data)
    
    def test_payroll_summary(self):
        """Test payroll summary endpoint."""
        # Create a payroll record
        PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            gross_salary=Decimal("6000.00"),
            net_salary=Decimal("5500.00")
        )
        
        url = '/api/v1/payroll/records/summary/?period_start=2024-01-01&period_end=2024-01-31'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_count'], 1)
        self.assertEqual(float(response.data['total_net_salary']), 5500.00)
    
    def test_payroll_reports(self):
        """Test payroll reports endpoint."""
        PayrollRecord.objects.create(
            company=self.company,
            employee=self.employee,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basic_salary=Decimal("5000.00"),
            gross_salary=Decimal("5000.00"),
            net_salary=Decimal("5000.00")
        )
        
        url = '/api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31&type=summary'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('employee_count', response.data)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access payroll endpoints."""
        self.client.force_authenticate(user=None)
        
        url = '/api/v1/payroll/records/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmployeeSalaryStructureTest(TestCase):
    """Test cases for EmployeeSalaryStructure model."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.department = Department.objects.create(
            company=self.company,
            name="Engineering"
        )
        
        self.employee = Employee.objects.create(
            company=self.company,
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        self.salary_rule = SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00")
        )
    
    def test_create_employee_salary_structure(self):
        """Test creating employee salary structure."""
        structure = EmployeeSalaryStructure.objects.create(
            company=self.company,
            employee=self.employee,
            salary_rule=self.salary_rule,
            effective_from=date(2024, 1, 1),
            is_active=True
        )
        
        self.assertEqual(structure.employee, self.employee)
        self.assertEqual(structure.salary_rule, self.salary_rule)
        self.assertTrue(structure.is_active)
    
    def test_custom_amount_override(self):
        """Test custom amount overrides default rule amount."""
        structure = EmployeeSalaryStructure.objects.create(
            company=self.company,
            employee=self.employee,
            salary_rule=self.salary_rule,
            custom_amount=Decimal("6000.00"),
            effective_from=date(2024, 1, 1),
            is_active=True
        )
        
        self.assertEqual(structure.applicable_amount, Decimal("6000.00"))
    
    def test_applicable_amount_uses_default(self):
        """Test applicable amount uses default when no custom amount."""
        structure = EmployeeSalaryStructure.objects.create(
            company=self.company,
            employee=self.employee,
            salary_rule=self.salary_rule,
            effective_from=date(2024, 1, 1),
            is_active=True
        )
        
        self.assertEqual(structure.applicable_amount, Decimal("5000.00"))
