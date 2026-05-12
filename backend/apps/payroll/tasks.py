"""
Celery tasks for payroll processing.
"""

from celery import shared_task, group, chord
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal

from apps.core.tasks import CallbackTask, send_email_task
from .models import PayrollRecord, SalaryRule, EmployeeSalaryStructure
from .services import PayrollCalculationService, PayrollCalculationError
from apps.employees.models import Employee
from apps.core.models import Company

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=300
)
def generate_payroll_for_employee(self, employee_id, period_start, period_end, company_id):
    """
    Generate payroll record for a single employee.
    
    Args:
        employee_id: Employee UUID
        period_start: Period start date (ISO format)
        period_end: Period end date (ISO format)
        company_id: Company UUID
    """
    try:
        logger.info(f"Generating payroll for employee {employee_id} for period {period_start} to {period_end}")
        
        # Convert dates
        period_start = datetime.fromisoformat(period_start).date()
        period_end = datetime.fromisoformat(period_end).date()
        
        # Get employee and company
        employee = Employee.objects.select_related('company', 'department').get(
            id=employee_id,
            company_id=company_id
        )
        company = Company.objects.get(id=company_id)
        
        # Initialize payroll service
        service = PayrollCalculationService(company)
        
        # Generate payroll record
        payroll_record = service.generate_payroll_record(
            employee=employee,
            period_start=period_start,
            period_end=period_end
        )
        
        logger.info(
            f"Payroll generated successfully for {employee.full_name}: "
            f"Net Salary = {payroll_record.net_salary}"
        )
        
        # Queue email notification
        send_payslip_notification.delay(str(payroll_record.id))
        
        return {
            'status': 'success',
            'employee_id': str(employee_id),
            'employee_name': employee.full_name,
            'payroll_id': str(payroll_record.id),
            'net_salary': float(payroll_record.net_salary)
        }
        
    except Employee.DoesNotExist:
        logger.error(f"Employee {employee_id} not found")
        return {
            'status': 'error',
            'employee_id': str(employee_id),
            'error': 'Employee not found'
        }
    
    except PayrollCalculationError as exc:
        logger.error(f"Payroll calculation error for employee {employee_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)
    
    except Exception as exc:
        logger.error(f"Failed to generate payroll for employee {employee_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(
    bind=True,
    base=CallbackTask,
    max_retries=2
)
def bulk_generate_payroll(self, company_id, period_start, period_end, employee_ids=None, department_id=None):
    """
    Generate payroll for multiple employees in bulk.
    
    Args:
        company_id: Company UUID
        period_start: Period start date (ISO format)
        period_end: Period end date (ISO format)
        employee_ids: Optional list of employee UUIDs
        department_id: Optional department UUID for filtering
    """
    try:
        logger.info(f"Starting bulk payroll generation for company {company_id}")
        
        # Get company
        company = Company.objects.get(id=company_id)
        
        # Build employee queryset
        employees = Employee.objects.filter(
            company=company,
            status='active'
        )
        
        if department_id:
            employees = employees.filter(department_id=department_id)
        
        if employee_ids:
            employees = employees.filter(id__in=employee_ids)
        
        employee_list = list(employees.values_list('id', flat=True))
        total_employees = len(employee_list)
        
        logger.info(f"Processing payroll for {total_employees} employees")
        
        # Create a group of tasks for parallel processing
        job = group(
            generate_payroll_for_employee.s(
                str(emp_id),
                period_start,
                period_end,
                str(company_id)
            ) for emp_id in employee_list
        )
        
        # Execute tasks in parallel
        result = job.apply_async()
        
        # Wait for all tasks to complete (with timeout)
        results = result.get(timeout=3600)  # 1 hour timeout
        
        # Aggregate results
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = total_employees - successful
        
        logger.info(
            f"Bulk payroll generation completed: "
            f"{successful} successful, {failed} failed out of {total_employees}"
        )
        
        # Send summary email to admin
        send_payroll_summary_email.delay(
            company_id=str(company_id),
            period_start=period_start,
            period_end=period_end,
            total=total_employees,
            successful=successful,
            failed=failed
        )
        
        return {
            'status': 'completed',
            'company_id': str(company_id),
            'period_start': period_start,
            'period_end': period_end,
            'total_employees': total_employees,
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {
            'status': 'error',
            'error': 'Company not found'
        }
    
    except Exception as exc:
        logger.error(f"Bulk payroll generation failed: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_payslip_notification(self, payroll_id):
    """
    Send payslip notification email to employee.
    
    Args:
        payroll_id: PayrollRecord UUID
    """
    try:
        payroll_record = PayrollRecord.objects.select_related(
            'employee',
            'employee__user',
            'company'
        ).get(id=payroll_id)
        
        employee = payroll_record.employee
        
        if not employee.user or not employee.user.email:
            logger.warning(f"Employee {employee.id} has no associated user or email")
            return {'status': 'skipped', 'reason': 'no_email'}
        
        # Prepare email context
        context = {
            'employee_name': employee.full_name,
            'period': payroll_record.period_display,
            'net_salary': payroll_record.net_salary,
            'payroll_id': str(payroll_record.id),
            'company_name': payroll_record.company.name
        }
        
        subject = f"Your Payslip for {payroll_record.period_display} is Ready"
        message = (
            f"Dear {employee.full_name},\n\n"
            f"Your payslip for {payroll_record.period_display} has been processed.\n"
            f"Net Salary: {payroll_record.net_salary} {payroll_record.company.currency}\n\n"
            f"Please log in to the HRMS portal to view and download your payslip.\n\n"
            f"Best regards,\n"
            f"{payroll_record.company.name}"
        )
        
        send_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=[employee.user.email]
        )
        
        logger.info(f"Payslip notification sent to {employee.user.email}")
        
        return {
            'status': 'success',
            'payroll_id': str(payroll_id),
            'employee_email': employee.user.email
        }
        
    except PayrollRecord.DoesNotExist:
        logger.error(f"PayrollRecord {payroll_id} not found")
        return {'status': 'error', 'error': 'Payroll record not found'}
    
    except Exception as exc:
        logger.error(f"Failed to send payslip notification: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_payroll_summary_email(self, company_id, period_start, period_end, total, successful, failed):
    """
    Send payroll processing summary email to company admin.
    
    Args:
        company_id: Company UUID
        period_start: Period start date
        period_end: Period end date
        total: Total employees processed
        successful: Number of successful payroll generations
        failed: Number of failed payroll generations
    """
    try:
        company = Company.objects.get(id=company_id)
        
        # Get admin users
        from apps.authentication.models import User
        admin_users = User.objects.filter(
            company=company,
            role__name__in=['Admin', 'HR Manager']
        ).values_list('email', flat=True)
        
        if not admin_users:
            logger.warning(f"No admin users found for company {company_id}")
            return {'status': 'skipped', 'reason': 'no_admins'}
        
        subject = f"Payroll Processing Summary - {period_start} to {period_end}"
        message = (
            f"Payroll Processing Summary\n"
            f"Company: {company.name}\n"
            f"Period: {period_start} to {period_end}\n\n"
            f"Total Employees: {total}\n"
            f"Successful: {successful}\n"
            f"Failed: {failed}\n\n"
            f"Please review the payroll records in the HRMS portal.\n"
        )
        
        send_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=list(admin_users)
        )
        
        logger.info(f"Payroll summary email sent to {len(admin_users)} admins")
        
        return {
            'status': 'success',
            'recipients': len(admin_users)
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {'status': 'error', 'error': 'Company not found'}
    
    except Exception as exc:
        logger.error(f"Failed to send payroll summary email: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def monthly_payroll_generation(self, company_id=None):
    """
    Scheduled task for monthly payroll generation.
    Runs on the 1st of each month for the previous month.
    
    Args:
        company_id: Optional company UUID. If None, processes all companies.
    """
    try:
        logger.info("Starting monthly payroll generation")
        
        # Calculate previous month period
        today = timezone.now().date()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1)
        
        period_start = first_day_previous_month.isoformat()
        period_end = last_day_previous_month.isoformat()
        
        logger.info(f"Processing payroll for period: {period_start} to {period_end}")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)
        
        results = []
        for company in companies:
            logger.info(f"Processing payroll for company: {company.name}")
            
            # Queue bulk payroll generation
            result = bulk_generate_payroll.delay(
                company_id=str(company.id),
                period_start=period_start,
                period_end=period_end
            )
            
            results.append({
                'company_id': str(company.id),
                'company_name': company.name,
                'task_id': result.id
            })
        
        logger.info(f"Monthly payroll generation queued for {len(results)} companies")
        
        return {
            'status': 'success',
            'period_start': period_start,
            'period_end': period_end,
            'companies_processed': len(results),
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Monthly payroll generation failed: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def generate_payroll_report(self, company_id, period_start, period_end, report_type='summary'):
    """
    Generate payroll report for a specific period.
    
    Args:
        company_id: Company UUID
        period_start: Period start date (ISO format)
        period_end: Period end date (ISO format)
        report_type: Type of report (summary, detailed, department)
    """
    try:
        logger.info(f"Generating {report_type} payroll report for company {company_id}")
        
        company = Company.objects.get(id=company_id)
        period_start_date = datetime.fromisoformat(period_start).date()
        period_end_date = datetime.fromisoformat(period_end).date()
        
        # Get payroll records
        payroll_records = PayrollRecord.objects.filter(
            company=company,
            period_start=period_start_date,
            period_end=period_end_date
        ).select_related('employee', 'employee__department')
        
        if report_type == 'summary':
            # Generate summary report
            from django.db.models import Sum, Avg, Count
            
            summary = payroll_records.aggregate(
                total_employees=Count('id'),
                total_gross_salary=Sum('gross_salary'),
                total_net_salary=Sum('net_salary'),
                total_deductions=Sum('deductions'),
                total_allowances=Sum('allowances'),
                avg_net_salary=Avg('net_salary')
            )
            
            report_data = {
                'report_type': 'summary',
                'period_start': period_start,
                'period_end': period_end,
                'company': company.name,
                'summary': summary
            }
        
        elif report_type == 'department':
            # Generate department-wise report
            from apps.employees.models import Department
            
            departments = Department.objects.filter(company=company)
            department_data = []
            
            for dept in departments:
                dept_payroll = payroll_records.filter(employee__department=dept)
                dept_summary = dept_payroll.aggregate(
                    employee_count=Count('id'),
                    total_net_salary=Sum('net_salary'),
                    total_gross_salary=Sum('gross_salary')
                )
                
                department_data.append({
                    'department_name': dept.name,
                    **dept_summary
                })
            
            report_data = {
                'report_type': 'department',
                'period_start': period_start,
                'period_end': period_end,
                'company': company.name,
                'departments': department_data
            }
        
        else:
            # Detailed report
            report_data = {
                'report_type': 'detailed',
                'period_start': period_start,
                'period_end': period_end,
                'company': company.name,
                'records': list(payroll_records.values(
                    'employee__first_name',
                    'employee__last_name',
                    'employee__employee_id',
                    'basic_salary',
                    'allowances',
                    'deductions',
                    'gross_salary',
                    'net_salary'
                ))
            }
        
        logger.info(f"Payroll report generated successfully")
        
        return {
            'status': 'success',
            'report_data': report_data
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {'status': 'error', 'error': 'Company not found'}
    
    except Exception as exc:
        logger.error(f"Failed to generate payroll report: {exc}")
        raise
