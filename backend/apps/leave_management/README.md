# Leave Management Module

## Overview
The Leave Management module provides comprehensive leave application, approval, and tracking functionality for the Admire HRMS system. It supports multiple leave types, balance tracking, approval workflows, and real-time notifications.

## Features

### Core Functionality
- **Leave Types**: Define multiple leave types (Annual, Sick, etc.) with configurable days allowed
- **Leave Balance**: Track accrued, used, and pending leave days per employee
- **Leave Requests**: Submit, approve, reject, and cancel leave requests
- **Approval Workflow**: Multi-step approval process with notifications
- **Leave Calendar**: Visual representation of team leave schedules
- **Reports**: Comprehensive leave statistics and upcoming schedules

### Key Capabilities
- ✅ Real-time balance validation
- ✅ Overlap detection and prevention
- ✅ WebSocket notifications for status changes
- ✅ Multi-tenant data isolation
- ✅ Flexible approval workflows
- ✅ Comprehensive reporting

## Models

### LeaveType
Defines different types of leave available in the system.

**Fields:**
- `name`: Leave type name (e.g., "Annual Leave")
- `description`: Optional description
- `days_allowed`: Number of days allowed per year
- `is_active`: Whether this leave type is currently active
- `allow_negative_balance`: Allow requests exceeding balance
- `requires_approval`: Whether approval is required

### LeaveBalance
Tracks leave balance for each employee per leave type and year.

**Fields:**
- `employee`: Foreign key to Employee
- `leave_type`: Foreign key to LeaveType
- `year`: Year for this balance
- `accrued_days`: Total days accrued
- `used_days`: Days already used
- `pending_days`: Days in pending requests

**Calculated:**
- `available_days`: accrued - used - pending

### LeaveRequest
Represents a leave application from an employee.

**Fields:**
- `employee`: Employee requesting leave
- `leave_type`: Type of leave requested
- `start_date`: Leave start date
- `end_date`: Leave end date
- `days_requested`: Number of days requested
- `reason`: Reason for leave
- `status`: pending, approved, rejected, cancelled
- `approver`: Employee who approved/rejected
- `approved_at`: Timestamp of approval/rejection
- `rejection_reason`: Reason for rejection
- `cancelled_at`: Timestamp of cancellation
- `cancellation_reason`: Reason for cancellation

## API Endpoints

### Leave Types
```
GET    /api/v1/leave/types/           # List all leave types
POST   /api/v1/leave/types/           # Create new leave type
GET    /api/v1/leave/types/{id}/      # Get leave type details
PUT    /api/v1/leave/types/{id}/      # Update leave type
DELETE /api/v1/leave/types/{id}/      # Delete leave type
```

### Leave Balances
```
GET  /api/v1/leave/balances/                    # List all balances
GET  /api/v1/leave/balances/my_balance/         # Get current user's balance
POST /api/v1/leave/balances/initialize_balances/ # Initialize balances for all employees
```

### Leave Requests
```
GET  /api/v1/leave/requests/                    # List all requests
POST /api/v1/leave/requests/                    # Create new request
GET  /api/v1/leave/requests/{id}/               # Get request details
PUT  /api/v1/leave/requests/{id}/               # Update request
DELETE /api/v1/leave/requests/{id}/             # Delete request
GET  /api/v1/leave/requests/my_requests/        # Get current user's requests
GET  /api/v1/leave/requests/pending_approvals/  # Get pending approvals
POST /api/v1/leave/requests/{id}/approve_reject/ # Approve or reject
POST /api/v1/leave/requests/{id}/cancel/        # Cancel request
GET  /api/v1/leave/requests/calendar/           # Get leave calendar
GET  /api/v1/leave/requests/reports/            # Get leave reports
```

## Usage Examples

### Creating a Leave Request
```python
POST /api/v1/leave/requests/
{
    "leave_type": "uuid-of-leave-type",
    "start_date": "2024-12-20",
    "end_date": "2024-12-24",
    "days_requested": 5,
    "reason": "Family vacation"
}
```

### Approving a Leave Request
```python
POST /api/v1/leave/requests/{id}/approve_reject/
{
    "action": "approve"
}
```

### Rejecting a Leave Request
```python
POST /api/v1/leave/requests/{id}/approve_reject/
{
    "action": "reject",
    "rejection_reason": "Insufficient coverage during this period"
}
```

### Cancelling a Leave Request
```python
POST /api/v1/leave/requests/{id}/cancel/
{
    "cancellation_reason": "Plans changed"
}
```

### Getting Leave Calendar
```python
GET /api/v1/leave/requests/calendar/?start_date=2024-12-01&end_date=2024-12-31
```

### Getting Leave Reports
```python
GET /api/v1/leave/requests/reports/?year=2024
```

## Validation Rules

### Leave Request Validation
1. **Date Validation**
   - Start date must be in the future
   - End date must be after or equal to start date
   - No overlapping with existing approved/pending requests

2. **Balance Validation**
   - Sufficient balance required (unless `allow_negative_balance` is true)
   - Balance checked before accepting request
   - Clear error messages with available balance

3. **Status Validation**
   - Only pending requests can be approved/rejected
   - Only pending or approved requests can be cancelled
   - Rejection requires a reason

## Workflow

### Leave Application Flow
1. Employee submits leave request
2. System validates dates and balance
3. Request status set to "pending"
4. Pending days added to balance
5. Manager receives notification

### Approval Flow
1. Manager reviews pending request
2. Manager approves or rejects with reason
3. System updates request status
4. Balance updated (pending → used or released)
5. Employee receives notification via WebSocket

### Cancellation Flow
1. Employee cancels pending/approved request
2. System validates cancellation is allowed
3. Request status set to "cancelled"
4. Balance restored (if approved) or released (if pending)
5. Notifications sent

## WebSocket Events

### Leave Status Change Event
```json
{
    "type": "leave.status_change",
    "data": {
        "request_id": "uuid",
        "status": "approved|rejected|cancelled",
        "employee_id": "uuid",
        "approver_id": "uuid",
        "leave_type": "Annual Leave",
        "start_date": "2024-12-20",
        "end_date": "2024-12-24"
    },
    "timestamp": "2024-12-15T10:30:00Z"
}
```

## Testing

Run tests with:
```bash
python manage.py test apps.leave_management
```

**Test Coverage:**
- 22 tests covering all functionality
- 100% pass rate
- Tests include:
  - Model creation and validation
  - API endpoints
  - Balance calculations
  - Approval/rejection workflows
  - Validation rules
  - Edge cases

## Multi-Tenant Support

All models and queries are automatically scoped to the current user's company:
- Company field set automatically via middleware
- All queries filtered by company
- Data isolation enforced at model level
- No cross-company data access possible

## Performance Considerations

### Database Indexes
- Index on `(employee, status)` for fast filtering
- Index on `(start_date, end_date)` for date range queries
- Unique constraint on `(employee, leave_type, year, company)` for balances

### Query Optimization
- `select_related()` used for foreign key queries
- Efficient balance calculation queries
- Pagination enabled for list endpoints

## Integration

### With Employee Management
- Links to Employee model
- Uses employee's company for multi-tenancy
- Validates employee exists and is active

### With Authentication
- JWT authentication required
- Uses `request.user.employee` for current employee
- Permission checks at view level

### With WebSocket System
- Real-time notifications via Django Channels
- Uses existing WebSocket infrastructure
- Sends to user-specific and company-wide channels

## Configuration

### Leave Type Setup
1. Create leave types via admin or API
2. Set days allowed per type
3. Configure negative balance and approval settings
4. Activate/deactivate as needed

### Balance Initialization
Use the initialize_balances endpoint to set up balances for all employees:
```python
POST /api/v1/leave/balances/initialize_balances/
{
    "year": 2024
}
```

## Troubleshooting

### Common Issues

**Issue: "Insufficient leave balance" error**
- Check employee's leave balance for the year
- Verify leave type days_allowed setting
- Check if negative balance is allowed

**Issue: "Leave request overlaps with existing leave"**
- Check for existing approved/pending requests
- Verify date ranges don't overlap
- Cancel conflicting request if needed

**Issue: "Cannot apply for leave in the past"**
- Ensure start_date is in the future
- Check system date/time settings

## Future Enhancements

Planned features:
- Automatic leave accrual based on tenure
- Holiday calendar integration
- Leave carry-forward rules
- Approval delegation
- Email notifications
- Bulk operations
- Advanced reporting with charts
- Leave request attachments
