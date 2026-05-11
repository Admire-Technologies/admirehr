# Employee Management Module

This module handles employee management, organizational structure (departments and branches), and related functionality for the Admire HRMS system.

## Models

### Branch
Represents physical locations or branches of the organization with hierarchical support.

**Fields:**
- `name`: Branch name
- `code`: Unique branch code
- `address`: Physical address
- `phone`: Contact phone number
- `email`: Contact email
- `parent`: Parent branch (for hierarchy)
- `city`, `state`, `country`, `postal_code`: Location details
- `is_active`: Active status

**Properties:**
- `employee_count`: Number of active employees in the branch
- `full_address`: Complete formatted address

### Department
Represents organizational departments with hierarchical support.

**Fields:**
- `name`: Department name
- `description`: Department description
- `parent`: Parent department (for hierarchy)
- `is_active`: Active status

### Employee
Represents employees in the organization.

**Fields:**
- `employee_id`: Unique employee identifier
- `first_name`, `last_name`: Employee name
- `email`, `phone`: Contact information
- `department`: Associated department (required)
- `branch`: Associated branch (optional)
- `position`: Job position
- `hire_date`: Date of hire
- `status`: Employment status (active, inactive, terminated)
- `biometric_data`: Biometric data for attendance
- Personal information fields

## API Endpoints

### Branches
- `GET /api/v1/branches/` - List all branches
- `POST /api/v1/branches/` - Create a new branch
- `GET /api/v1/branches/{id}/` - Get branch details
- `PUT /api/v1/branches/{id}/` - Update branch
- `DELETE /api/v1/branches/{id}/` - Delete branch
- `GET /api/v1/branches/hierarchy/` - Get branch hierarchy tree

### Departments
- `GET /api/v1/departments/` - List all departments
- `POST /api/v1/departments/` - Create a new department
- `GET /api/v1/departments/{id}/` - Get department details
- `PUT /api/v1/departments/{id}/` - Update department
- `DELETE /api/v1/departments/{id}/` - Delete department (fails if has employees)
- `GET /api/v1/departments/hierarchy/` - Get department hierarchy tree

### Employees
- `GET /api/v1/employees/` - List all employees
  - Query params: `department`, `branch`, `status`
- `POST /api/v1/employees/` - Create a new employee
- `GET /api/v1/employees/{id}/` - Get employee details
- `PUT /api/v1/employees/{id}/` - Update employee
- `DELETE /api/v1/employees/{id}/` - Delete employee

## Features

### Hierarchical Organization Structure
Both branches and departments support parent-child relationships, allowing for complex organizational hierarchies.

**Example hierarchy:**
```
Head Office (Branch)
├── Regional Office East
│   └── Local Office A
└── Regional Office West
    └── Local Office B

Engineering (Department)
├── Backend Team
│   ├── API Team
│   └── Database Team
└── Frontend Team
```

### Multi-tenant Support
All models are tenant-aware and automatically scoped to the user's company.

### Employee Assignment
Employees can be assigned to:
- A department (required)
- A branch (optional)

This allows for flexible organizational structures where employees can be tracked by both functional (department) and physical (branch) organization.

### Data Protection
- Departments with active employees cannot be deleted
- All queries are automatically scoped to the user's company
- Hierarchical data is validated to prevent circular references

## Testing

Run tests with:
```bash
python manage.py test apps.employees
```

Test coverage includes:
- Model creation and relationships
- Hierarchical structures
- API endpoints (CRUD operations)
- Filtering and querying
- Data isolation between companies
- Employee count calculations

## Frontend Components

### Department Management
- `DepartmentList`: Display departments in a table
- `DepartmentForm`: Create/edit departments
- `HierarchyTree`: Visualize department hierarchy

### Branch Management
- `BranchList`: Display branches in a table
- `BranchForm`: Create/edit branches with location details
- `HierarchyTree`: Visualize branch hierarchy

### Services
- `departmentService`: API client for department operations
- `branchService`: API client for branch operations
- `employeeService`: API client for employee operations

## Usage Examples

### Creating a Branch
```python
branch = Branch.objects.create(
    company=company,
    name='Main Office',
    code='MAIN',
    city='New York',
    country='USA'
)
```

### Creating a Department Hierarchy
```python
engineering = Department.objects.create(
    company=company,
    name='Engineering'
)

backend_team = Department.objects.create(
    company=company,
    name='Backend Team',
    parent=engineering
)
```

### Assigning Employee to Branch and Department
```python
employee = Employee.objects.create(
    company=company,
    employee_id='EMP001',
    first_name='John',
    last_name='Doe',
    email='john@company.com',
    department=backend_team,
    branch=branch,
    hire_date='2024-01-01'
)
```

### Querying Employees by Branch
```python
employees = Employee.objects.filter(
    company=company,
    branch=branch,
    status='active'
)
```

## Migration

The organizational structure was added in migration `0002_branch_employee_branch.py`:
- Creates the Branch model
- Adds branch field to Employee model

Run migrations with:
```bash
python manage.py migrate employees
```
