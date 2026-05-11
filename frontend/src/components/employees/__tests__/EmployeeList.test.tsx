import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import EmployeeList from '../EmployeeList';
import { employeeService } from '@/services/employees';
import { departmentService } from '@/services/departments';
import { branchService } from '@/services/branches';

// Mock the services
jest.mock('@/services/employees');
jest.mock('@/services/departments');
jest.mock('@/services/branches');

const mockEmployees = [
  {
    id: '1',
    employee_id: 'EMP001',
    first_name: 'John',
    last_name: 'Doe',
    full_name: 'John Doe',
    email: 'john@test.com',
    department: 'dept-1',
    department_name: 'Engineering',
    branch: 'branch-1',
    branch_name: 'Main Office',
    position: 'Software Engineer',
    company: 'company-1',
    hire_date: '2024-01-01',
    status: 'active' as const,
  },
  {
    id: '2',
    employee_id: 'EMP002',
    first_name: 'Jane',
    last_name: 'Smith',
    full_name: 'Jane Smith',
    email: 'jane@test.com',
    department: 'dept-2',
    department_name: 'Marketing',
    position: 'Marketing Manager',
    company: 'company-1',
    hire_date: '2024-01-15',
    status: 'active' as const,
  },
];

const mockDepartments = [
  { id: 'dept-1', name: 'Engineering', company: 'company-1', is_active: true },
  { id: 'dept-2', name: 'Marketing', company: 'company-1', is_active: true },
];

const mockBranches = [
  { id: 'branch-1', name: 'Main Office', code: 'MAIN', company: 'company-1', is_active: true },
];

describe('EmployeeList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (employeeService.getEmployees as jest.Mock).mockResolvedValue(mockEmployees);
    (departmentService.getDepartments as jest.Mock).mockResolvedValue(mockDepartments);
    (branchService.getBranches as jest.Mock).mockResolvedValue(mockBranches);
  });

  it('renders employee list correctly', async () => {
    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@test.com')).toBeInTheDocument();
    });
  });

  it('displays all employees', async () => {
    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
      expect(screen.getByText('EMP002')).toBeInTheDocument();
    });
  });

  it('filters employees by search term', async () => {
    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Name, email, or ID/i);
    fireEvent.change(searchInput, { target: { value: 'John' } });

    await waitFor(() => {
      expect(employeeService.getEmployees).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'John' })
      );
    });
  });

  it('filters employees by department', async () => {
    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
    });

    const departmentSelect = screen.getByLabelText(/Department/i);
    fireEvent.change(departmentSelect, { target: { value: 'dept-1' } });

    await waitFor(() => {
      expect(employeeService.getEmployees).toHaveBeenCalledWith(
        expect.objectContaining({ department: 'dept-1' })
      );
    });
  });

  it('filters employees by status', async () => {
    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
    });

    const statusSelect = screen.getByLabelText(/Status/i);
    fireEvent.change(statusSelect, { target: { value: 'active' } });

    await waitFor(() => {
      expect(employeeService.getEmployees).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'active' })
      );
    });
  });

  it('calls onEdit when edit button is clicked', async () => {
    const onEdit = jest.fn();
    render(<EmployeeList onEdit={onEdit} />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
    });

    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);

    expect(onEdit).toHaveBeenCalledWith(mockEmployees[0]);
  });

  it('calls onView when view button is clicked', async () => {
    const onView = jest.fn();
    render(<EmployeeList onView={onView} />);

    await waitFor(() => {
      expect(screen.getByText('EMP001')).toBeInTheDocument();
    });

    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[0]);

    expect(onView).toHaveBeenCalledWith(mockEmployees[0]);
  });

  it('shows loading state initially', () => {
    render(<EmployeeList />);
    expect(screen.getByText(/Loading employees/i)).toBeInTheDocument();
  });

  it('shows error message when loading fails', async () => {
    (employeeService.getEmployees as jest.Mock).mockRejectedValue(
      new Error('Failed to load')
    );

    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText(/Error: Failed to load/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no employees found', async () => {
    (employeeService.getEmployees as jest.Mock).mockResolvedValue([]);

    render(<EmployeeList />);

    await waitFor(() => {
      expect(screen.getByText(/No employees found/i)).toBeInTheDocument();
    });
  });

  it('displays status badges correctly', async () => {
    render(<EmployeeList />);

    await waitFor(() => {
      const statusBadges = screen.getAllByText('active');
      expect(statusBadges.length).toBeGreaterThan(0);
    });
  });
});
