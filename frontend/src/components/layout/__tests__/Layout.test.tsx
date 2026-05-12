import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import DashboardLayout from '../DashboardLayout';
import Header from '../Header';
import Sidebar from '../Sidebar';

// Mock the contexts
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: '1',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      email: 'test@example.com',
    },
    logout: jest.fn(),
  }),
}));

jest.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: jest.fn(),
    setTheme: jest.fn(),
  }),
}));

jest.mock('@/contexts/PermissionContext', () => ({
  usePermissions: () => ({
    hasPermission: (permission: string) => true,
    permissions: ['view_dashboard', 'view_employee', 'view_attendance'],
  }),
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/dashboard',
  }),
  usePathname: () => '/dashboard',
}));

describe('Layout Components', () => {
  describe('DashboardLayout', () => {
    it('renders children correctly', () => {
      render(
        <DashboardLayout>
          <div>Test Content</div>
        </DashboardLayout>
      );

      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders header and sidebar', () => {
      render(
        <DashboardLayout>
          <div>Content</div>
        </DashboardLayout>
      );

      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('has proper responsive classes', () => {
      const { container } = render(
        <DashboardLayout>
          <div>Content</div>
        </DashboardLayout>
      );

      const mainContent = container.querySelector('.lg\\:pl-64');
      expect(mainContent).toBeInTheDocument();
    });

    it('toggles sidebar on mobile menu click', () => {
      render(
        <DashboardLayout>
          <div>Content</div>
        </DashboardLayout>
      );

      const menuButton = screen.getByLabelText('Toggle menu');
      fireEvent.click(menuButton);

      // Sidebar should be visible after click
      const sidebar = screen.getByRole('navigation').closest('aside');
      expect(sidebar).toHaveClass('translate-x-0');
    });
  });

  describe('Header', () => {
    it('renders user information', () => {
      render(<Header onMenuClick={() => {}} />);

      expect(screen.getByText(/Welcome back, Test/)).toBeInTheDocument();
    });

    it('renders theme toggle button', () => {
      render(<Header onMenuClick={() => {}} />);

      const themeButton = screen.getByLabelText(/Switch to/);
      expect(themeButton).toBeInTheDocument();
    });

    it('renders notifications button', () => {
      render(<Header onMenuClick={() => {}} />);

      const notificationsButton = screen.getByLabelText('Notifications');
      expect(notificationsButton).toBeInTheDocument();
    });

    it('renders user menu', () => {
      render(<Header onMenuClick={() => {}} />);

      const userMenuButton = screen.getByLabelText('User menu');
      expect(userMenuButton).toBeInTheDocument();
    });

    it('opens user menu on click', () => {
      render(<Header onMenuClick={() => {}} />);

      const userMenuButton = screen.getByLabelText('User menu');
      fireEvent.click(userMenuButton);

      expect(screen.getByText('Profile')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });

    it('calls onMenuClick when mobile menu button is clicked', () => {
      const mockOnMenuClick = jest.fn();
      render(<Header onMenuClick={mockOnMenuClick} />);

      const menuButton = screen.getByLabelText('Toggle menu');
      fireEvent.click(menuButton);

      expect(mockOnMenuClick).toHaveBeenCalledTimes(1);
    });

    it('has proper ARIA attributes', () => {
      render(<Header onMenuClick={() => {}} />);

      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();

      const menuButton = screen.getByLabelText('Toggle menu');
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });
  });

  describe('Sidebar', () => {
    it('renders navigation menu', () => {
      render(<Sidebar isOpen={true} onClose={() => {}} />);

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Employees')).toBeInTheDocument();
    });

    it('renders logo and branding', () => {
      render(<Sidebar isOpen={true} onClose={() => {}} />);

      expect(screen.getByText('Admire HRMS')).toBeInTheDocument();
    });

    it('filters menu items based on permissions', () => {
      render(<Sidebar isOpen={true} onClose={() => {}} />);

      // Items with permissions should be visible
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Employees')).toBeInTheDocument();
    });

    it('expands and collapses menu items with children', () => {
      render(<Sidebar isOpen={true} onClose={() => {}} />);

      const attendanceButton = screen.getByText('Attendance');
      fireEvent.click(attendanceButton);

      // Sub-items should be visible after expansion
      expect(screen.getByText('Terminal')).toBeInTheDocument();
      expect(screen.getByText('Records')).toBeInTheDocument();
    });

    it('highlights active menu item', () => {
      render(<Sidebar isOpen={true} onClose={() => {}} />);

      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveClass('bg-primary-100');
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    });

    it('closes on mobile when menu item is clicked', () => {
      const mockOnClose = jest.fn();
      render(<Sidebar isOpen={true} onClose={mockOnClose} />);

      const dashboardLink = screen.getByText('Dashboard');
      fireEvent.click(dashboardLink);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('has proper responsive classes', () => {
      const { container } = render(<Sidebar isOpen={false} onClose={() => {}} />);

      const sidebar = container.querySelector('aside');
      expect(sidebar).toHaveClass('-translate-x-full');
      expect(sidebar).toHaveClass('lg:translate-x-0');
    });

    it('has proper ARIA attributes', () => {
      render(<Sidebar isOpen={true} onClose={() => {}} />);

      const nav = screen.getByRole('navigation');
      expect(nav).toBeInTheDocument();

      const expandableButton = screen.getByText('Attendance');
      expect(expandableButton).toHaveAttribute('aria-expanded');
    });
  });

  describe('Responsive Behavior', () => {
    it('sidebar is hidden by default on mobile', () => {
      const { container } = render(
        <DashboardLayout>
          <div>Content</div>
        </DashboardLayout>
      );

      const sidebar = container.querySelector('aside');
      expect(sidebar).toHaveClass('-translate-x-full');
    });

    it('main content has proper padding on different screen sizes', () => {
      const { container } = render(
        <DashboardLayout>
          <div>Content</div>
        </DashboardLayout>
      );

      const main = screen.getByRole('main');
      expect(main).toHaveClass('p-4');
      expect(main).toHaveClass('sm:p-6');
      expect(main).toHaveClass('lg:p-8');
    });
  });

  describe('Accessibility', () => {
    it('all interactive elements are keyboard accessible', () => {
      render(<Header onMenuClick={() => {}} />);

      const menuButton = screen.getByLabelText('Toggle menu');
      const themeButton = screen.getByLabelText(/Switch to/);
      const notificationsButton = screen.getByLabelText('Notifications');
      const userMenuButton = screen.getByLabelText('User menu');

      menuButton.focus();
      expect(document.activeElement).toBe(menuButton);

      themeButton.focus();
      expect(document.activeElement).toBe(themeButton);

      notificationsButton.focus();
      expect(document.activeElement).toBe(notificationsButton);

      userMenuButton.focus();
      expect(document.activeElement).toBe(userMenuButton);
    });

    it('has proper landmark regions', () => {
      render(
        <DashboardLayout>
          <div>Content</div>
        </DashboardLayout>
      );

      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });
});
