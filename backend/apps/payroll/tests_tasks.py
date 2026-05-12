"""
Tests for payroll Celery tasks.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from apps.core.models import Company
from apps.authentication.models import User, Role, Permission
from apps.employees.models import Employee, Department
from apps.payroll.models import PayrollRecord, SalaryRule, EmployeeSalaryStructure
from apps.payroll.tasks import (
    generate_payroll_for_employee,
    bulk_generate_payroll,
    send_payslip_notification,
    monthly_payroll_generation,
    generate_payroll_report
)


class PayrollTaskTestCase(TestCase):
    """Base test case for payroll tasks."""
    
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
        
        # Create employees
        self.employee1 = Employee.objects.create(
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            company=self.company,
            department=self.department,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        self.employee2 = Employee.objects.create(
            employee_id="EMP002",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            company=self.company,
            department=self.department,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        # Create users
        self.user1 = User.objects.create_user(
            username="john.doe",
            email="john.doe@test.com",
            password="testpass123",
            company=self.company,
            role=self.role,
            employee=self.employee1
        )
        
        self.user2 = User.objects.create_user(
            username="jane.smith",
            email="jane.smith@test.com",
            password="testpass123",
            company=self.company,
            role=self.role,
            employee=self.employee2
        )
        
        # Create salary rules
        self.basic_salary_rule = SalaryRule.objects.create(
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00"),
            company=self.company
        )
        
        self.allowance_rule = SalaryRule.objects.create(
            name="Housing Allowance",
            rule_type="allowance",
            calculation_method="fixed",
            amount=Decimal("1000.00"),
            company=self.company
        )


@pytest.mark.django_db
class TestGeneratePayrollForEmployee(PayrollTaskTestCase):
    """Tests for generate_payroll_for_employee task."""
    
    @patch('apps.payroll.tasks.PayrollCalculationService')
    @patch('apps.payroll.tasks.send_payslip_notification')
    def test_generate_payroll_success(self, mock_notification, mock_service):
        """Test successful payroll generation for single employee."""
        # Mock payroll service
        mock_payroll = MagicMock()
        mock_payroll.id = 'payroll-123'
        mock_payroll.net_salary = Decimal("5500.00")
        mock_service.return_value.generate_payroll_record.return_value = mock_payroll
        
        period_start = '2024-01-01'
        period_end = '2024-01-31'
        
        result = generate_payroll_for_employee.apply(kwargs={
            'employee_id': str(self.employee1.id),
            'period_start': period_start,
            'period_end': period_end,
            'company_id': str(self.company.id)
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        assert result.result['employee_id'] == str(self.employee1.id)
        mock_notification.delay.assert_called_once()
    
    def test_generate_payroll_employee_not_found(self):
        """Test payroll generation with non-existent employee."""
        result = generate_payroll_for_employee.apply(kwargs={
            'employee_id': '00000000-0000-0000-0000-000000000000',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'company_id': str(self.company.id)
        })
        
        assert result.successful()
        assert result.result['status'] == 'error'
        assert 'not found' in result.result['error']


@pytest.mark.django_db
class TestBulkGeneratePayroll(PayrollTaskTestCase):
    """Tests for bulk_generate_payroll task."""
    
    @patch('apps.payroll.tasks.generate_payroll_for_employee')
    @patch('apps.payroll.tasks.send_payroll_summary_email')
    def test_bulk_generate_payroll_all_employees(self, mock_summary, mock_generate):
        """Test bulk payroll generation for all employees."""
        # Mock individual payroll generation
        mock_result = MagicMock()
        mock_result.get.return_value = {'status': 'success'}
        mock_generate.s.return_value.apply_async.return_value.get.return_value = [
            {'status': 'success'},
            {'status': 'success'}
        ]
        
        result = bulk_generate_payroll.apply(kwargs={
            'company_id': str(self.company.id),
            'period_start': '2024-01-01',
            'period_end': '2024-01-31'
        })
        
        # Note: This test may need adjustment based on actual implementation
        # as group tasks behave differently in tests
        assert result.successful()
    
    @patch('apps.payroll.tasks.generate_payroll_for_employee')
    def test_bulk_generate_payroll_specific_employees(self, mock_generate):
        """Test bulk payroll generation for specific employees."""
        employee_ids = [str(self.employee1.id)]
        
        result = bulk_generate_payroll.apply(kwargs={
            'company_id': str(self.company.id),
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'employee_ids': employee_ids
        })
        
        assert result.successful()


@pytest.mark.django_db
class TestSendPayslipNotification(PayrollTaskTestCase):
    """Tests for send_payslip_notification task."""
    
    @patch('apps.payroll.tasks.send_email_task')
    def test_send_payslip_notification_success(self, mock_email):
        """Test successful payslip notification sending."""
        # Create payroll record
        payroll = PayrollRecord.objects.create(
            employee=self.employee1,
            period_start=datetime(2024, 1, 1).date(),
            period_end=datetime(2024, 1, 31).date(),
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            gross_salary=Decimal("6000.00"),
            net_salary=Decimal("5500.00"),
            company=self.company
        )
        
        result = send_payslip_notification.apply(kwargs={
            'payroll_id': str(payroll.id)
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        assert result.result['payroll_id'] == str(payroll.id)
        mock_email.delay.assert_called_once()
    
    def test_send_payslip_notification_no_email(self):
        """Test payslip notification when employee has no email."""
        # Create employee without user
        employee_no_email = Employee.objects.create(
            employee_id="EMP003",
            first_name="No",
            last_name="Email",
            email="",
            company=self.company,
            department=self.department,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        payroll = PayrollRecord.objects.create(
            employee=employee_no_email,
            period_start=datetime(2024, 1, 1).date(),
            period_end=datetime(2024, 1, 31).date(),
            basic_salary=Decimal("5000.00"),
            net_salary=Decimal("5000.00"),
            gross_salary=Decimal("5000.00"),
            company=self.company
        )
        
        result = send_payslip_notification.apply(kwargs={
            'payroll_id': str(payroll.id)
        })
        
        assert result.successful()
        assert result.result['status'] == 'skipped'


@pytest.mark.django_db
class TestMonthlyPayrollGeneration(PayrollTaskTestCase):
    """Tests for monthly_payroll_generation scheduled task."""
    
    @patch('apps.payroll.tasks.bulk_generate_payroll')
    def test_monthly_payroll_generation_all_companies(self, mock_bulk):
        """Test monthly payroll generation for all companies."""
        mock_bulk.delay.return_value.id = 'task-123'
        
        result = monthly_payroll_generation.apply()
        
        assert result.successful()
        assert result.result['status'] == 'success'
        assert result.result['companies_processed'] == 1
        mock_bulk.delay.assert_called_once()
    
    @patch('apps.payroll.tasks.bulk_generate_payroll')
    def test_monthly_payroll_generation_specific_company(self, mock_bulk):
        """Test monthly payroll generation for specific company."""
        mock_bulk.delay.return_value.id = 'task-123'
        
        result = monthly_payroll_generation.apply(kwargs={
            'company_id': str(self.company.id)
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        mock_bulk.delay.assert_called_once()


@pytest.mark.django_db
class TestGeneratePayrollReport(PayrollTaskTestCase):
    """Tests for generate_payroll_report task."""
    
    def setUp(self):
        """Set up test data with payroll records."""
        super().setUp()
        
        # Create payroll records
        self.payroll1 = PayrollRecord.objects.create(
            employee=self.employee1,
            period_start=datetime(2024, 1, 1).date(),
            period_end=datetime(2024, 1, 31).date(),
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            gross_salary=Decimal("6000.00"),
            net_salary=Decimal("5500.00"),
            company=self.company
        )
        
        self.payroll2 = PayrollRecord.objects.create(
            employee=self.employee2,
            period_start=datetime(2024, 1, 1).date(),
            period_end=datetime(2024, 1, 31).date(),
            basic_salary=Decimal("6000.00"),
            allowances=Decimal("1200.00"),
            deductions=Decimal("600.00"),
            gross_salary=Decimal("7200.00"),
            net_salary=Decimal("6600.00"),
            company=self.company
        )
    
    def test_generate_summary_report(self):
        """Test generating summary payroll report."""
        result = generate_payroll_report.apply(kwargs={
            'company_id': str(self.company.id),
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'report_type': 'summary'
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        report_data = result.result['report_data']
        assert report_data['report_type'] == 'summary'
        assert report_data['summary']['total_employees'] == 2
    
    def test_generate_department_report(self):
        """Test generating department-wise payroll report."""
        result = generate_payroll_report.apply(kwargs={
            'company_id': str(self.company.id),
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'report_type': 'department'
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        report_data = result.result['report_data']
        assert report_data['report_type'] == 'department'
        assert len(report_data['departments']) > 0
    
    def test_generate_detailed_report(self):
        """Test generating detailed payroll report."""
        result = generate_payroll_report.apply(kwargs={
            'company_id': str(self.company.id),
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'report_type': 'detailed'
        })
        
        assert result.successful()
        assert result.result['status'] == 'success'
        report_data = result.result['report_data']
        assert report_data['report_type'] == 'detailed'
        assert len(report_data['records']) == 2


@pytest.mark.django_db
class TestPayrollTaskIntegration(PayrollTaskTestCase):
    """Integration tests for payroll tasks."""
    
    @patch('apps.payroll.tasks.send_email_task')
    def test_complete_payroll_workflow(self, mock_email):
        """Test complete payroll generation workflow."""
        # This would test the full workflow from generation to notification
        # In a real scenario, you'd want to test with actual PayrollCalculationService
        pass
