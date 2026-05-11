"""
Payroll calculation service for processing employee salaries.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Q
from django.utils import timezone
from .models import PayrollRecord, SalaryRule
from apps.employees.models import Employee
from apps.attendance.models import AttendanceRecord
from apps.leave_management.models import LeaveRequest


class PayrollCalculationError(Exception):
    """Custom exception for payroll calculation errors."""
    pass


class PayrollCalculationService:
    """
    Service class for calculating employee payroll based on attendance,
    leave, and salary rules.
    """
    
    def __init__(self, company):
        self.company = company
    
    def calculate_payroll(self, employee, period_start, period_end):
        """
        Calculate payroll for a single employee for the given period.
        
        Args:
            employee: Employee instance
            period_start: Start date of payroll period
            period_end: End date of payroll period
            
        Returns:
            dict: Calculated payroll components
        """
        # Get employee's salary rules
        salary_rules = self._get_employee_salary_rules(employee)
        
        # Calculate basic salary
        basic_salary = self._calculate_basic_salary(salary_rules)
        
        # Calculate attendance-based adjustments
        attendance_data = self._get_attendance_data(employee, period_start, period_end)
        
        # Calculate leave-based deductions
        leave_data = self._get_leave_data(employee, period_start, period_end)
        
        # Calculate allowances
        allowances = self._calculate_allowances(salary_rules, basic_salary)
        
        # Calculate deductions
        deductions = self._calculate_deductions(
            salary_rules, 
            basic_salary, 
            attendance_data, 
            leave_data
        )
        
        # Calculate gross and net salary
        gross_salary = basic_salary + allowances
        net_salary = gross_salary - deductions
        
        return {
            'basic_salary': basic_salary,
            'allowances': allowances,
            'deductions': deductions,
            'gross_salary': gross_salary,
            'net_salary': net_salary,
            'attendance_days': attendance_data['present_days'],
            'total_working_days': attendance_data['total_working_days'],
            'leave_days': leave_data['approved_leave_days'],
            'unpaid_leave_days': leave_data['unpaid_leave_days'],
        }
    
    def generate_payroll_record(self, employee, period_start, period_end):
        """
        Generate and save a payroll record for an employee.
        
        Args:
            employee: Employee instance
            period_start: Start date of payroll period
            period_end: End date of payroll period
            
        Returns:
            PayrollRecord: Created payroll record
        """
        # Check if payroll already exists for this period
        existing = PayrollRecord.objects.filter(
            employee=employee,
            period_start=period_start,
            period_end=period_end,
            company=self.company
        ).first()
        
        if existing:
            raise PayrollCalculationError(
                f"Payroll already exists for {employee.full_name} "
                f"for period {period_start} to {period_end}"
            )
        
        # Calculate payroll
        payroll_data = self.calculate_payroll(employee, period_start, period_end)
        
        # Create payroll record
        payroll_record = PayrollRecord.objects.create(
            employee=employee,
            company=self.company,
            period_start=period_start,
            period_end=period_end,
            basic_salary=payroll_data['basic_salary'],
            allowances=payroll_data['allowances'],
            deductions=payroll_data['deductions'],
            gross_salary=payroll_data['gross_salary'],
            net_salary=payroll_data['net_salary'],
            working_days=payroll_data['total_working_days'],
            present_days=payroll_data['attendance_days'],
            leave_days=payroll_data['leave_days'],
            absent_days=payroll_data['total_working_days'] - payroll_data['attendance_days'] - int(payroll_data['leave_days']),
            is_processed=True,
            processed_at=timezone.now()
        )
        
        return payroll_record
    
    def bulk_generate_payroll(self, period_start, period_end, employee_ids=None):
        """
        Generate payroll for multiple employees.
        
        Args:
            period_start: Start date of payroll period
            period_end: End date of payroll period
            employee_ids: Optional list of employee IDs to process
            
        Returns:
            dict: Summary of payroll generation
        """
        # Get employees to process
        employees = Employee.objects.filter(
            company=self.company,
            status='active'
        )
        
        if employee_ids:
            employees = employees.filter(id__in=employee_ids)
        
        results = {
            'total': employees.count(),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for employee in employees:
            try:
                self.generate_payroll_record(employee, period_start, period_end)
                results['successful'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'employee_id': str(employee.id),
                    'employee_name': employee.full_name,
                    'error': str(e)
                })
        
        return results
    
    def _get_employee_salary_rules(self, employee):
        """Get active salary rules for the company."""
        return SalaryRule.objects.filter(
            company=self.company,
            is_active=True
        )
    
    def _calculate_basic_salary(self, salary_rules):
        """Calculate basic salary from salary rules."""
        basic_rule = salary_rules.filter(rule_type='basic').first()
        if not basic_rule:
            raise PayrollCalculationError("No basic salary rule defined")
        return basic_rule.amount
    
    def _get_attendance_data(self, employee, period_start, period_end):
        """
        Get attendance data for the employee in the given period.
        
        Returns:
            dict: Attendance statistics
        """
        # Get attendance records
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            company=self.company,
            date__gte=period_start,
            date__lte=period_end
        )
        
        # Count present days
        present_days = attendance_records.filter(
            status__in=['present', 'late', 'half_day']
        ).count()
        
        # Calculate total working days (excluding weekends)
        total_days = (period_end - period_start).days + 1
        working_days_per_week = self.company.working_days_per_week
        total_working_days = (total_days // 7) * working_days_per_week
        
        # Add remaining days
        remaining_days = total_days % 7
        if remaining_days > 0:
            total_working_days += min(remaining_days, working_days_per_week)
        
        return {
            'present_days': present_days,
            'total_working_days': total_working_days,
            'absent_days': total_working_days - present_days
        }
    
    def _get_leave_data(self, employee, period_start, period_end):
        """
        Get leave data for the employee in the given period.
        
        Returns:
            dict: Leave statistics
        """
        # Get approved leave requests
        leave_requests = LeaveRequest.objects.filter(
            employee=employee,
            company=self.company,
            status='approved',
            start_date__lte=period_end,
            end_date__gte=period_start
        )
        
        approved_leave_days = sum(
            float(lr.days_requested) for lr in leave_requests
        )
        
        # For now, assume all leave is paid
        # In a real system, you'd check leave type to determine if it's unpaid
        unpaid_leave_days = 0
        
        return {
            'approved_leave_days': approved_leave_days,
            'unpaid_leave_days': unpaid_leave_days
        }
    
    def _calculate_allowances(self, salary_rules, basic_salary):
        """Calculate total allowances based on salary rules."""
        allowances = Decimal('0.00')
        
        for rule in salary_rules.filter(rule_type='allowance'):
            if rule.calculation_method == 'fixed':
                allowances += rule.amount
            elif rule.calculation_method == 'percentage':
                allowances += (basic_salary * rule.amount / Decimal('100'))
        
        return allowances
    
    def _calculate_deductions(self, salary_rules, basic_salary, attendance_data, leave_data):
        """Calculate total deductions based on salary rules and attendance."""
        deductions = Decimal('0.00')
        
        # Apply salary rule deductions
        for rule in salary_rules.filter(rule_type='deduction'):
            if rule.calculation_method == 'fixed':
                deductions += rule.amount
            elif rule.calculation_method == 'percentage':
                deductions += (basic_salary * rule.amount / Decimal('100'))
        
        # Calculate deductions for unpaid leave
        if leave_data['unpaid_leave_days'] > 0:
            daily_rate = basic_salary / Decimal(str(attendance_data['total_working_days']))
            deductions += daily_rate * Decimal(str(leave_data['unpaid_leave_days']))
        
        # Calculate deductions for absent days (not covered by leave)
        absent_days = attendance_data['absent_days'] - leave_data['approved_leave_days']
        if absent_days > 0:
            daily_rate = basic_salary / Decimal(str(attendance_data['total_working_days']))
            deductions += daily_rate * Decimal(str(absent_days))
        
        return deductions
    
    def get_payroll_summary(self, period_start, period_end, department_id=None):
        """
        Get payroll summary for a period, optionally filtered by department.
        
        Args:
            period_start: Start date of payroll period
            period_end: End date of payroll period
            department_id: Optional department ID to filter by
            
        Returns:
            dict: Payroll summary statistics
        """
        payroll_records = PayrollRecord.objects.filter(
            company=self.company,
            period_start=period_start,
            period_end=period_end
        )
        
        if department_id:
            payroll_records = payroll_records.filter(
                employee__department_id=department_id
            )
        
        summary = payroll_records.aggregate(
            total_basic_salary=Sum('basic_salary'),
            total_allowances=Sum('allowances'),
            total_deductions=Sum('deductions'),
            total_gross_salary=Sum('gross_salary'),
            total_net_salary=Sum('net_salary')
        )
        
        summary['employee_count'] = payroll_records.count()
        
        return summary
