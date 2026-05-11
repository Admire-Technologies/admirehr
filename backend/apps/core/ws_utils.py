"""
Utility functions for sending WebSocket messages.
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def send_dashboard_update(company_id, data):
    """
    Send dashboard metrics update to all connected clients for a company.
    
    Args:
        company_id: UUID of the company
        data: Dictionary containing dashboard metrics
    """
    channel_layer = get_channel_layer()
    group_name = f"dashboard_{company_id}"
    
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'dashboard_update',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Dashboard update sent to group {group_name}")
    except Exception as e:
        logger.error(f"Failed to send dashboard update: {str(e)}")


def send_attendance_update(company_id, data):
    """
    Send attendance update to all connected clients for a company.
    
    Args:
        company_id: UUID of the company
        data: Dictionary containing attendance event data
            {
                "employee_id": "uuid",
                "action": "check_in|check_out",
                "timestamp": "ISO datetime",
                "location": "terminal_id"
            }
    """
    channel_layer = get_channel_layer()
    group_name = f"attendance_{company_id}"
    
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'attendance_update',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Attendance update sent to group {group_name}")
    except Exception as e:
        logger.error(f"Failed to send attendance update: {str(e)}")


def send_leave_status_change(company_id, user_id, data):
    """
    Send leave status change notification.
    
    Args:
        company_id: UUID of the company
        user_id: UUID of the user (employee) to notify
        data: Dictionary containing leave request data
            {
                "request_id": "uuid",
                "status": "approved|rejected|pending",
                "employee_id": "uuid",
                "approver_id": "uuid"
            }
    """
    channel_layer = get_channel_layer()
    
    # Send to company-wide leave group
    company_group = f"leave_{company_id}"
    # Send to specific user
    user_group = f"leave_user_{user_id}"
    
    try:
        message = {
            'type': 'leave_status_change',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to both groups
        async_to_sync(channel_layer.group_send)(company_group, message)
        async_to_sync(channel_layer.group_send)(user_group, message)
        
        logger.info(f"Leave status change sent to company {company_id} and user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send leave status change: {str(e)}")


def send_notification(company_id, user_id, data, company_wide=False):
    """
    Send notification to specific user or company-wide.
    
    Args:
        company_id: UUID of the company
        user_id: UUID of the user to notify (if not company-wide)
        data: Dictionary containing notification data
        company_wide: If True, send to all users in company
    """
    channel_layer = get_channel_layer()
    
    try:
        message = {
            'type': 'notification',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if company_wide:
            # Send to all users in company
            group_name = f"company_{company_id}"
            async_to_sync(channel_layer.group_send)(group_name, message)
            logger.info(f"Company-wide notification sent to {group_name}")
        else:
            # Send to specific user
            group_name = f"user_{user_id}"
            async_to_sync(channel_layer.group_send)(group_name, message)
            logger.info(f"User notification sent to {group_name}")
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
