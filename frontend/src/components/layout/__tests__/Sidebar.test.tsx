import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Sidebar from '../Sidebar';
import { usePermissions } from '@/contexts/PermissionContext';
import { usePathname } from 'next/navigation';

// Mock dependencies
jest.mock('@/contexts/PermissionContext');
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

const mockUsePermissions = usePermissions as jest.MockedFunction<typeof usePermissions>;
const mockUsePathname = usePathname as jest.MockedFunction<typeof usePathname>;

describe('Sidebar', () => {
  beforeEach(() => {
    mockUsePathname.mockReturnValue('/dashboard');
    mockUsePermissions.mockReturnValue({
      hasPermission: jest.fn(() => true),
      permissions: [],
      loading: false,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render sidebar with logo', () => {
    render(<Sidebar isOpen={true} />);

    expect(screen.getByText('Admire HRMS')).toBeInTheDocument();
  });

  it('should render all menu items when user has all permissions', () => {
    render(<Sidebar isOpen={true} />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Employees')).toBeInTheDocument();
    expect(screen.getByText('Attendance')).toBeInTheDocument();
    expect(screen.getByText('Leave Management')).toBeInTheDocument();
    expect(screen.getByText('Payroll')).toBeInTheDocument();
    expect(screen.getByText('Organization')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Security')).toBeInTheDocument();
  });

  it('should filter menu items based on permissions', () => {
    mockUsePermissions.mockReturnValue({
      hasPermission: jest.fn((permission: string) => {
        return permission === 'view_dashboard' || permission === 'view_employee';
      }),
      permissions: [],
      loading: false,
    });

    render(<Sidebar isOpen={true} />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Employees')).toBeInTheDocument();
    expect(screen.queryByText('Payroll')).not.toBeInTheDocument();
    expect(screen.queryByText('Security')).not.toBeInTheDocument();
  });

  it('should expand submenu when clicked', async () => {
    const user = userEvent.setup();
    render(<Sidebar isOpen={true} />);

    const attendanceButton = screen.getByRole('button', { name: /Toggle Attendance menu/i });
    await user.click(attendanceButton);

    await waitFor(() => {
      expect(screen.getByText('Terminal')).toBeInTheDocument();
      expect(screen.getByText('Records')).toBeInTheDocument();
      expect(screen.getByText('Reports')).toBeInTheDocument();
    });
  });

  it('should collapse submenu when clicked again', async () => {
    const user = userEvent.setup();
    render(<Sidebar isOpen={true} />);

    const attendanceButton = screen.getByRole('button', { name: /Toggle Attendance menu/i });
    
    // Expand
    await user.click(attendanceButton);
    await waitFor(() => {
      expect(screen.getByText('Terminal')).toBeInTheDocument();
    });

    // Collapse
    await user.click(attendanceButton);
    await waitFor(() => {
      expect(screen.queryByText('Terminal')).not.toBeInTheDocument();
    });
  });

  it('should highlight active menu item', () => {
    mockUsePathname.mockReturnValue('/dashboard');
    render(<Sidebar isOpen={true} />);

    const dashboardLink = screen.getByRole('link', { name: /Dashboard/i });
    expect(dashboardLink).toHaveClass('bg-primary-100');
  });

  it('should apply mobile overlay when open on mobile', () => {
    render(<Sidebar isOpen={true} />);

    const overlay = document.querySelector('.fixed.inset-0.bg-black');
    expect(overlay).toBeInTheDocument();
  });

  it('should call onClose when overlay is clicked', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    render(<Sidebar isOpen={true} onClose={onClose} />);

    const overlay = document.querySelector('.fixed.inset-0.bg-black') as HTMLElement;
    await user.click(overlay);

    expect(onClose).toHaveBeenCalled();
  });

  it('should have proper ARIA attributes', () => {
    render(<Sidebar isOpen={true} />);

    const sidebar = screen.getByRole('complementary', { name: /Main navigation/i });
    expect(sidebar).toBeInTheDocument();

    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
  });

  it('should render copyright footer', () => {
    render(<Sidebar isOpen={true} />);

    expect(screen.getByText(/© 2024 Admire HRMS/i)).toBeInTheDocument();
  });
});
