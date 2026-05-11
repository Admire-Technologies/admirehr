import { render, screen, waitFor } from '@testing-library/react';
import DepartmentList from '../DepartmentList';
import { departmentService } from '@/services/departments';

// Mock the department service
jest.mock('@/services/departments');

const mockDepartments = [
  {
    id: '1',
    name: 'Engineering',
    description: 'Engineering department',
    company: 'company-1',
    is_active: true,
    employee_count: 10,
  },
  {
    id: '2',
    name: 'Sales',
    description: 'Sales department',
    company: 'company-1',
    is_active: true,
    employee_count: 5,
  },
];

describe('DepartmentList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (departmentService.getDepartments as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<DepartmentList />);
    expect(screen.getByText(/loading departments/i)).toBeInTheDocument();
  });

  it('renders departments after loading', async () => {
    (departmentService.getDepartments as jest.Mock).mockResolvedValue(mockDepartments);

    render(<DepartmentList />);

    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('Sales')).toBeInTheDocument();
    });
  });

  it('displays employee count for each department', async () => {
    (departmentService.getDepartments as jest.Mock).mockResolvedValue(mockDepartments);

    render(<DepartmentList />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  it('renders error state when loading fails', async () => {
    (departmentService.getDepartments as jest.Mock).mockRejectedValue(
      new Error('Failed to load')
    );

    render(<DepartmentList />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no departments exist', async () => {
    (departmentService.getDepartments as jest.Mock).mockResolvedValue([]);

    render(<DepartmentList />);

    await waitFor(() => {
      expect(screen.getByText(/no departments found/i)).toBeInTheDocument();
    });
  });
});
