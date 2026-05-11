import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import EmployeeForm from '../EmployeeForm';
import { employeeService } from '@/services/employees';
import { departmentService } from '@/services/departments';
import { branchService } from '@/services/branches';

// Mock the services
jest.mock('@/services/employees');
jest.mock('@/services/departments');
jest.mock('@/services/branches');

const mockDepartments = [
  { id: 'dept-1', name: 'Engineering', company: 'company-1', is_active: true },
  { id: 'dept-2', name: 'Marketing', company: 'company-1', is_active: true },
];

const mockBranches = [
  { id: 'branch-1', name: 'Main Office', code: 'MAIN', company: 'company-1', is_active: true },
];

const mockEmployee = {
  id: '1',
  employee_id: 'EMP001',
  first_name: 'John',
  last_name: 'Doe',
  email: 'john@test.com',
  phone: '+1234567890',
  department: 'dept-1',
  branch: 'branch-1',
  position: 'Software Engineer',
  company: 'company-1',
  hire_date: '2024-01-01',
  status: 'active' as const,
  date_of_birth: '1990-05-15',
  address: '123 Main St',
  emergency_contact_name: 'Jane Doe',
  emergency_contact_phone: '+0987654321',
};

describe('EmployeeForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (departmentService.getDepartments as jest.Mock).mockResolvedValue(mockDepartments);
    (branchService.getBranches as jest.Mock).mockResolvedValue(mockBranches);
  });

  it('renders form fields correctly', async () => {
    render(<EmployeeForm />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Employee ID/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    });
  });

  it('loads departments and branches on mount', async () => {
    render(<EmployeeForm />);

    await waitFor(() => {
      expect(departmentService.getDepartments).toHaveBeenCalled();
      expect(branchService.getBranches).toHaveBeenCalled();
    });
  });

  it('populates form with employee data when editing', async () => {
    render(<EmployeeForm employee={mockEmployee} />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('EMP001')).toBeInTheDocument();
      expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
      expect(screen.getByDisplayValue('john@test.com')).toBeInTheDocument();
    });
  });

  it('submits form with correct data when creating', async () => {
    const onSuccess = jest.fn();
    (employeeService.createEmployee as jest.Mock).mockResolvedValue(mockEmployee);

    render(<EmployeeForm onSuccess={onSuccess} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Employee ID/i)).toBeInTheDocument();
    });

    // Fill in required fields
    fireEvent.change(screen.getByLabelText(/Employee ID/i), {
      target: { value: 'EMP001' },
    });
    fireEvent.change(screen.getByLabelText(/First Name/i), {
      target: { value: 'John' },
    });
    fireEvent.change(screen.getByLabelText(/Last Name/i), {
      target: { value: 'Doe' },
    });
    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: 'john@test.com' },
    });

    // Select department
    const departmentSelect = screen.getByLabelText(/Department/i);
    fireEvent.change(departmentSelect, { target: { value: 'dept-1' } });

    // Set hire date
    const hireDateInput = screen.getByLabelText(/Hire Date/i);
    fireEvent.change(hireDateInput, { target: { value: '2024-01-01' } });

    // Submit form
    const submitButton = screen.getByText(/Create Employee/i);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(employeeService.createEmployee).toHaveBeenCalledWith(
        expect.objectContaining({
          employee_id: 'EMP001',
          first_name: 'John',
          last_name: 'Doe',
          email: 'john@test.com',
          department: 'dept-1',
          hire_date: '2024-01-01',
        })
      );
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('submits form with correct data when updating', async () => {
    const onSuccess = jest.fn();
    (employeeService.updateEmployee as jest.Mock).mockResolvedValue(mockEmployee);

    render(<EmployeeForm employee={mockEmployee} onSuccess={onSuccess} />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    });

    // Update first name
    const firstNameInput = screen.getByLabelText(/First Name/i);
    fireEvent.change(firstNameInput, { target: { value: 'Johnny' } });

    // Submit form
    const submitButton = screen.getByText(/Update Employee/i);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(employeeService.updateEmployee).toHaveBeenCalledWith(
        '1',
        expect.objectContaining({
          first_name: 'Johnny',
        })
      );
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('displays error message when submission fails', async () => {
    (employeeService.createEmployee as jest.Mock).mockRejectedValue({
      response: { data: { error: 'Employee ID already exists' } },
    });

    render(<EmployeeForm />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Employee ID/i)).toBeInTheDocument();
    });

    // Fill in required fields
    fireEvent.change(screen.getByLabelText(/Employee ID/i), {
      target: { value: 'EMP001' },
    });
    fireEvent.change(screen.getByLabelText(/First Name/i), {
      target: { value: 'John' },
    });
    fireEvent.change(screen.getByLabelText(/Last Name/i), {
      target: { value: 'Doe' },
    });
    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: 'john@test.com' },
    });

    const departmentSelect = screen.getByLabelText(/Department/i);
    fireEvent.change(departmentSelect, { target: { value: 'dept-1' } });

    const hireDateInput = screen.getByLabelText(/Hire Date/i);
    fireEvent.change(hireDateInput, { target: { value: '2024-01-01' } });

    // Submit form
    const submitButton = screen.getByText(/Create Employee/i);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Employee ID already exists/i)).toBeInTheDocument();
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const onCancel = jest.fn();
    render(<EmployeeForm onCancel={onCancel} />);

    await waitFor(() => {
      expect(screen.getByText(/Cancel/i)).toBeInTheDocument();
    });

    const cancelButton = screen.getByText(/Cancel/i);
    fireEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  it('validates required fields', async () => {
    render(<EmployeeForm />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Employee ID/i)).toBeInTheDocument();
    });

    // Try to submit without filling required fields
    const submitButton = screen.getByText(/Create Employee/i);
    fireEvent.click(submitButton);

    // Form should not submit (HTML5 validation will prevent it)
    expect(employeeService.createEmployee).not.toHaveBeenCalled();
  });
});
