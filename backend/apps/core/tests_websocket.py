"""
Tests for WebSocket functionality.
"""

import json
import pytest
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken
from apps.core.models import Company
from apps.core.routing import websocket_urlpatterns
from apps.core.ws_auth import JWTAuthMiddlewareStack
from apps.core.ws_utils import (
    send_dashboard_update,
    send_attendance_update,
    send_leave_status_change,
    send_notification,
)
from apps.authentication.models import Role, Permission

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestWebSocketAuthentication:
    """Test WebSocket authentication and authorization."""

    async def test_connection_without_token(self):
        """Test that connection without token is rejected."""
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(application, "/ws/dashboard/")
        connected, _ = await communicator.connect()
        
        # Should be rejected
        assert not connected

    async def test_connection_with_invalid_token(self):
        """Test that connection with invalid token is rejected."""
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            "/ws/dashboard/?token=invalid_token"
        )
        connected, _ = await communicator.connect()
        
        # Should be rejected
        assert not connected

    async def test_connection_with_valid_token(self):
        """Test that connection with valid token is accepted."""
        # Create test company and user
        company = await self._create_company()
        user = await self._create_user(company)
        
        # Generate JWT token
        token = str(AccessToken.for_user(user))
        
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/dashboard/?token={token}"
        )
        connected, _ = await communicator.connect()
        
        # Should be accepted
        assert connected
        
        await communicator.disconnect()

    @staticmethod
    async def _create_company():
        """Helper to create test company."""
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def create():
            return Company.objects.create(
                name="Test Company",
                code="TEST001"
            )
        
        return await create()

    @staticmethod
    async def _create_user(company):
        """Helper to create test user."""
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def create():
            # Create role
            role = Role.objects.create(
                name="Test Role",
                company=company
            )
            
            # Create user
            user = User.objects.create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                company=company,
                role=role
            )
            return user
        
        return await create()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestDashboardConsumer:
    """Test dashboard WebSocket consumer."""

    async def test_dashboard_receives_updates(self):
        """Test that dashboard consumer receives metrics updates."""
        # Create test company and user
        company = await TestWebSocketAuthentication._create_company()
        user = await TestWebSocketAuthentication._create_user(company)
        token = str(AccessToken.for_user(user))
        
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/dashboard/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send dashboard update
        test_data = {
            'present_count': 150,
            'on_leave_count': 5,
            'pending_requests': 3,
        }
        
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def send_update():
            send_dashboard_update(company.id, test_data)
        
        await send_update()
        
        # Receive message
        response = await communicator.receive_json_from(timeout=5)
        
        assert response['type'] == 'dashboard.metrics_update'
        assert response['data'] == test_data
        assert 'timestamp' in response
        
        await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestAttendanceConsumer:
    """Test attendance WebSocket consumer."""

    async def test_attendance_receives_updates(self):
        """Test that attendance consumer receives check-in/out updates."""
        # Create test company and user
        company = await TestWebSocketAuthentication._create_company()
        user = await TestWebSocketAuthentication._create_user(company)
        token = str(AccessToken.for_user(user))
        
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/attendance/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send attendance update
        test_data = {
            'employee_id': str(user.id),
            'action': 'check_in',
            'timestamp': '2024-01-15T09:00:00Z',
            'location': 'terminal_001',
        }
        
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def send_update():
            send_attendance_update(company.id, test_data)
        
        await send_update()
        
        # Receive message
        response = await communicator.receive_json_from(timeout=5)
        
        assert response['type'] == 'attendance.update'
        assert response['data'] == test_data
        assert 'timestamp' in response
        
        await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestLeaveConsumer:
    """Test leave WebSocket consumer."""

    async def test_leave_receives_status_changes(self):
        """Test that leave consumer receives status change updates."""
        # Create test company and user
        company = await TestWebSocketAuthentication._create_company()
        user = await TestWebSocketAuthentication._create_user(company)
        token = str(AccessToken.for_user(user))
        
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/leave/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send leave status change
        test_data = {
            'request_id': 'test-request-id',
            'status': 'approved',
            'employee_id': str(user.id),
            'approver_id': str(user.id),
        }
        
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def send_update():
            send_leave_status_change(company.id, user.id, test_data)
        
        await send_update()
        
        # Receive message
        response = await communicator.receive_json_from(timeout=5)
        
        assert response['type'] == 'leave.status_change'
        assert response['data'] == test_data
        assert 'timestamp' in response
        
        await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestNotificationConsumer:
    """Test notification WebSocket consumer."""

    async def test_notification_receives_user_notifications(self):
        """Test that notification consumer receives user-specific notifications."""
        # Create test company and user
        company = await TestWebSocketAuthentication._create_company()
        user = await TestWebSocketAuthentication._create_user(company)
        token = str(AccessToken.for_user(user))
        
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send user notification
        test_data = {
            'id': 'notif-001',
            'title': 'Test Notification',
            'message': 'This is a test notification',
            'type': 'info',
        }
        
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def send_update():
            send_notification(company.id, user.id, test_data, company_wide=False)
        
        await send_update()
        
        # Receive message
        response = await communicator.receive_json_from(timeout=5)
        
        assert response['type'] == 'notification'
        assert response['data'] == test_data
        assert 'timestamp' in response
        
        await communicator.disconnect()

    async def test_notification_receives_company_wide_notifications(self):
        """Test that notification consumer receives company-wide notifications."""
        # Create test company and user
        company = await TestWebSocketAuthentication._create_company()
        user = await TestWebSocketAuthentication._create_user(company)
        token = str(AccessToken.for_user(user))
        
        application = JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send company-wide notification
        test_data = {
            'id': 'notif-002',
            'title': 'Company Announcement',
            'message': 'This is a company-wide announcement',
            'type': 'info',
        }
        
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def send_update():
            send_notification(company.id, user.id, test_data, company_wide=True)
        
        await send_update()
        
        # Receive message
        response = await communicator.receive_json_from(timeout=5)
        
        assert response['type'] == 'notification'
        assert response['data'] == test_data
        assert 'timestamp' in response
        
        await communicator.disconnect()


class TestWebSocketUtils(TestCase):
    """Test WebSocket utility functions."""

    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.role = Role.objects.create(
            name="Test Role",
            company=self.company
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            company=self.company,
            role=self.role
        )

    def test_send_dashboard_update(self):
        """Test sending dashboard update doesn't raise errors."""
        data = {
            'present_count': 100,
            'on_leave_count': 5,
            'pending_requests': 2,
        }
        
        # Should not raise any exceptions
        send_dashboard_update(self.company.id, data)

    def test_send_attendance_update(self):
        """Test sending attendance update doesn't raise errors."""
        data = {
            'employee_id': str(self.user.id),
            'action': 'check_in',
            'timestamp': '2024-01-15T09:00:00Z',
            'location': 'terminal_001',
        }
        
        # Should not raise any exceptions
        send_attendance_update(self.company.id, data)

    def test_send_leave_status_change(self):
        """Test sending leave status change doesn't raise errors."""
        data = {
            'request_id': 'test-request-id',
            'status': 'approved',
            'employee_id': str(self.user.id),
            'approver_id': str(self.user.id),
        }
        
        # Should not raise any exceptions
        send_leave_status_change(self.company.id, self.user.id, data)

    def test_send_notification(self):
        """Test sending notification doesn't raise errors."""
        data = {
            'id': 'notif-001',
            'title': 'Test Notification',
            'message': 'This is a test',
            'type': 'info',
        }
        
        # Should not raise any exceptions
        send_notification(self.company.id, self.user.id, data, company_wide=False)
        send_notification(self.company.id, self.user.id, data, company_wide=True)
