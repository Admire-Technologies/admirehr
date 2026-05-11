"""
WebSocket utility functions for sending dashboard updates.
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .services import DashboardMetricsService


def send_dashboard_update(company):
    """
    Send real-time dashboard metrics update to all connected clients for a company.
    """
    channel_layer = get_channel_layer()
    service = DashboardMetricsService(company)
    metrics = service.get_real_time_metrics()
    
    group_name = f"dashboard_{company.id}"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'dashboard_update',
            'data': metrics,
            'timestamp': timezone.now().isoformat()
        }
    )


def send_attendance_update(company, employee_id, action, timestamp):
    """
    Send attendance update and trigger dashboard refresh.
    """
    # Send attendance-specific update
    channel_layer = get_channel_layer()
    attendance_group = f"attendance_{company.id}"
    
    async_to_sync(channel_layer.group_send)(
        attendance_group,
        {
            'type': 'attendance_update',
            'data': {
                'employee_id': str(employee_id),
                'action': action,
                'timestamp': timestamp.isoformat()
            },
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # Also update dashboard metrics
    send_dashboard_update(company)
