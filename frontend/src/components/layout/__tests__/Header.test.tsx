import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Header from '../Header';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useRouter } from 'next/navigation';

// Mock dependencies
jest.mock('@/contexts/AuthContext');
jest.mock('@/contexts/ThemeContext');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseTheme = useTheme as jest.MockedFunction<typeof useTheme>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

describe('Header', () => {
  const mockLogout = jest.fn();
  const mockToggleTheme = jest.fn();
  const mockPush = jest.fn();
  const mockOnMenuClick = jest.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
      },
      logout: mockLogout,
      login: jest.fn(),
      loading: false,
      isAuthenticated: true,
    });

    mockUseTheme.mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });

    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      refresh: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn(),
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render header with user name', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);

    expect(screen.getByText(/Welcome back, Test/i)).toBeInTheDocument();
  });

  it('should call onMenuClick when menu button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const menuButton = screen.getByRole('button', { name: /Toggle menu/i });
    await user.click(menuButton);

    expect(mockOnMenuClick).toHaveBeenCalled();
  });

  it('should toggle theme when theme button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const themeButton = screen.getByRole('button', { name: /Switch to dark mode/i });
    await user.click(themeButton);

    expect(mockToggleTheme).toHaveBeenCalled();
  });

  it('should show correct theme icon based on current theme', () => {
    mockUseTheme.mockReturnValue({
      theme: 'dark',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });

    render(<Header onMenuClick={mockOnMenuClick} />);

    const themeButton = screen.getByRole('button', { name: /Switch to light mode/i });
    expect(themeButton).toBeInTheDocument();
  });

  it('should open notifications dropdown when clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const notificationsButton = screen.getByRole('button', { name: /Notifications/i });
    await user.click(notificationsButton);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('No new notifications')).toBeInTheDocument();
    });
  });

  it('should open user menu when clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const userMenuButton = screen.getByRole('button', { name: /User menu/i });
    await user.click(userMenuButton);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByRole('menuitem', { name: /Profile/i })).toBeInTheDocument();
      expect(screen.getByRole('menuitem', { name: /Settings/i })).toBeInTheDocument();
      expect(screen.getByRole('menuitem', { name: /Logout/i })).toBeInTheDocument();
    });
  });

  it('should navigate to profile when profile menu item is clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const userMenuButton = screen.getByRole('button', { name: /User menu/i });
    await user.click(userMenuButton);

    const profileButton = screen.getByRole('menuitem', { name: /Profile/i });
    await user.click(profileButton);

    expect(mockPush).toHaveBeenCalledWith('/profile');
  });

  it('should navigate to settings when settings menu item is clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const userMenuButton = screen.getByRole('button', { name: /User menu/i });
    await user.click(userMenuButton);

    const settingsButton = screen.getByRole('menuitem', { name: /Settings/i });
    await user.click(settingsButton);

    expect(mockPush).toHaveBeenCalledWith('/settings');
  });

  it('should logout and redirect when logout is clicked', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const userMenuButton = screen.getByRole('button', { name: /User menu/i });
    await user.click(userMenuButton);

    const logoutButton = screen.getByRole('menuitem', { name: /Logout/i });
    await user.click(logoutButton);

    expect(mockLogout).toHaveBeenCalled();
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  it('should close user menu when clicking outside', async () => {
    const user = userEvent.setup();
    render(<Header onMenuClick={mockOnMenuClick} />);

    const userMenuButton = screen.getByRole('button', { name: /User menu/i });
    await user.click(userMenuButton);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    // Click outside
    await user.click(document.body);

    await waitFor(() => {
      expect(screen.queryByText('test@example.com')).not.toBeInTheDocument();
    });
  });

  it('should display user initials in avatar', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);

    expect(screen.getByText('T')).toBeInTheDocument();
  });

  it('should have proper ARIA attributes', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);

    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();

    const menuButton = screen.getByRole('button', { name: /Toggle menu/i });
    expect(menuButton).toHaveAttribute('aria-label', 'Toggle menu');
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });
});
