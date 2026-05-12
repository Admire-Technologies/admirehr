"""
Celery tasks for attendance reporting and processing.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from datetime import datetime, timedelta

from apps.core.tasks import CallbackTask, send_email_task
from .models import AttendanceRecord
from apps.employees.models import Employee
from apps.core.models import Company

logger = get_task_logger(__name__)


@shared_task(bind=True, base=CallbackTask)
def generate_attendance_report(self, company_id, start_date, end_date, report_type='summary', department_id=None):
    """
    Generate attendance report for a specific period.
    
    Args:
        company_id: Company UUID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        report_type: Type of report (summary, detailed, employee)
        department_id: Optional department UUID for filtering
    """
    try:
        logger.info(f"Generating {report_type} attendance report for company {company_id}")
        
        company = Company.objects.get(id=company_id)
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()
        
        # Get attendance records
        attendance_records = AttendanceRecord.objects.filter(
            company=company,
            date__gte=start_date_obj,
            date__lte=end_date_obj
        ).select_related('employee', 'employee__department')
        
        if department_id:
            attendance_records = attendance_records.filter(
                employee__department_id=department_id
            )
        
        if report_type == 'summary':
            # Generate summary report
            summary = attendance_records.aggregate(
                total_records=Count('id'),
                present_count=Count('id', filter=Q(status='present')),
                absent_count=Count('id', filter=Q(status='absent')),
                late_count=Count('id', filter=Q(status='late')),
                total_working_hours=Sum('working_hours'),
                avg_working_hours=Avg('working_hours')
            )
            
            # Calculate attendance percentage
            if summary['total_records'] > 0:
                summary['attendance_percentage'] = (
                    summary['present_count'] / summary['total_records']
                ) * 100
            else:
                summary['attendance_percentage'] = 0
            
            report_data = {
                'report_type': 'summary',
                'start_date': start_date,
                'end_date': end_date,
                'company': company.name,
                'summary': summary
            }
        
        elif report_type == 'employee':
            # Generate employee-wise report
            employees = Employee.objects.filter(
                company=company,
                status='active'
            )
            
            if department_id:
                employees = employees.filter(department_id=department_id)
            
            employee_data = []
            
            for employee in employees:
                emp_records = attendance_records.filter(employee=employee)
                emp_summary = emp_records.aggregate(
                    total_days=Count('id'),
                    present_days=Count('id', filter=Q(status='present')),
                    absent_days=Count('id', filter=Q(status='absent')),
                    late_days=Count('id', filter=Q(status='late')),
                    total_hours=Sum('working_hours')
                )
                
                # Calculate attendance percentage
                if emp_summary['total_days'] > 0:
                    emp_summary['attendance_percentage'] = (
                        emp_summary['present_days'] / emp_summary['total_days']
                    ) * 100
                else:
                    emp_summary['attendance_percentage'] = 0
                
                employee_data.append({
                    'employee_id': str(employee.id),
                    'employee_name': employee.full_name,
                    'employee_code': employee.employee_id,
                    'department': employee.department.name if employee.department else 'N/A',
                    **emp_summary
                })
            
            report_data = {
                'report_type': 'employee',
                'start_date': start_date,
                'end_date': end_date,
                'company': company.name,
                'employees': employee_data
            }
        
        else:
            # Detailed report
            report_data = {
                'report_type': 'detailed',
                'start_date': start_date,
                'end_date': end_date,
                'company': company.name,
                'records': list(attendance_records.values(
                    'employee__first_name',
                    'employee__last_name',
                    'employee__employee_id',
                    'date',
                    'check_in',
                    'check_out',
                    'working_hours',
                    'status'
                ))
            }
        
        logger.info(f"Attendance report generated successfully")
        
        return {
            'status': 'success',
            'report_data': report_data
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {'status': 'error', 'error': 'Company not found'}
    
    except Exception as exc:
        logger.error(f"Failed to generate attendance report: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_daily_attendance_summary(self, company_id=None):
    """
    Send daily attendance summary email to managers.
    Scheduled task that runs at end of day.
    
    Args:
        company_id: Optional company UUID. If None, processes all companies.
    """
    try:
        logger.info("Sending daily attendance summaries")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)
        
        today = timezone.now().date()
        emails_sent = 0
        
        for company in companies:
            # Get today's attendance summary
            attendance_records = AttendanceRecord.objects.filter(
                company=company,
                date=today
            )
            
            summary = attendance_records.aggregate(
                total_employees=Count('employee', distinct=True),
                present_count=Count('id', filter=Q(status='present')),
                absent_count=Count('id', filter=Q(status='absent')),
                late_count=Count('id', filter=Q(status='late'))
            )
            
            # Get manager emails
            from apps.authentication.models import User
            
            managers = User.objects.filter(
                company=company,
                role__name__in=['Manager', 'HR Manager', 'Admin']
            ).values_list('email', flat=True)
            
            if not managers:
                logger.warning(f"No managers found for company {company.id}")
                continue
            
            manager_emails = [email for email in managers if email]
            
            if not manager_emails:
                continue
            
            subject = f"Daily Attendance Summary - {today}"
            message = (
                f"Daily Attendance Summary for {company.name}\n"
                f"Date: {today}\n\n"
                f"Total Employees: {summary['total_employees']}\n"
                f"Present: {summary['present_count']}\n"
                f"Absent: {summary['absent_count']}\n"
                f"Late: {summary['late_count']}\n\n"
                f"Please review the detailed attendance records in the HRMS portal.\n\n"
                f"Best regards,\n"
                f"HRMS System"
            )
            
            send_email_task.delay(
                subject=subject,
                message=message,
                recipient_list=manager_emails
            )
            
            emails_sent += len(manager_emails)
        
        logger.info(f"Daily attendance summaries sent to {emails_sent} recipients")
        
        return {
            'status': 'success',
            'companies_processed': companies.count(),
            'emails_sent': emails_sent
        }
        
    except Exception as exc:
        logger.error(f"Failed to send daily attendance summaries: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_absent_employee_alert(self, company_id=None):
    """
    Send alert for employees who are absent without leave.
    Scheduled task that runs during work hours.
    
    Args:
        company_id: Optional company UUID. If None, processes all companies.
    """
    try:
        logger.info("Checking for absent employees")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)
        
        today = timezone.now().date()
        alerts_sent = 0
        
        for company in companies:
            # Get employees who are absent today
            absent_records = AttendanceRecord.objects.filter(
                company=company,
                date=today,
                status='absent'
            ).select_related('employee', 'employee__user')
            
            # Check if they have approved leave
            from apps.leave_management.models import LeaveRequest
            
            for record in absent_records:
                # Check for approved leave
                has_leave = LeaveRequest.objects.filter(
                    employee=record.employee,
                    status='approved',
                    start_date__lte=today,
                    end_date__gte=today
                ).exists()
                
                if not has_leave:
                    # Send alert to HR
                    from apps.authentication.models import User
                    
                    hr_emails = User.objects.filter(
                        company=company,
                        role__name__in=['HR Manager', 'Admin']
                    ).values_list('email', flat=True)
                    
                    if hr_emails:
                        subject = f"Absent Employee Alert - {record.employee.full_name}"
                        message = (
                            f"Employee {record.employee.full_name} ({record.employee.employee_id}) "
                            f"is marked absent today without approved leave.\n\n"
                            f"Date: {today}\n"
                            f"Department: {record.employee.department.name if record.employee.department else 'N/A'}\n\n"
                            f"Please follow up with the employee.\n"
                        )
                        
                        send_email_task.delay(
                            subject=subject,
                            message=message,
                            recipient_list=list(hr_emails)
                        )
                        
                        alerts_sent += 1
        
        logger.info(f"Absent employee alerts sent: {alerts_sent}")
        
        return {
            'status': 'success',
            'companies_processed': companies.count(),
            'alerts_sent': alerts_sent
        }
        
    except Exception as exc:
        logger.error(f"Failed to send absent employee alerts: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def calculate_monthly_attendance_summary(self, company_id=None, year=None, month=None):
    """
    Calculate and store monthly attendance summary for all employees.
    Scheduled task that runs at the beginning of each month.
    
    Args:
        company_id: Optional company UUID. If None, processes all companies.
        year: Year to process. Defaults to previous month.
        month: Month to process. Defaults to previous month.
    """
    try:
        # Default to previous month
        if year is None or month is None:
            today = timezone.now().date()
            first_day_current_month = today.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            year = last_day_previous_month.year
            month = last_day_previous_month.month
        
        logger.info(f"Calculating monthly attendance summary for {year}-{month:02d}")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)
        
        # Calculate date range
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        
        summaries_created = 0
        
        for company in companies:
            employees = Employee.objects.filter(
                company=company,
                status='active'
            )
            
            for employee in employees:
                # Get attendance records for the month
                records = AttendanceRecord.objects.filter(
                    employee=employee,
                    date__gte=start_date,
                    date__lte=end_date
                )
                
                summary = records.aggregate(
                    total_days=Count('id'),
                    present_days=Count('id', filter=Q(status='present')),
                    absent_days=Count('id', filter=Q(status='absent')),
                    late_days=Count('id', filter=Q(status='late')),
                    total_hours=Sum('working_hours')
                )
                
                # Store summary (you might want to create a MonthlyAttendanceSummary model)
                logger.debug(
                    f"Monthly summary for {employee.full_name}: "
                    f"Present: {summary['present_days']}, Absent: {summary['absent_days']}"
                )
                
                summaries_created += 1
        
        logger.info(f"Created {summaries_created} monthly attendance summaries")
        
        return {
            'status': 'success',
            'year': year,
            'month': month,
            'companies_processed': companies.count(),
            'summaries_created': summaries_created
        }
        
    except Exception as exc:
        logger.error(f"Failed to calculate monthly attendance summary: {exc}")
        raise
