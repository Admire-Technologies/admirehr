"""
Integration tests for payroll management system.
Tests the complete workflow from salary rule creation to payslip generation.
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
from .models import SalaryRule, PayrollRecord
from .services import PayrollCalculationService

User = get_user_model()


class PayrollWorkflowIntegrationTest(APITestCase):
    """
    Integration test for complete payroll workflow.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            working_days_per_week=5,
            working_hours_per_day=8
        )
        
        # Create department
        self.department = Department.objects.create(
            company=self.company,
            name="Engineering"
        )
        
        # Create employees
        self.employee1 = Employee.objects.create(
            company=self.company,
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        self.employee2 = Employee.objects.create(
            company=self.company,
            employee_id="EMP002",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            department=self.department,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            company=self.company
        )
        
        # Authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create leave type
        self.leave_type = LeaveType.objects.create(
            company=self.company,
            name="Annual Leave",
            days_allowed=21,
            is_active=True
        )
    
    def test_complete_payroll_workflow(self):
        """
        Test the complete payroll workflow:
        1. Create salary rules
        2. Create attendance records
        3. Create leave requests
        4. Generate payroll
        5. Retrieve payslip
        6. Generate reports
        """
        
        # Step 1: Create salary rules
        basic_rule_data = {
            'name': 'Basic Salary',
            'rule_type': 'basic',
            'calculation_method': 'fixed',
            'amount': '5000.00',
            'is_active': True,
            'applies_to_all': True
        }
        response = self.client.post('/api/v1/payroll/salary-rules/', basic_rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        allowance_data = {
            'name': 'Housing Allowance',
            'rule_type': 'allowance',
            'calculation_method': 'fixed',
            'amount': '1000.00',
            'is_active': True,
            'applies_to_all': True
        }
        response = self.client.post('/api/v1/payroll/salary-rules/', allowance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        deduction_data = {
            'name': 'Tax',
            'rule_type': 'deduction',
            'calculation_method': 'percentage',
            'amount': '10.00',
            'is_active': True,
            'applies_to_all': True
        }
        response = self.client.post('/api/v1/payroll/salary-rules/', deduction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Create attendance records for January 2024
        period_start = date(2024, 1, 1)
        period_end = date(2024, 1, 31)
        
        # Employee 1: 20 present days
        for day in range(1, 21):
            AttendanceRecord.objects.create(
                company=self.company,
                employee=self.employee1,
                date=date(2024, 1, day),
                check_in=timezone.now(),
                check_out=timezone.now(),
                status='present',
                working_hours=8
            )
        
        # Employee 2: 18 present days
        for day in range(1, 19):
            AttendanceRecord.objects.create(
                company=self.company,
                employee=self.employee2,
                date=date(2024, 1, day),
                check_in=timezone.now(),
                check_out=timezone.now(),
                status='present',
                working_hours=8
            )
        
        # Step 3: Create leave request for employee 2
        LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee2,
            leave_type=self.leave_type,
            year=2024,
            accrued_days=21
        )
        
        leave_request = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee2,
            leave_type=self.leave_type,
            start_date=date(2024, 1, 22),
            end_date=date(2024, 1, 23),
            days_requested=2,
            reason="Personal",
            status='approved',
            approver=self.employee1,
            approved_at=timezone.now()
        )
        
        # Step 4: Generate payroll
        payroll_data = {
            'period_start': '2024-01-01',
            'period_end': '2024-01-31'
        }
        response = self.client.post('/api/v1/payroll/generate/', payroll_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['results']['successful'], 2)
        self.assertEqual(response.data['results']['failed'], 0)
        
        # Step 5: Retrieve payroll records
        response = self.client.get('/api/v1/payroll/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify employee 1 payroll
        emp1_payroll = [r for r in response.data['results'] if r['employee_id'] == 'EMP001'][0]
        self.assertEqual(float(emp1_payroll['basic_salary']), 5000.00)
        self.assertEqual(float(emp1_payroll['allowances']), 1000.00)
        self.assertEqual(float(emp1_payroll['gross_salary']), 6000.00)
        
        # Step 6: Get payslip for employee 1
        payroll_id = emp1_payroll['id']
        response = self.client.get(f'/api/v1/payroll/records/{payroll_id}/payslip/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('employee_details', response.data)
        
        # Step 7: Generate summary report
        response = self.client.get(
            '/api/v1/payroll/records/summary/?period_start=2024-01-01&period_end=2024-01-31'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_count'], 2)
        
        # Step 8: Generate detailed report
        response = self.client.get(
            '/api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31&type=detailed'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('records', response.data)
        self.assertEqual(len(response.data['records']), 2)
    
    def test_payroll_with_attendance_deductions(self):
        """
        Test that payroll correctly deducts for absent days.
        """
        # Create salary rules
        SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00"),
            is_active=True
        )
        
        # Create attendance for only 15 days (out of ~22 working days)
        for day in range(1, 16):
            AttendanceRecord.objects.create(
                company=self.company,
                employee=self.employee1,
                date=date(2024, 1, day),
                check_in=timezone.now(),
                check_out=timezone.now(),
                status='present'
            )
        
        # Generate payroll
        service = PayrollCalculationService(self.company)
        payroll_record = service.generate_payroll_record(
            self.employee1,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        # Verify deductions were applied for absent days
        self.assertEqual(payroll_record.present_days, 15)
        self.assertGreater(payroll_record.deductions, 0)
        self.assertLess(payroll_record.net_salary, payroll_record.basic_salary)
    
    def test_bulk_payroll_processing_with_filtering(self):
        """
        Test bulk payroll processing with department filtering.
        """
        # Create another department
        sales_dept = Department.objects.create(
            company=self.company,
            name="Sales"
        )
        
        # Create employee in sales
        sales_employee = Employee.objects.create(
            company=self.company,
            employee_id="EMP003",
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@test.com",
            department=sales_dept,
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        # Create salary rule
        SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00"),
            is_active=True
        )
        
        # Process payroll only for Engineering department
        bulk_data = {
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'department_id': str(self.department.id)
        }
        response = self.client.post('/api/v1/payroll/bulk-process/', bulk_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should process only 2 employees from Engineering
        self.assertEqual(response.data['results']['total'], 2)
        
        # Verify sales employee was not processed
        sales_payroll = PayrollRecord.objects.filter(employee=sales_employee)
        self.assertEqual(sales_payroll.count(), 0)
    
    def test_payroll_summary_by_department(self):
        """
        Test department-wise payroll summary.
        """
        # Create salary rule
        SalaryRule.objects.create(
            company=self.company,
            name="Basic Salary",
            rule_type="basic",
            calculation_method="fixed",
            amount=Decimal("5000.00"),
            is_active=True
        )
        
        # Generate payroll
        service = PayrollCalculationService(self.company)
        service.bulk_generate_payroll(date(2024, 1, 1), date(2024, 1, 31))
        
        # Get department report
        response = self.client.get(
            '/api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31&type=department'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('departments', response.data)
        
        # Find Engineering department
        eng_dept = [d for d in response.data['departments'] if d['department_name'] == 'Engineering'][0]
        self.assertEqual(eng_dept['employee_count'], 2)
