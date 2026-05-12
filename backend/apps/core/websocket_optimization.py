"""
WebSocket performance optimization for Django Channels
Implements connection pooling, message batching, and performance tuning
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from typing import Dict, List, Any
import logging
import time
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class WebSocketMessageBatcher:
    """
    Batches WebSocket messages to reduce network overhead
    """
    
    def __init__(self, batch_size: int = 10, flush_interval: float = 0.5):
        """
        Initialize message batcher
        
        Args:
            batch_size: Maximum number of messages per batch
            flush_interval: Maximum time to wait before flushing (seconds)
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batches = defaultdict(list)
        self.last_flush = defaultdict(float)
    
    def add_message(self, group_name: str, message: Dict):
        """
        Add message to batch
        
        Args:
            group_name: WebSocket group name
            message: Message to send
        """
        self.batches[group_name].append(message)
        
        # Flush if batch is full
        if len(self.batches[group_name]) >= self.batch_size:
            self.flush_group(group_name)
        
        # Flush if interval exceeded
        elif time.time() - self.last_flush[group_name] >= self.flush_interval:
            self.flush_group(group_name)
    
    def flush_group(self, group_name: str):
        """
        Flush all messages for a group
        
        Args:
            group_name: WebSocket group name
        """
        if not self.batches[group_name]:
            return
        
        channel_layer = get_channel_layer()
        messages = self.batches[group_name]
        
        try:
            # Send batched messages
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'batch_message',
                    'messages': messages
                }
            )
            
            logger.debug(f"Flushed {len(messages)} messages to group {group_name}")
            
        except Exception as e:
            logger.error(f"Error flushing messages to {group_name}: {str(e)}")
        
        finally:
            # Clear batch
            self.batches[group_name] = []
            self.last_flush[group_name] = time.time()
    
    def flush_all(self):
        """Flush all pending messages"""
        for group_name in list(self.batches.keys()):
            self.flush_group(group_name)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections and provides connection pooling
    """
    
    def __init__(self):
        self.connections = defaultdict(set)
        self.connection_metadata = {}
    
    def add_connection(self, group_name: str, channel_name: str, metadata: Dict = None):
        """
        Add connection to group
        
        Args:
            group_name: WebSocket group name
            channel_name: Channel name
            metadata: Optional connection metadata
        """
        self.connections[group_name].add(channel_name)
        self.connection_metadata[channel_name] = {
            'group': group_name,
            'connected_at': time.time(),
            'metadata': metadata or {}
        }
        
        logger.info(f"Connection added to {group_name}: {channel_name}")
    
    def remove_connection(self, group_name: str, channel_name: str):
        """
        Remove connection from group
        
        Args:
            group_name: WebSocket group name
            channel_name: Channel name
        """
        if channel_name in self.connections[group_name]:
            self.connections[group_name].remove(channel_name)
            
            if channel_name in self.connection_metadata:
                del self.connection_metadata[channel_name]
            
            logger.info(f"Connection removed from {group_name}: {channel_name}")
    
    def get_connection_count(self, group_name: str) -> int:
        """Get number of connections in a group"""
        return len(self.connections[group_name])
    
    def get_total_connections(self) -> int:
        """Get total number of connections"""
        return sum(len(conns) for conns in self.connections.values())
    
    def get_group_stats(self) -> Dict[str, int]:
        """Get connection statistics by group"""
        return {
            group: len(conns)
            for group, conns in self.connections.items()
        }


class WebSocketPerformanceMonitor:
    """
    Monitors WebSocket performance metrics
    """
    
    def __init__(self):
        self.message_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.latencies = defaultdict(list)
    
    def record_message(self, group_name: str, latency_ms: float = None):
        """
        Record message sent
        
        Args:
            group_name: WebSocket group name
            latency_ms: Message latency in milliseconds
        """
        self.message_counts[group_name] += 1
        
        if latency_ms is not None:
            self.latencies[group_name].append(latency_ms)
            
            # Keep only last 100 latencies
            if len(self.latencies[group_name]) > 100:
                self.latencies[group_name] = self.latencies[group_name][-100:]
    
    def record_error(self, group_name: str):
        """Record error"""
        self.error_counts[group_name] += 1
    
    def get_stats(self, group_name: str = None) -> Dict:
        """
        Get performance statistics
        
        Args:
            group_name: Optional group name to filter by
        
        Returns:
            Dictionary with performance metrics
        """
        if group_name:
            latencies = self.latencies.get(group_name, [])
            return {
                'group': group_name,
                'message_count': self.message_counts[group_name],
                'error_count': self.error_counts[group_name],
                'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
                'max_latency_ms': max(latencies) if latencies else 0,
                'min_latency_ms': min(latencies) if latencies else 0
            }
        else:
            return {
                'total_messages': sum(self.message_counts.values()),
                'total_errors': sum(self.error_counts.values()),
                'groups': list(self.message_counts.keys())
            }
    
    def reset_stats(self):
        """Reset all statistics"""
        self.message_counts.clear()
        self.error_counts.clear()
        self.latencies.clear()


# Global instances
message_batcher = WebSocketMessageBatcher()
connection_manager = WebSocketConnectionManager()
performance_monitor = WebSocketPerformanceMonitor()


def send_to_group_optimized(group_name: str, message: Dict, batch: bool = True):
    """
    Send message to WebSocket group with optimization
    
    Args:
        group_name: WebSocket group name
        message: Message to send
        batch: Whether to batch the message (default: True)
    """
    start_time = time.time()
    
    try:
        if batch:
            # Add to batch
            message_batcher.add_message(group_name, message)
        else:
            # Send immediately
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_message',
                    'message': message
                }
            )
        
        # Record performance
        latency_ms = (time.time() - start_time) * 1000
        performance_monitor.record_message(group_name, latency_ms)
        
    except Exception as e:
        logger.error(f"Error sending message to {group_name}: {str(e)}")
        performance_monitor.record_error(group_name)


def broadcast_to_company(company_id: str, event_type: str, data: Dict, batch: bool = True):
    """
    Broadcast message to all users in a company
    
    Args:
        company_id: Company ID
        event_type: Event type
        data: Event data
        batch: Whether to batch the message
    """
    group_name = f"company_{company_id}"
    message = {
        'type': event_type,
        'data': data,
        'timestamp': time.time()
    }
    
    send_to_group_optimized(group_name, message, batch=batch)


def broadcast_dashboard_update(company_id: str, metrics: Dict):
    """
    Broadcast dashboard metrics update
    
    Args:
        company_id: Company ID
        metrics: Dashboard metrics
    """
    broadcast_to_company(
        company_id,
        'dashboard.update',
        metrics,
        batch=True  # Dashboard updates can be batched
    )


def broadcast_attendance_update(company_id: str, attendance_data: Dict):
    """
    Broadcast attendance update
    
    Args:
        company_id: Company ID
        attendance_data: Attendance record data
    """
    broadcast_to_company(
        company_id,
        'attendance.update',
        attendance_data,
        batch=False  # Attendance updates should be immediate
    )


def broadcast_leave_status_change(company_id: str, leave_data: Dict):
    """
    Broadcast leave status change
    
    Args:
        company_id: Company ID
        leave_data: Leave request data
    """
    broadcast_to_company(
        company_id,
        'leave.status_change',
        leave_data,
        batch=False  # Leave status changes should be immediate
    )


def get_websocket_stats() -> Dict:
    """
    Get comprehensive WebSocket statistics
    
    Returns:
        Dictionary with connection and performance stats
    """
    return {
        'connections': {
            'total': connection_manager.get_total_connections(),
            'by_group': connection_manager.get_group_stats()
        },
        'performance': performance_monitor.get_stats(),
        'batching': {
            'pending_batches': len(message_batcher.batches),
            'batch_size': message_batcher.batch_size,
            'flush_interval': message_batcher.flush_interval
        }
    }
