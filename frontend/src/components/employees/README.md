# Employee Management Components

This directory contains all React components for the Employee Management module of the Admire HRMS system.

## Components

### EmployeeList
A comprehensive employee listing component with search, filtering, and pagination capabilities.

**Features:**
- Search by name, email, or employee ID
- Filter by department, branch, and status
- Pagination (10 items per page)
- Export to CSV functionality
- View, Edit, and Delete actions

**Props:**
- `onEdit?: (employee: Employee) => void` - Callback when edit button is clicked
- `onDelete?: (id: string) => void` - Callback when delete is successful
- `onView?: (employee: Employee) => void` - Callback when view button is clicked

**Usage:**
```tsx
<EmployeeList
  onEdit={handleEdit}
  onView={handleView}
  onDelete={handleDelete}
/>
```

### EmployeeForm
A comprehensive form for creating and editing employee records with validation.

**Features:**
- All employee fields including personal, professional, and emergency contact information
- Department and branch selection
- Form validation
- Support for both create and update operations

**Props:**
- `employee?: Employee` - Employee data for editing (omit for create mode)
- `onSuccess?: () => void` - Callback when form submission succeeds
- `onCancel?: () => void` - Callback when cancel button is clicked

**Usage:**
```tsx
// Create mode
<EmployeeForm onSuccess={handleSuccess} onCancel={handleCancel} />

// Edit mode
<EmployeeForm
  employee={selectedEmployee}
  onSuccess={handleSuccess}
  onCancel={handleCancel}
/>
```

### EmployeeProfile
A detailed view component displaying complete employee information.

**Features:**
- Organized sections for contact, professional, personal, and emergency information
- Formatted dates and status badges
- Edit and close actions

**Props:**
- `employee: Employee` - Employee data to display
- `onEdit?: () => void` - Callback when edit button is clicked
- `onClose?: () => void` - Callback when close button is clicked

**Usage:**
```tsx
<EmployeeProfile
  employee={selectedEmployee}
  onEdit={handleEdit}
  onClose={handleClose}
/>
```

### EmployeeImport
A component for importing employees from CSV files.

**Features:**
- CSV file upload
- Template download
- Validation and error reporting
- Batch import with detailed results

**Props:**
- `onSuccess?: () => void` - Callback when import succeeds
- `onCancel?: () => void` - Callback when cancel button is clicked

**CSV Format:**
```csv
employee_id,first_name,last_name,email,department_name,position,hire_date,status
EMP001,John,Doe,john.doe@example.com,Engineering,Software Engineer,2024-01-15,active
```

**Usage:**
```tsx
<EmployeeImport onSuccess={handleSuccess} onCancel={handleCancel} />
```

## Testing

Unit tests are provided for all components using Jest and React Testing Library.

To run tests:
```bash
npm test -- --testPathPattern=employees
```

To run tests in watch mode:
```bash
npm run test:watch -- --testPathPattern=employees
```

## API Integration

All components use the `employeeService` from `@/services/employees.ts` which provides:
- `getEmployees(params)` - List employees with filtering
- `getEmployee(id)` - Get single employee
- `createEmployee(data)` - Create new employee
- `updateEmployee(id, data)` - Update employee
- `deleteEmployee(id)` - Delete employee
- `importEmployees(file)` - Import from CSV
- `exportEmployees(params)` - Export to CSV

## Styling

Components use Tailwind CSS for styling and follow the existing design patterns in the application.

## Requirements Coverage

These components fulfill the following requirements from the spec:

- **Requirement 1.1**: Display list of all employees with basic information
- **Requirement 1.2**: Display complete employee profile
- **Requirement 1.3**: Create new employee records with validation
- **Requirement 1.4**: Update employee information
- **Requirement 1.5**: Search/filter employees by name, department, role, or employee ID
- **Requirement 1.6**: Department-specific policies (enforced at API level)
