"""
Celery tasks for leave management.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import datetime, timedelta

from apps.core.tasks import CallbackTask, send_email_task
from .models import LeaveRequest, LeaveBalance, LeaveType
from apps.employees.models import Employee
from apps.core.models import Company

logger = get_task_logger(__name__)


@shared_task(bind=True, base=CallbackTask)
def send_leave_approval_notification(self, leave_request_id):
    """
    Send leave approval notification email to employee.
    
    Args:
        leave_request_id: LeaveRequest UUID
    """
    try:
        leave_request = LeaveRequest.objects.select_related(
            'employee',
            'employee__user',
            'leave_type',
            'approver',
            'company'
        ).get(id=leave_request_id)
        
        employee = leave_request.employee
        
        if not employee.user or not employee.user.email:
            logger.warning(f"Employee {employee.id} has no associated user or email")
            return {'status': 'skipped', 'reason': 'no_email'}
        
        # Prepare email based on status
        if leave_request.status == 'approved':
            subject = "Leave Request Approved"
            message = (
                f"Dear {employee.full_name},\n\n"
                f"Your leave request has been approved.\n\n"
                f"Leave Type: {leave_request.leave_type.name}\n"
                f"Start Date: {leave_request.start_date}\n"
                f"End Date: {leave_request.end_date}\n"
                f"Days: {leave_request.days_requested}\n"
                f"Approved by: {leave_request.approver.full_name if leave_request.approver else 'System'}\n\n"
                f"Best regards,\n"
                f"{leave_request.company.name}"
            )
        elif leave_request.status == 'rejected':
            subject = "Leave Request Rejected"
            message = (
                f"Dear {employee.full_name},\n\n"
                f"Your leave request has been rejected.\n\n"
                f"Leave Type: {leave_request.leave_type.name}\n"
                f"Start Date: {leave_request.start_date}\n"
                f"End Date: {leave_request.end_date}\n"
                f"Days: {leave_request.days_requested}\n"
                f"Rejected by: {leave_request.approver.full_name if leave_request.approver else 'System'}\n"
                f"Reason: {leave_request.rejection_reason}\n\n"
                f"Best regards,\n"
                f"{leave_request.company.name}"
            )
        else:
            logger.warning(f"Leave request {leave_request_id} has status {leave_request.status}")
            return {'status': 'skipped', 'reason': 'invalid_status'}
        
        send_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=[employee.user.email]
        )
        
        logger.info(f"Leave {leave_request.status} notification sent to {employee.user.email}")
        
        return {
            'status': 'success',
            'leave_request_id': str(leave_request_id),
            'employee_email': employee.user.email,
            'leave_status': leave_request.status
        }
        
    except LeaveRequest.DoesNotExist:
        logger.error(f"LeaveRequest {leave_request_id} not found")
        return {'status': 'error', 'error': 'Leave request not found'}
    
    except Exception as exc:
        logger.error(f"Failed to send leave notification: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_leave_request_notification_to_manager(self, leave_request_id):
    """
    Send leave request notification to manager for approval.
    
    Args:
        leave_request_id: LeaveRequest UUID
    """
    try:
        leave_request = LeaveRequest.objects.select_related(
            'employee',
            'employee__department',
            'leave_type',
            'company'
        ).get(id=leave_request_id)
        
        # Get department managers or HR admins
        from apps.authentication.models import User
        
        managers = User.objects.filter(
            company=leave_request.company,
            role__name__in=['Manager', 'HR Manager', 'Admin']
        ).exclude(employee=leave_request.employee)
        
        if not managers.exists():
            logger.warning(f"No managers found for company {leave_request.company.id}")
            return {'status': 'skipped', 'reason': 'no_managers'}
        
        manager_emails = [m.email for m in managers if m.email]
        
        if not manager_emails:
            logger.warning(f"No manager emails found for company {leave_request.company.id}")
            return {'status': 'skipped', 'reason': 'no_manager_emails'}
        
        subject = f"New Leave Request from {leave_request.employee.full_name}"
        message = (
            f"A new leave request requires your approval.\n\n"
            f"Employee: {leave_request.employee.full_name}\n"
            f"Department: {leave_request.employee.department.name if leave_request.employee.department else 'N/A'}\n"
            f"Leave Type: {leave_request.leave_type.name}\n"
            f"Start Date: {leave_request.start_date}\n"
            f"End Date: {leave_request.end_date}\n"
            f"Days: {leave_request.days_requested}\n"
            f"Reason: {leave_request.reason}\n\n"
            f"Please log in to the HRMS portal to approve or reject this request.\n\n"
            f"Best regards,\n"
            f"{leave_request.company.name}"
        )
        
        send_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=manager_emails
        )
        
        logger.info(f"Leave request notification sent to {len(manager_emails)} managers")
        
        return {
            'status': 'success',
            'leave_request_id': str(leave_request_id),
            'recipients': len(manager_emails)
        }
        
    except LeaveRequest.DoesNotExist:
        logger.error(f"LeaveRequest {leave_request_id} not found")
        return {'status': 'error', 'error': 'Leave request not found'}
    
    except Exception as exc:
        logger.error(f"Failed to send leave request notification: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def initialize_annual_leave_balances(self, company_id=None, year=None):
    """
    Initialize leave balances for all employees for a given year.
    Scheduled task that runs at the beginning of each year.
    
    Args:
        company_id: Optional company UUID. If None, processes all companies.
        year: Year to initialize balances for. Defaults to current year.
    """
    try:
        if year is None:
            year = timezone.now().year
        
        logger.info(f"Initializing leave balances for year {year}")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)
        
        total_balances_created = 0
        
        for company in companies:
            logger.info(f"Processing leave balances for company: {company.name}")
            
            # Get active employees
            employees = Employee.objects.filter(
                company=company,
                status='active'
            )
            
            # Get active leave types
            leave_types = LeaveType.objects.filter(
                company=company,
                is_active=True
            )
            
            # Create balances for each employee and leave type
            for employee in employees:
                for leave_type in leave_types:
                    balance, created = LeaveBalance.objects.get_or_create(
                        employee=employee,
                        leave_type=leave_type,
                        year=year,
                        company=company,
                        defaults={'accrued_days': leave_type.days_allowed}
                    )
                    
                    if created:
                        total_balances_created += 1
                        logger.debug(
                            f"Created leave balance for {employee.full_name} - "
                            f"{leave_type.name}: {leave_type.days_allowed} days"
                        )
        
        logger.info(f"Initialized {total_balances_created} leave balances for year {year}")
        
        return {
            'status': 'success',
            'year': year,
            'companies_processed': companies.count(),
            'balances_created': total_balances_created
        }
        
    except Exception as exc:
        logger.error(f"Failed to initialize leave balances: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_leave_balance_reminder(self, company_id=None):
    """
    Send leave balance reminder emails to employees.
    Scheduled task that runs monthly or quarterly.
    
    Args:
        company_id: Optional company UUID. If None, processes all companies.
    """
    try:
        logger.info("Sending leave balance reminders")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id, is_active=True)
        else:
            companies = Company.objects.filter(is_active=True)
        
        current_year = timezone.now().year
        emails_sent = 0
        
        for company in companies:
            # Get active employees with leave balances
            employees = Employee.objects.filter(
                company=company,
                status='active',
                user__isnull=False
            ).select_related('user')
            
            for employee in employees:
                if not employee.user.email:
                    continue
                
                # Get leave balances
                balances = LeaveBalance.objects.filter(
                    employee=employee,
                    year=current_year,
                    company=company
                ).select_related('leave_type')
                
                if not balances.exists():
                    continue
                
                # Prepare balance summary
                balance_summary = []
                for balance in balances:
                    balance_summary.append(
                        f"{balance.leave_type.name}: {balance.available_days} days available "
                        f"(Used: {balance.used_days}, Pending: {balance.pending_days})"
                    )
                
                subject = "Leave Balance Reminder"
                message = (
                    f"Dear {employee.full_name},\n\n"
                    f"This is a reminder of your current leave balances:\n\n"
                    f"{chr(10).join(balance_summary)}\n\n"
                    f"Please plan your leaves accordingly.\n\n"
                    f"Best regards,\n"
                    f"{company.name}"
                )
                
                send_email_task.delay(
                    subject=subject,
                    message=message,
                    recipient_list=[employee.user.email]
                )
                
                emails_sent += 1
        
        logger.info(f"Leave balance reminders sent to {emails_sent} employees")
        
        return {
            'status': 'success',
            'companies_processed': companies.count(),
            'emails_sent': emails_sent
        }
        
    except Exception as exc:
        logger.error(f"Failed to send leave balance reminders: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def send_upcoming_leave_reminder(self, days_ahead=7):
    """
    Send reminders for upcoming approved leaves.
    
    Args:
        days_ahead: Number of days ahead to check for upcoming leaves
    """
    try:
        logger.info(f"Sending reminders for leaves starting in {days_ahead} days")
        
        today = timezone.now().date()
        target_date = today + timedelta(days=days_ahead)
        
        # Get approved leaves starting on target date
        upcoming_leaves = LeaveRequest.objects.filter(
            status='approved',
            start_date=target_date
        ).select_related('employee', 'employee__user', 'leave_type', 'company')
        
        emails_sent = 0
        
        for leave_request in upcoming_leaves:
            employee = leave_request.employee
            
            if not employee.user or not employee.user.email:
                continue
            
            subject = f"Reminder: Your Leave Starts in {days_ahead} Days"
            message = (
                f"Dear {employee.full_name},\n\n"
                f"This is a reminder that your approved leave is starting soon.\n\n"
                f"Leave Type: {leave_request.leave_type.name}\n"
                f"Start Date: {leave_request.start_date}\n"
                f"End Date: {leave_request.end_date}\n"
                f"Days: {leave_request.days_requested}\n\n"
                f"Please ensure all your pending work is completed before your leave.\n\n"
                f"Best regards,\n"
                f"{leave_request.company.name}"
            )
            
            send_email_task.delay(
                subject=subject,
                message=message,
                recipient_list=[employee.user.email]
            )
            
            emails_sent += 1
        
        logger.info(f"Upcoming leave reminders sent to {emails_sent} employees")
        
        return {
            'status': 'success',
            'days_ahead': days_ahead,
            'emails_sent': emails_sent
        }
        
    except Exception as exc:
        logger.error(f"Failed to send upcoming leave reminders: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def generate_leave_report(self, company_id, start_date, end_date, report_type='summary'):
    """
    Generate leave report for a specific period.
    
    Args:
        company_id: Company UUID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        report_type: Type of report (summary, detailed, by_type)
    """
    try:
        logger.info(f"Generating {report_type} leave report for company {company_id}")
        
        company = Company.objects.get(id=company_id)
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()
        
        # Get leave requests in the period
        leave_requests = LeaveRequest.objects.filter(
            company=company,
            start_date__lte=end_date_obj,
            end_date__gte=start_date_obj
        ).select_related('employee', 'leave_type')
        
        if report_type == 'summary':
            # Generate summary report
            from django.db.models import Sum, Count
            
            summary = leave_requests.aggregate(
                total_requests=Count('id'),
                approved_requests=Count('id', filter=models.Q(status='approved')),
                rejected_requests=Count('id', filter=models.Q(status='rejected')),
                pending_requests=Count('id', filter=models.Q(status='pending')),
                total_days=Sum('days_requested', filter=models.Q(status='approved'))
            )
            
            report_data = {
                'report_type': 'summary',
                'start_date': start_date,
                'end_date': end_date,
                'company': company.name,
                'summary': summary
            }
        
        elif report_type == 'by_type':
            # Generate report by leave type
            leave_types = LeaveType.objects.filter(company=company)
            type_data = []
            
            for leave_type in leave_types:
                type_requests = leave_requests.filter(leave_type=leave_type)
                type_summary = type_requests.aggregate(
                    total_requests=Count('id'),
                    approved_requests=Count('id', filter=models.Q(status='approved')),
                    total_days=Sum('days_requested', filter=models.Q(status='approved'))
                )
                
                type_data.append({
                    'leave_type': leave_type.name,
                    **type_summary
                })
            
            report_data = {
                'report_type': 'by_type',
                'start_date': start_date,
                'end_date': end_date,
                'company': company.name,
                'leave_types': type_data
            }
        
        else:
            # Detailed report
            report_data = {
                'report_type': 'detailed',
                'start_date': start_date,
                'end_date': end_date,
                'company': company.name,
                'records': list(leave_requests.values(
                    'employee__first_name',
                    'employee__last_name',
                    'leave_type__name',
                    'start_date',
                    'end_date',
                    'days_requested',
                    'status'
                ))
            }
        
        logger.info(f"Leave report generated successfully")
        
        return {
            'status': 'success',
            'report_data': report_data
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {'status': 'error', 'error': 'Company not found'}
    
    except Exception as exc:
        logger.error(f"Failed to generate leave report: {exc}")
        raise
