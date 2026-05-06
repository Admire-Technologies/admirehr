"""
WebSocket consumers for real-time functionality.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for dashboard real-time updates.
    """
    
    async def connect(self):
        self.group_name = f"dashboard_{self.scope['user'].company.id}"
        
        # Join dashboard group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave dashboard group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def dashboard_update(self, event):
        """
        Send dashboard update to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))


class AttendanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for attendance real-time updates.
    """
    
    async def connect(self):
        self.group_name = f"attendance_{self.scope['user'].company.id}"
        
        # Join attendance group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave attendance group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def attendance_update(self, event):
        """
        Send attendance update to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'attendance_update',
            'data': event['data']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for general notifications.
    """
    
    async def connect(self):
        self.user_group_name = f"user_{self.scope['user'].id}"
        self.company_group_name = f"company_{self.scope['user'].company.id}"
        
        # Join user and company groups
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.company_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave groups
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
            'data': event['data']
        }))