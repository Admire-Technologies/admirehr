"""
WebSocket URL routing for the HRMS application.
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/dashboard/', consumers.DashboardConsumer.as_asgi()),
    path('ws/attendance/', consumers.AttendanceConsumer.as_asgi()),
    path('ws/leave/', consumers.LeaveConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]