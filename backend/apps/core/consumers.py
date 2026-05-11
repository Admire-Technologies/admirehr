"""
WebSocket consumers for real-time functionality.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class BaseAuthenticatedConsumer(AsyncWebsocketConsumer):
    """
    Base consumer with authentication and authorization.
    """
    
    async def connect(self):
        """
        Handle WebSocket connection with authentication.
        """
        # Check if user is authenticated
        if isinstance(self.scope.get('user'), AnonymousUser) or not self.scope.get('user'):
            logger.warning("Unauthenticated WebSocket connection attempt")
            await self.close(code=4001)
            return
        
        # Check if user has company
        if not hasattr(self.scope['user'], 'company') or not self.scope['user'].company:
            logger.warning(f"User {self.scope['user'].id} has no company")
            await self.close(code=4003)
            return
        
        # Perform consumer-specific connection logic
        await self.on_connect()
        
        # Accept the connection
        await self.accept()
        logger.info(f"WebSocket connected: {self.__class__.__name__} for user {self.scope['user'].id}")
    
    async def on_connect(self):
        """
        Override this method in subclasses for specific connection logic.
        """
        pass
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        await self.on_disconnect(close_code)
        logger.info(f"WebSocket disconnected: {self.__class__.__name__} with code {close_code}")
    
    async def on_disconnect(self, close_code):
        """
        Override this method in subclasses for specific disconnection logic.
        """
        pass
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        """
        try:
            data = json.loads(text_data)
            await self.handle_message(data)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_error("Internal server error")
    
    async def handle_message(self, data):
        """
        Override this method in subclasses to handle specific messages.
        """
        pass
    
    async def send_error(self, message):
        """
        Send error message to client.
        """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))


class DashboardConsumer(BaseAuthenticatedConsumer):
    """
    WebSocket consumer for dashboard real-time updates.
    """
    
    async def on_connect(self):
        """
        Join dashboard group for company.
        """
        self.company_id = str(self.scope['user'].company.id)
        self.group_name = f"dashboard_{self.company_id}"
        
        # Join dashboard group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def on_disconnect(self, close_code):
        """
        Leave dashboard group.
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def dashboard_update(self, event):
        """
        Send dashboard update to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'dashboard.metrics_update',
            'data': event['data'],
            'timestamp': event.get('timestamp')
        }))


class AttendanceConsumer(BaseAuthenticatedConsumer):
    """
    WebSocket consumer for attendance real-time updates.
    """
    
    async def on_connect(self):
        """
        Join attendance group for company.
        """
        self.company_id = str(self.scope['user'].company.id)
        self.group_name = f"attendance_{self.company_id}"
        
        # Join attendance group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def on_disconnect(self, close_code):
        """
        Leave attendance group.
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def attendance_update(self, event):
        """
        Send attendance update to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'attendance.update',
            'data': event['data'],
            'timestamp': event.get('timestamp')
        }))


class NotificationConsumer(BaseAuthenticatedConsumer):
    """
    WebSocket consumer for general notifications.
    """
    
    async def on_connect(self):
        """
        Join user and company notification groups.
        """
        self.user_id = str(self.scope['user'].id)
        self.company_id = str(self.scope['user'].company.id)
        self.user_group_name = f"user_{self.user_id}"
        self.company_group_name = f"company_{self.company_id}"
        
        # Join user and company groups
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.company_group_name,
            self.channel_name
        )

    async def on_disconnect(self, close_code):
        """
        Leave notification groups.
        """
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.company_group_name,
            self.channel_name
        )

    async def notification(self, event):
        """
        Send notification to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data'],
            'timestamp': event.get('timestamp')
        }))


class LeaveConsumer(BaseAuthenticatedConsumer):
    """
    WebSocket consumer for leave request updates.
    """
    
    async def on_connect(self):
        """
        Join leave group for company.
        """
        self.company_id = str(self.scope['user'].company.id)
        self.user_id = str(self.scope['user'].id)
        self.company_group_name = f"leave_{self.company_id}"
        self.user_group_name = f"leave_user_{self.user_id}"
        
        # Join company and user leave groups
        await self.channel_layer.group_add(
            self.company_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

    async def on_disconnect(self, close_code):
        """
        Leave leave groups.
        """
        await self.channel_layer.group_discard(
            self.company_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def leave_status_change(self, event):
        """
        Send leave status change to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'leave.status_change',
            'data': event['data'],
            'timestamp': event.get('timestamp')
        }))