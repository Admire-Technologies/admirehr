# Admire HRMS API Documentation

## Overview

The Admire HRMS API is a RESTful API built with Django REST Framework. It provides comprehensive endpoints for managing employees, attendance, leave, payroll, and more.

**Base URL**: `http://localhost:8000/api/v1/` (Development)  
**Production URL**: `https://api.admire-hrms.com/api/v1/`

## Authentication

### JWT Token Authentication

All API requests require authentication using JWT (JSON Web Tokens).

#### Obtaining Tokens

**Endpoint**: `POST /api/v1/auth/login/`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "HR Manager"
  }
}
```

#### Using Tokens

Include the access token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Refreshing Tokens

**Endpoint**: `POST /api/v1/auth/refresh/`

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Rate Limiting

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **Burst limit**: 20 requests/minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
```

## API Endpoints

### Authentication

#### Login
```
POST /api/v1/auth/login/
```

#### Logout
```
POST /api/v1/auth/logout/
```

#### Refresh Token
```
POST /api/v1/auth/refresh/
```

#### Get Current User Profile
```
GET /api/v1/auth/profile/
```

### Employees

#### List Employees
```
GET /api/v1/employees/
```

**Query Parameters**:
- `search`: Search by name or employee ID
- `department`: Filter by department ID
- `status`: Filter by status (active, inactive)
- `page`: Page number for pagination
- `page_size`: Number of results per page

**Response**:
```json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/employees/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "employee_id": "EMP001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "department": {
        "id": "uuid",
        "name": "Engineering"
      },
      "position": "Software Engineer",
      "status": "active",
      "hire_date": "2023-01-15"
    }
  ]
}
```

#### Get Employee Details
```
GET /api/v1/employees/{id}/
```

#### Create Employee
```
POST /api/v1/employees/
```

**Request**:
```json
{
  "employee_id": "EMP001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "department_id": "uuid",
  "position": "Software Engineer",
  "hire_date": "2023-01-15",
  "basic_salary": 5000.00,
  "status": "active"
}
```

#### Update Employee
```
PUT /api/v1/employees/{id}/
PATCH /api/v1/employees/{id}/
```

#### Delete Employee
```
DELETE /api/v1/employees/{id}/
```

### Attendance

#### List Attendance Records
```
GET /api/v1/attendance/
```

**Query Parameters**:
- `employee`: Filter by employee ID
- `date`: Filter by specific date (YYYY-MM-DD)
- `date_from`: Start date for range
- `date_to`: End date for range
- `status`: Filter by status (present, late, absent)

**Response**:
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "employee": {
        "id": "uuid",
        "name": "John Doe",
        "employee_id": "EMP001"
      },
      "date": "2024-01-15",
      "check_in": "2024-01-15T09:00:00Z",
      "check_out": "2024-01-15T18:00:00Z",
      "working_hours": 9.0,
      "status": "present",
      "biometric_verified": true
    }
  ]
}
```

#### Check In (Biometric)
```
POST /api/v1/attendance/check-in/
```

**Request**:
```json
{
  "biometric_data": "base64_encoded_face_data",
  "terminal_id": "TERMINAL_001"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Check-in successful",
  "attendance": {
    "id": "uuid",
    "employee": {
      "id": "uuid",
      "name": "John Doe"
    },
    "check_in": "2024-01-15T09:00:00Z",
    "status": "present"
  }
}
```

#### Check Out (Biometric)
```
POST /api/v1/attendance/check-out/
```

#### Manual Attendance Entry
```
POST /api/v1/attendance/manual-entry/
```

**Request**:
```json
{
  "employee_id": "uuid",
  "date": "2024-01-15",
  "check_in": "2024-01-15T09:00:00Z",
  "check_out": "2024-01-15T18:00:00Z",
  "reason": "System was down"
}
```

#### Attendance Reports
```
GET /api/v1/attendance/reports/
```

**Query Parameters**:
- `report_type`: daily, monthly, employee
- `date_from`: Start date
- `date_to`: End date
- `employee`: Employee ID (for employee report)
- `department`: Department ID
- `format`: pdf, excel, csv

### Leave Management

#### List Leave Requests
```
GET /api/v1/leave/requests/
```

**Query Parameters**:
- `status`: pending, approved, rejected
- `employee`: Filter by employee ID
- `date_from`: Start date
- `date_to`: End date

**Response**:
```json
{
  "count": 25,
  "results": [
    {
      "id": "uuid",
      "employee": {
        "id": "uuid",
        "name": "John Doe"
      },
      "leave_type": {
        "id": "uuid",
        "name": "Annual Leave"
      },
      "start_date": "2024-02-01",
      "end_date": "2024-02-05",
      "days_requested": 5,
      "status": "pending",
      "reason": "Family vacation",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Create Leave Request
```
POST /api/v1/leave/requests/
```

**Request**:
```json
{
  "leave_type_id": "uuid",
  "start_date": "2024-02-01",
  "end_date": "2024-02-05",
  "reason": "Family vacation"
}
```

#### Approve Leave Request
```
POST /api/v1/leave/approve/{id}/
```

**Request**:
```json
{
  "comments": "Approved for vacation"
}
```

#### Reject Leave Request
```
POST /api/v1/leave/reject/{id}/
```

**Request**:
```json
{
  "comments": "Insufficient coverage during this period"
}
```

#### Get Leave Balance
```
GET /api/v1/leave/balance/
GET /api/v1/leave/balance/{employee_id}/
```

**Response**:
```json
{
  "employee": {
    "id": "uuid",
    "name": "John Doe"
  },
  "balances": [
    {
      "leave_type": "Annual Leave",
      "total_days": 20,
      "used_days": 5,
      "remaining_days": 15
    },
    {
      "leave_type": "Sick Leave",
      "total_days": 10,
      "used_days": 2,
      "remaining_days": 8
    }
  ]
}
```

### Payroll

#### List Payroll Records
```
GET /api/v1/payroll/
```

**Query Parameters**:
- `employee`: Filter by employee ID
- `period_start`: Start of payroll period
- `period_end`: End of payroll period
- `year`: Filter by year
- `month`: Filter by month

#### Generate Payroll
```
POST /api/v1/payroll/generate/
```

**Request**:
```json
{
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "employee_ids": ["uuid1", "uuid2"],  // Optional, all if not specified
  "department_id": "uuid"  // Optional
}
```

#### Get Payslip
```
GET /api/v1/payroll/slips/{id}/
```

**Response**:
```json
{
  "id": "uuid",
  "employee": {
    "id": "uuid",
    "name": "John Doe",
    "employee_id": "EMP001"
  },
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "basic_salary": 5000.00,
  "allowances": 1000.00,
  "deductions": 500.00,
  "net_salary": 5500.00,
  "components": [
    {
      "name": "Basic Salary",
      "type": "earning",
      "amount": 5000.00
    },
    {
      "name": "Housing Allowance",
      "type": "earning",
      "amount": 1000.00
    },
    {
      "name": "Tax",
      "type": "deduction",
      "amount": 500.00
    }
  ]
}
```

#### Download Payslip PDF
```
GET /api/v1/payroll/slips/{id}/pdf/
```

### Dashboard

#### Get Dashboard Metrics
```
GET /api/v1/dashboard/metrics/
```

**Query Parameters**:
- `date`: Specific date (defaults to today)

**Response**:
```json
{
  "date": "2024-01-15",
  "total_employees": 150,
  "present_count": 140,
  "late_count": 5,
  "absent_count": 5,
  "on_leave_count": 3,
  "pending_leave_requests": 8,
  "attendance_rate": 93.3
}
```

#### Get Attendance Trends
```
GET /api/v1/dashboard/attendance-trends/
```

**Query Parameters**:
- `period`: week, month, year
- `date_from`: Start date
- `date_to`: End date

### Users and Roles

#### List Users
```
GET /api/v1/users/
```

#### Create User
```
POST /api/v1/users/
```

**Request**:
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "secure_password",
  "role_id": "uuid",
  "employee_id": "uuid"
}
```

#### List Roles
```
GET /api/v1/roles/
```

#### Create Role
```
POST /api/v1/roles/
```

**Request**:
```json
{
  "name": "Department Manager",
  "permissions": [
    "view_employees",
    "edit_employees",
    "approve_leave",
    "view_attendance"
  ]
}
```

## WebSocket Events

### Connection

Connect to WebSocket at: `ws://localhost:8000/ws/`

Include JWT token in connection:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/?token=YOUR_JWT_TOKEN');
```

### Event Types

#### Attendance Update
```json
{
  "type": "attendance.update",
  "data": {
    "employee_id": "uuid",
    "employee_name": "John Doe",
    "action": "check_in",
    "timestamp": "2024-01-15T09:00:00Z"
  }
}
```

#### Leave Status Change
```json
{
  "type": "leave.status_change",
  "data": {
    "request_id": "uuid",
    "employee_name": "John Doe",
    "status": "approved",
    "approver_name": "Jane Smith"
  }
}
```

#### Dashboard Update
```json
{
  "type": "dashboard.update",
  "data": {
    "present_count": 140,
    "on_leave_count": 3,
    "pending_requests": 8
  }
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field": ["Error detail"]
    },
    "path": "/api/v1/endpoint"
  }
}
```

### Common Error Codes

- `validation_error`: Request validation failed
- `authentication_failed`: Invalid or missing authentication
- `permission_denied`: Insufficient permissions
- `not_found`: Resource not found
- `rate_limit_exceeded`: Too many requests
- `internal_server_error`: Server error

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Business logic error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Pagination

List endpoints support pagination:

**Request**:
```
GET /api/v1/employees/?page=2&page_size=20
```

**Response**:
```json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/employees/?page=3",
  "previous": "http://api.example.com/api/v1/employees/?page=1",
  "results": [...]
}
```

## Filtering and Searching

Most list endpoints support filtering and searching:

```
GET /api/v1/employees/?search=john&department=uuid&status=active
```

## Ordering

Use the `ordering` parameter to sort results:

```
GET /api/v1/employees/?ordering=-hire_date
GET /api/v1/attendance/?ordering=date,-check_in
```

Prefix with `-` for descending order.

## API Versioning

The API uses URL-based versioning:

- Current version: `v1`
- Base URL: `/api/v1/`

Include version in Accept header (optional):
```
Accept: application/json; version=v1
```

## Interactive API Documentation

Access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`

These provide:
- Complete API reference
- Try-it-out functionality
- Request/response examples
- Authentication testing

## Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login/',
    json={'email': 'user@example.com', 'password': 'password'}
)
token = response.json()['access']

# Get employees
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/employees/',
    headers=headers
)
employees = response.json()['results']
```

### JavaScript

```javascript
// Login
const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const {access} = await response.json();

// Get employees
const employeesResponse = await fetch('http://localhost:8000/api/v1/employees/', {
  headers: {'Authorization': `Bearer ${access}`}
});
const {results} = await employeesResponse.json();
```

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (not in localStorage for sensitive apps)
3. **Implement token refresh** before expiration
4. **Handle rate limits** with exponential backoff
5. **Validate input** on client side before sending
6. **Use pagination** for large datasets
7. **Implement proper error handling**
8. **Cache responses** when appropriate

## Support

For API support:
- Email: api-support@admire-hrms.com
- Documentation: https://docs.admire-hrms.com
- GitHub Issues: https://github.com/admire-hrms/issues

---

**API Version**: 1.0.0  
**Last Updated**: 2024
