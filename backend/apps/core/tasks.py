"""
Core Celery tasks and utilities for background job processing.
"""

from celery import shared_task, Task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import traceback

logger = get_task_logger(__name__)


class CallbackTask(Task):
    """
    Base task class with callbacks for success, failure, and retry.
    Provides comprehensive error handling and logging.
    """
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {self.name} [{task_id}] succeeded with result: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            f"Task {self.name} [{task_id}] failed with exception: {exc}\n"
            f"Args: {args}\n"
            f"Kwargs: {kwargs}\n"
            f"Traceback: {einfo}"
        )
        
        # Store failure information for monitoring
        from .models import JobExecution
        try:
            JobExecution.objects.create(
                task_id=task_id,
                task_name=self.name,
                status='failed',
                error_message=str(exc),
                error_traceback=str(einfo),
                args=args,
                kwargs=kwargs
            )
        except Exception as e:
            logger.error(f"Failed to log task failure: {e}")
        
        return super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            f"Task {self.name} [{task_id}] is being retried due to: {exc}"
        )
        return super().on_retry(exc, task_id, args, kwargs, einfo)


@shared_task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60
)
def send_email_task(self, subject, message, recipient_list, html_message=None, from_email=None):
    """
    Send email asynchronously.
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        html_message: Optional HTML message
        from_email: Optional from email address
    """
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        logger.info(f"Sending email to {recipient_list}: {subject}")
        
        if html_message:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False
            )
        
        logger.info(f"Email sent successfully to {recipient_list}")
        return {
            'status': 'success',
            'recipients': recipient_list,
            'subject': subject
        }
        
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, base=CallbackTask)
def send_notification_email(self, user_id, notification_type, context):
    """
    Send notification email based on type.
    
    Args:
        user_id: User ID to send notification to
        notification_type: Type of notification (leave_approved, payslip_ready, etc.)
        context: Context data for email template
    """
    try:
        from apps.authentication.models import User
        
        user = User.objects.select_related('employee', 'company').get(id=user_id)
        
        if not user.email:
            logger.warning(f"User {user_id} has no email address")
            return {'status': 'skipped', 'reason': 'no_email'}
        
        # Email templates mapping
        templates = {
            'leave_approved': {
                'subject': 'Leave Request Approved',
                'template': 'emails/leave_approved.html'
            },
            'leave_rejected': {
                'subject': 'Leave Request Rejected',
                'template': 'emails/leave_rejected.html'
            },
            'payslip_ready': {
                'subject': 'Your Payslip is Ready',
                'template': 'emails/payslip_ready.html'
            },
            'payroll_processed': {
                'subject': 'Payroll Processed Successfully',
                'template': 'emails/payroll_processed.html'
            }
        }
        
        if notification_type not in templates:
            logger.error(f"Unknown notification type: {notification_type}")
            return {'status': 'error', 'reason': 'unknown_type'}
        
        template_config = templates[notification_type]
        context['user'] = user
        context['company'] = user.company
        
        # Render email content
        html_message = render_to_string(template_config['template'], context)
        plain_message = f"Hello {user.get_full_name()},\n\n{context.get('message', '')}"
        
        # Send email
        send_email_task.delay(
            subject=template_config['subject'],
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
        
        logger.info(f"Notification email queued for user {user_id}: {notification_type}")
        return {
            'status': 'success',
            'user_id': str(user_id),
            'notification_type': notification_type
        }
        
    except Exception as exc:
        logger.error(f"Failed to send notification email: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def cleanup_old_job_executions(self, days=30):
    """
    Clean up old job execution records.
    
    Args:
        days: Number of days to keep records (default: 30)
    """
    try:
        from .models import JobExecution
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = JobExecution.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old job execution records")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed to cleanup job executions: {exc}")
        raise


@shared_task(bind=True, base=CallbackTask)
def health_check_task(self):
    """
    Health check task to verify Celery workers are functioning.
    """
    logger.info("Health check task executed successfully")
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'worker': self.request.hostname
    }
