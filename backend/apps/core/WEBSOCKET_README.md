# WebSocket Infrastructure Documentation

## Overview

The Admire HRMS WebSocket infrastructure provides real-time updates for attendance, leave requests, dashboard metrics, and notifications. It uses Django Channels with Redis as the channel layer backend and JWT authentication for secure connections.

## Architecture

### Backend Components

1. **Consumers** (`apps/core/consumers.py`)
   - `BaseAuthenticatedConsumer`: Base class with authentication and authorization
   - `DashboardConsumer`: Real-time dashboard metrics updates
   - `AttendanceConsumer`: Attendance check-in/out updates
   - `LeaveConsumer`: Leave request status changes
   - `NotificationConsumer`: General notifications

2. **Authentication Middleware** (`apps/core/ws_auth.py`)
   - `JWTAuthMiddleware`: Authenticates WebSocket connections using JWT tokens
   - Validates tokens and loads user with company and role information

3. **Utility Functions** (`apps/core/ws_utils.py`)
   - `send_dashboard_update()`: Send dashboard metrics to all connected clients
   - `send_attendance_update()`: Send attendance events
   - `send_leave_status_change()`: Send leave status changes
   - `send_notification()`: Send notifications (user-specific or company-wide)

4. **Routing** (`apps/core/routing.py`)
   - WebSocket URL patterns for different endpoints

### Frontend Components

1. **WebSocket Client** (`frontend/src/lib/websocket.ts`)
   - `WebSocketClient`: Core WebSocket client with reconnection logic
   - Automatic reconnection with exponential backoff
   - Event subscription system
   - Connection state management

2. **React Context** (`frontend/src/contexts/WebSocketContext.tsx`)
   - `WebSocketProvider`: Context provider for WebSocket connections
   - `useWebSocket()`: Hook to access WebSocket context
   - `useWebSocketEvent()`: Hook to subscribe to specific events
   - Specialized hooks: `useAttendanceUpdates()`, `useLeaveStatusChanges()`, etc.

## WebSocket Endpoints

### Available Endpoints

- `ws://host/ws/dashboard/?token=<jwt_token>` - Dashboard metrics
- `ws://host/ws/attendance/?token=<jwt_token>` - Attendance updates
- `ws://host/ws/leave/?token=<jwt_token>` - Leave status changes
- `ws://host/ws/notifications/?token=<jwt_token>` - Notifications

### Authentication

All WebSocket connections require a valid JWT token passed as a query parameter:

```
ws://localhost:8000/ws/dashboard/?token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Close Codes

- `1000`: Normal closure
- `4001`: Authentication failed (invalid or missing token)
- `4003`: Authorization failed (user has no company)

## Event Types and Data Structures

### Attendance Update

```json
{
  "type": "attendance.update",
  "data": {
    "employee_id": "uuid",
    "action": "check_in|check_out",
    "timestamp": "2024-01-15T09:00:00Z",
    "location": "terminal_001"
  },
  "timestamp": "2024-01-15T09:00:01Z"
}
```

### Leave Status Change

```json
{
  "type": "leave.status_change",
  "data": {
    "request_id": "uuid",
    "status": "approved|rejected|pending",
    "employee_id": "uuid",
    "approver_id": "uuid"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Dashboard Metrics Update

```json
{
  "type": "dashboard.metrics_update",
  "data": {
    "present_count": 150,
    "on_leave_count": 5,
    "pending_requests": 3,
    "timestamp": "2024-01-15T09:00:00Z"
  },
  "timestamp": "2024-01-15T09:00:01Z"
}
```

### Notification

```json
{
  "type": "notification",
  "data": {
    "id": "notif-001",
    "title": "Leave Request Approved",
    "message": "Your leave request has been approved",
    "type": "success"
  },
  "timestamp": "2024-01-15T11:00:00Z"
}
```

## Usage Examples

### Backend: Sending Updates

```python
from apps.core.ws_utils import (
    send_attendance_update,
    send_leave_status_change,
    send_dashboard_update,
    send_notification
)

# Send attendance update
def process_attendance_checkin(employee, company):
    # ... process check-in logic ...
    
    send_attendance_update(company.id, {
        'employee_id': str(employee.id),
        'action': 'check_in',
        'timestamp': timezone.now().isoformat(),
        'location': 'terminal_001'
    })

# Send leave status change
def approve_leave_request(leave_request, approver):
    leave_request.status = 'approved'
    leave_request.approver = approver
    leave_request.save()
    
    send_leave_status_change(
        leave_request.company.id,
        leave_request.employee.user.id,
        {
            'request_id': str(leave_request.id),
            'status': 'approved',
            'employee_id': str(leave_request.employee.id),
            'approver_id': str(approver.id)
        }
    )

# Send dashboard update
def update_dashboard_metrics(company):
    metrics = calculate_dashboard_metrics(company)
    
    send_dashboard_update(company.id, {
        'present_count': metrics['present'],
        'on_leave_count': metrics['on_leave'],
        'pending_requests': metrics['pending'],
        'timestamp': timezone.now().isoformat()
    })

# Send notification
def notify_user(user, title, message):
    send_notification(
        user.company.id,
        user.id,
        {
            'id': str(uuid.uuid4()),
            'title': title,
            'message': message,
            'type': 'info'
        },
        company_wide=False
    )
```

### Frontend: Connecting and Subscribing

```typescript
import { useEffect } from 'react';
import { useWebSocket, useAttendanceUpdates } from '@/contexts/WebSocketContext';

function MyComponent() {
  const { connect, disconnect, isConnected } = useWebSocket();

  // Connect on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      connect(token);
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Subscribe to attendance updates
  useAttendanceUpdates((data) => {
    console.log('Attendance update:', data);
    // Update UI with new attendance data
  });

  return (
    <div>
      <p>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</p>
    </div>
  );
}
```

### Frontend: Manual Event Subscription

```typescript
import { useWebSocketEvent } from '@/contexts/WebSocketContext';

function DashboardComponent() {
  const [metrics, setMetrics] = useState(null);

  // Subscribe to dashboard metrics
  useWebSocketEvent(
    'dashboard',
    'dashboard.metrics_update',
    (data) => {
      setMetrics(data);
    }
  );

  return (
    <div>
      {metrics && (
        <div>
          <p>Present: {metrics.present_count}</p>
          <p>On Leave: {metrics.on_leave_count}</p>
          <p>Pending: {metrics.pending_requests}</p>
        </div>
      )}
    </div>
  );
}
```

## Testing

### Backend Tests

Run WebSocket tests:

```bash
cd backend
pytest apps/core/tests_websocket.py -v
```

Tests cover:
- Authentication and authorization
- Message sending and receiving
- Consumer functionality
- Utility functions

### Frontend Tests

Run WebSocket client tests:

```bash
cd frontend
npm test -- websocket.test.ts
```

Tests cover:
- Connection and disconnection
- Event subscription and unsubscription
- Reconnection logic
- Error handling

## Configuration

### Backend Configuration

In `settings.py`:

```python
# Redis configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# ASGI application
ASGI_APPLICATION = 'admire_hrms.asgi.application'
```

### Frontend Configuration

In `.env.local`:

```
NEXT_PUBLIC_WS_URL=localhost:8000
```

For production with HTTPS:

```
NEXT_PUBLIC_WS_URL=your-domain.com
```

## Deployment Considerations

### Redis Setup

Ensure Redis is running and accessible:

```bash
# Local development
redis-server

# Docker
docker run -d -p 6379:6379 redis:latest
```

### ASGI Server

Use Daphne or Uvicorn for production:

```bash
# Daphne
daphne -b 0.0.0.0 -p 8000 admire_hrms.asgi:application

# Uvicorn
uvicorn admire_hrms.asgi:application --host 0.0.0.0 --port 8000
```

### Nginx Configuration

For WebSocket support in Nginx:

```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Troubleshooting

### Connection Issues

1. **Token not valid**: Ensure JWT token is not expired
2. **CORS issues**: Check CORS settings in Django
3. **Redis not running**: Verify Redis is accessible
4. **Port conflicts**: Ensure WebSocket port is not blocked

### Debugging

Enable debug logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.core.consumers': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'apps.core.ws_auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

Frontend debugging:

```typescript
// Enable verbose logging
const client = new WebSocketClient('dashboard');
client.connect(token);

// Monitor connection state
client.onConnectionStateChange((connected) => {
  console.log('Connection state:', connected);
});
```

## Performance Optimization

### Backend

1. **Use Redis connection pooling**
2. **Implement message batching for high-frequency updates**
3. **Use database connection pooling**
4. **Consider horizontal scaling with multiple Daphne workers**

### Frontend

1. **Debounce high-frequency updates**
2. **Unsubscribe from events when components unmount**
3. **Use React.memo for components receiving WebSocket updates**
4. **Implement virtual scrolling for large lists**

## Security Best Practices

1. **Always validate JWT tokens on connection**
2. **Implement rate limiting for WebSocket connections**
3. **Validate all incoming messages**
4. **Use WSS (WebSocket Secure) in production**
5. **Implement proper error handling to avoid information leakage**
6. **Log security events (failed auth, suspicious activity)**
