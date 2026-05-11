# Payroll Management System

## Overview

The Payroll Management System is a comprehensive module for processing employee salaries, generating payslips, and managing salary rules. It integrates seamlessly with the attendance and leave management systems to provide accurate salary calculations.

## Features

### 1. Flexible Salary Rules
- Define basic salary, allowances, and deductions
- Support for fixed amounts and percentage-based calculations
- Apply rules globally or to specific employees
- Employee-specific salary overrides

### 2. Automated Payroll Calculation
- Integrates with attendance records
- Considers approved leave requests
- Calculates deductions for absent days
- Handles unpaid leave scenarios

### 3. Bulk Processing
- Generate payroll for multiple employees
- Filter by department or specific employees
- Error handling and reporting
- Batch processing capabilities

### 4. Comprehensive Reporting
- Summary reports by period
- Department-wise analysis
- Detailed employee payroll records
- Export capabilities

### 5. PDF Payslip Generation
- Professional payslip design
- Company branding
- Detailed salary breakdown
- Attendance information

## API Endpoints

### Salary Rules
```
GET    /api/v1/payroll/salary-rules/           - List all salary rules
POST   /api/v1/payroll/salary-rules/           - Create a new salary rule
GET    /api/v1/payroll/salary-rules/{id}/      - Get salary rule details
PUT    /api/v1/payroll/salary-rules/{id}/      - Update salary rule
DELETE /api/v1/payroll/salary-rules/{id}/      - Delete salary rule
```

### Payroll Records
```
GET    /api/v1/payroll/records/                - List payroll records
POST   /api/v1/payroll/records/                - Create payroll record
GET    /api/v1/payroll/records/{id}/           - Get payroll details
GET    /api/v1/payroll/records/{id}/payslip/   - Get payslip data
GET    /api/v1/payroll/records/summary/        - Get payroll summary
```

### Payroll Generation
```
POST   /api/v1/payroll/generate/               - Generate payroll
POST   /api/v1/payroll/bulk-process/           - Bulk payroll processing
```

### Reports
```
GET    /api/v1/payroll/reports/                - Generate reports
GET    /api/v1/payroll/payslip/{id}/pdf/       - Download PDF payslip
```

## Usage Examples

### 1. Create Salary Rules

```python
# Create basic salary rule
POST /api/v1/payroll/salary-rules/
{
    "name": "Basic Salary",
    "rule_type": "basic",
    "calculation_method": "fixed",
    "amount": "5000.00",
    "is_active": true,
    "applies_to_all": true
}

# Create allowance
POST /api/v1/payroll/salary-rules/
{
    "name": "Housing Allowance",
    "rule_type": "allowance",
    "calculation_method": "fixed",
    "amount": "1000.00",
    "is_active": true,
    "applies_to_all": true
}

# Create percentage-based deduction
POST /api/v1/payroll/salary-rules/
{
    "name": "Tax",
    "rule_type": "deduction",
    "calculation_method": "percentage",
    "amount": "10.00",
    "is_active": true,
    "applies_to_all": true
}
```

### 2. Generate Payroll

```python
# Generate payroll for all active employees
POST /api/v1/payroll/generate/
{
    "period_start": "2024-01-01",
    "period_end": "2024-01-31"
}

# Generate payroll for specific employees
POST /api/v1/payroll/generate/
{
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "employee_ids": ["uuid1", "uuid2"]
}
```

### 3. Bulk Processing with Filtering

```python
# Process payroll for a specific department
POST /api/v1/payroll/bulk-process/
{
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "department_id": "dept-uuid"
}
```

### 4. Get Payroll Summary

```python
# Get summary for a period
GET /api/v1/payroll/records/summary/?period_start=2024-01-01&period_end=2024-01-31

# Get summary for a specific department
GET /api/v1/payroll/records/summary/?period_start=2024-01-01&period_end=2024-01-31&department_id=dept-uuid
```

### 5. Generate Reports

```python
# Summary report
GET /api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31&type=summary

# Detailed report
GET /api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31&type=detailed

# Department-wise report
GET /api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31&type=department
```

### 6. Download PDF Payslip

```python
# Download payslip as PDF
GET /api/v1/payroll/payslip/{payroll_id}/pdf/
```

## Models

### SalaryRule
Defines salary calculation rules.

**Fields:**
- `name`: Rule name
- `rule_type`: basic, allowance, or deduction
- `calculation_method`: fixed, percentage, or formula
- `amount`: Amount or percentage value
- `is_active`: Whether the rule is active
- `applies_to_all`: Apply to all employees or specific ones
- `specific_employees`: Specific employees (if not applies_to_all)

### PayrollRecord
Stores processed payroll data.

**Fields:**
- `employee`: Employee reference
- `period_start`, `period_end`: Payroll period
- `basic_salary`: Basic salary amount
- `allowances`: Total allowances
- `deductions`: Total deductions
- `gross_salary`: Gross salary (basic + allowances)
- `net_salary`: Net salary (gross - deductions)
- `working_days`: Total working days in period
- `present_days`: Days employee was present
- `leave_days`: Days on approved leave
- `absent_days`: Days absent
- `is_processed`: Processing status
- `processed_at`: Processing timestamp
- `processed_by`: User who processed
- `notes`: Additional notes
- `breakdown`: Detailed calculation breakdown (JSON)

### EmployeeSalaryStructure
Links employees to salary rules with custom overrides.

**Fields:**
- `employee`: Employee reference
- `salary_rule`: Salary rule reference
- `custom_amount`: Override amount (optional)
- `effective_from`: Start date
- `effective_to`: End date (optional)
- `is_active`: Active status

## Calculation Logic

### 1. Basic Salary
- Retrieved from active basic salary rule
- Only one basic salary rule allowed per company

### 2. Allowances
- Sum of all active allowance rules
- Fixed amounts added directly
- Percentage amounts calculated from basic salary

### 3. Deductions
- Sum of all active deduction rules
- Fixed amounts deducted directly
- Percentage amounts calculated from basic salary
- Additional deductions for:
  - Unpaid leave days
  - Absent days (not covered by leave)

### 4. Attendance Integration
- Counts present days from attendance records
- Calculates total working days based on company settings
- Determines absent days (working days - present days - leave days)

### 5. Leave Integration
- Considers approved leave requests
- Distinguishes between paid and unpaid leave
- Adjusts deductions accordingly

## Testing

The module includes comprehensive tests:
- **24 unit tests** covering models, services, and APIs
- **4 integration tests** covering complete workflows
- **Total: 28 tests - All passing ✓**

Run tests:
```bash
python manage.py test apps.payroll
```

## Dependencies

- Django REST Framework
- ReportLab (for PDF generation)
- PostgreSQL (for JSON field support)

## Multi-Tenancy

All models and queries are company-scoped:
- Automatic company assignment
- Filtered queries by company
- Data isolation between tenants

## Security

- JWT authentication required for all endpoints
- Company-scoped data access
- Audit trail for payroll processing
- Permission-based access control

## Performance Considerations

- Database indexes on frequently queried fields
- Select_related for foreign key queries
- Bulk operations for multiple employees
- Efficient calculation algorithms

## Future Enhancements

- Celery integration for background processing
- Email notifications for payslip generation
- Advanced tax calculation rules
- Overtime calculation
- Bonus and incentive management
- Bank transfer file generation
- Advanced analytics dashboards

## Support

For issues or questions, please refer to the main HRMS documentation or contact the development team.
