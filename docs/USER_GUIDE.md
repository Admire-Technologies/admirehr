# Admire HRMS User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Employee Management](#employee-management)
4. [Attendance Management](#attendance-management)
5. [Leave Management](#leave-management)
6. [Payroll Management](#payroll-management)
7. [Dashboard and Reports](#dashboard-and-reports)
8. [User Administration](#user-administration)
9. [Troubleshooting](#troubleshooting)

## Introduction

Admire HRMS is a comprehensive Human Resource Management System designed to streamline HR operations for organizations of all sizes. The system provides:

- **Employee Management**: Maintain comprehensive employee records
- **Biometric Attendance**: Track attendance using face recognition
- **Leave Management**: Handle leave requests and approvals
- **Payroll Processing**: Automate salary calculations and payslip generation
- **Real-time Dashboard**: Monitor HR metrics in real-time
- **Role-Based Access Control**: Secure access based on user roles

## Getting Started

### Logging In

1. Navigate to the Admire HRMS login page
2. Enter your email address and password
3. Click "Login" to access the system

**First-time users**: Contact your system administrator to receive your login credentials.

### Dashboard Overview

After logging in, you'll see the main dashboard with:

- **Present Employees**: Number of employees currently checked in
- **On Leave**: Employees on approved leave today
- **Pending Requests**: Leave requests awaiting approval
- **Attendance Chart**: Visual representation of attendance trends
- **Recent Activities**: Latest system activities

The dashboard updates in real-time as attendance and leave data changes.

## Employee Management

### Viewing Employees

1. Click **Employees** in the main navigation
2. View the list of all employees with:
   - Employee ID
   - Name
   - Department
   - Position
   - Status (Active/Inactive)

### Searching and Filtering

- **Search**: Use the search box to find employees by name or ID
- **Filter by Department**: Select a department from the dropdown
- **Filter by Status**: Choose Active or Inactive employees

### Adding a New Employee

1. Click the **Add Employee** button
2. Fill in the required information:
   - **Personal Information**: Name, date of birth, gender, contact details
   - **Professional Information**: Employee ID, department, position, hire date
   - **Salary Information**: Basic salary, allowances
3. Click **Save** to create the employee record

### Editing Employee Information

1. Click on an employee name to view their profile
2. Click the **Edit** button
3. Update the necessary information
4. Click **Save Changes**

### Registering Biometric Data

For attendance tracking, employees need to register their biometric data:

1. Go to the employee's profile
2. Click **Register Biometric**
3. Follow the on-screen instructions to capture facial data
4. Confirm the registration

**Note**: Biometric registration requires access to the attendance terminal.

## Attendance Management

### Checking In/Out

**Using the Attendance Terminal**:

1. Approach the attendance terminal
2. Look at the camera for face recognition
3. Wait for verification (usually 1-2 seconds)
4. Confirmation message will appear on screen

**Manual Check-in** (for administrators):

1. Go to **Attendance** > **Manual Entry**
2. Select the employee
3. Enter check-in/check-out time
4. Add a reason for manual entry
5. Click **Submit**

### Viewing Attendance Records

1. Navigate to **Attendance** > **Records**
2. Select date range
3. Filter by employee or department
4. View attendance details:
   - Check-in time
   - Check-out time
   - Working hours
   - Status (Present, Late, Absent)

### Attendance Reports

1. Go to **Attendance** > **Reports**
2. Select report type:
   - Daily Attendance Summary
   - Monthly Attendance Report
   - Employee Attendance History
   - Late Arrivals Report
3. Choose date range and filters
4. Click **Generate Report**
5. Export as PDF or Excel

### Attendance Policies

The system automatically applies attendance policies:

- **Late Arrival**: Check-in after scheduled start time
- **Early Departure**: Check-out before scheduled end time
- **Overtime**: Working hours beyond scheduled time
- **Absent**: No check-in record for the day

## Leave Management

### Applying for Leave

1. Navigate to **Leave** > **Apply Leave**
2. Select leave type (Annual, Sick, Casual, etc.)
3. Choose start and end dates
4. View your available leave balance
5. Enter reason for leave
6. Click **Submit Request**

**Note**: The system will validate your leave balance before submission.

### Viewing Leave Balance

1. Go to **Leave** > **My Balance**
2. View available days for each leave type
3. See leave history and upcoming leaves

### Checking Leave Status

1. Navigate to **Leave** > **My Requests**
2. View all your leave requests with status:
   - **Pending**: Awaiting approval
   - **Approved**: Leave has been approved
   - **Rejected**: Leave request was denied

### Approving Leave Requests (Managers)

1. Go to **Leave** > **Pending Approvals**
2. Review leave request details
3. Check employee's leave balance
4. Click **Approve** or **Reject**
5. Add comments if necessary

**Real-time Notifications**: You'll receive instant notifications when:
- Your leave request is approved/rejected
- A team member applies for leave (managers)
- Leave balance is updated

## Payroll Management

### Viewing Payslips

1. Navigate to **Payroll** > **My Payslips**
2. Select the month/year
3. View payslip details:
   - Basic Salary
   - Allowances
   - Deductions
   - Net Salary
4. Download PDF copy

### Salary Components

Your payslip includes:

- **Basic Salary**: Base monthly salary
- **Allowances**: Housing, transport, meal allowances
- **Deductions**: Tax, insurance, loan repayments
- **Attendance-based**: Deductions for absences, overtime pay
- **Leave-based**: Deductions for unpaid leave

### Payroll Processing (HR Administrators)

1. Go to **Payroll** > **Process Payroll**
2. Select the month/year
3. Review attendance and leave data
4. Click **Calculate Payroll**
5. Review calculated salaries
6. Click **Generate Payslips**
7. Approve and finalize payroll

**Bulk Processing**: Process payroll for all employees at once or by department.

## Dashboard and Reports

### Dashboard Widgets

The dashboard displays real-time metrics:

- **Employee Count**: Total active employees
- **Today's Attendance**: Present, late, and absent counts
- **Leave Summary**: Employees on leave today
- **Pending Actions**: Leave requests and other approvals

### Generating Reports

1. Navigate to **Reports**
2. Select report category:
   - Employee Reports
   - Attendance Reports
   - Leave Reports
   - Payroll Reports
3. Choose specific report type
4. Set filters and date ranges
5. Click **Generate**
6. Export in desired format (PDF, Excel, CSV)

### Scheduled Reports

Set up automatic report generation:

1. Go to **Reports** > **Scheduled Reports**
2. Click **Create Schedule**
3. Select report type and frequency
4. Choose recipients
5. Set delivery time
6. Click **Save Schedule**

## User Administration

### Managing Users (Administrators)

1. Navigate to **Administration** > **Users**
2. View all user accounts
3. Create new users:
   - Click **Add User**
   - Enter user details
   - Assign role and permissions
   - Link to employee record
4. Edit or deactivate users as needed

### Role Management

1. Go to **Administration** > **Roles**
2. View existing roles and permissions
3. Create custom roles:
   - Click **Create Role**
   - Enter role name
   - Select permissions for each module
   - Click **Save**

### Permission Levels

- **View**: Read-only access
- **Create**: Can add new records
- **Edit**: Can modify existing records
- **Delete**: Can remove records
- **Approve**: Can approve requests (leave, attendance corrections)

### Company Settings

1. Navigate to **Administration** > **Settings**
2. Configure:
   - Working hours and schedules
   - Leave policies and balances
   - Salary rules and components
   - Attendance policies
   - Email notifications

## Troubleshooting

### Common Issues

**Cannot Log In**
- Verify your email and password
- Check if your account is active
- Contact your administrator if locked out

**Biometric Recognition Fails**
- Ensure good lighting conditions
- Look directly at the camera
- Remove glasses or face coverings if possible
- Contact HR to re-register biometric data

**Leave Request Not Submitting**
- Check if you have sufficient leave balance
- Verify date range is valid
- Ensure no overlapping leave requests
- Check for blackout dates

**Payslip Not Available**
- Verify payroll has been processed for that month
- Check if you were employed during that period
- Contact HR department

### Getting Help

**In-App Support**:
- Click the **Help** icon in the top navigation
- Search the knowledge base
- Submit a support ticket

**Contact Support**:
- Email: support@admire-hrms.com
- Phone: [Your support number]
- Hours: Monday-Friday, 9 AM - 5 PM

### Best Practices

1. **Keep Information Updated**: Regularly update your contact information
2. **Check Dashboard Daily**: Stay informed about pending actions
3. **Apply Leave in Advance**: Submit leave requests early for better planning
4. **Review Payslips**: Check your payslip each month for accuracy
5. **Report Issues Promptly**: Contact support immediately if you notice discrepancies

## Mobile Access

Admire HRMS is fully responsive and works on mobile devices:

- Access via mobile browser
- All features available on mobile
- Optimized interface for smaller screens
- Touch-friendly controls

## Security Tips

1. **Strong Passwords**: Use complex passwords with letters, numbers, and symbols
2. **Don't Share Credentials**: Keep your login information private
3. **Log Out**: Always log out when using shared computers
4. **Report Suspicious Activity**: Contact IT immediately if you notice unusual activity

## Updates and New Features

The system is regularly updated with new features and improvements. Check the **What's New** section in the dashboard for:

- New feature announcements
- System updates
- Policy changes
- Training materials

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**For Technical Support**: support@admire-hrms.com
