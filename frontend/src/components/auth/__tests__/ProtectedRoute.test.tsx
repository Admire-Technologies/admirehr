import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ProtectedRoute from '../ProtectedRoute';
import { authService } from '@/services/auth';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/services/auth', () => ({
  authService: {
    isAuthenticated: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

import { useRouter } from 'next/navigation';

const mockPush = jest.fn();
const mockAuthService = authService as jest.Mocked<typeof authService>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      back: jest.fn(),
    } as any);
  });

  it('should render children when user is authenticated', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      company: { id: '1', name: 'Test Company', code: 'TEST' },
      role: { 
        id: '1', 
        name: 'Admin', 
        permissions: [{ id: '1', name: 'Can view', codename: 'view_permission' }] 
      },
    };

    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should redirect to login when user is not authenticated', async () => {
    mockAuthService.isAuthenticated.mockReturnValue(false);

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should redirect to unauthorized when user lacks required permissions', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      company: { id: '1', name: 'Test Company', code: 'TEST' },
      role: { 
        id: '1', 
        name: 'User', 
        permissions: [{ id: '1', name: 'Can view', codename: 'view_permission' }] 
      },
    };

    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <ProtectedRoute requiredPermissions={['admin_permission']}>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/unauthorized');
    });

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should allow access when user has required permissions', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      company: { id: '1', name: 'Test Company', code: 'TEST' },
      role: { 
        id: '1', 
        name: 'Admin', 
        permissions: [
          { id: '1', name: 'Can view', codename: 'view_permission' },
          { id: '2', name: 'Can admin', codename: 'admin_permission' }
        ] 
      },
    };

    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <ProtectedRoute requiredPermissions={['admin_permission']}>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should show loading fallback initially', () => {
    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <ProtectedRoute fallback={<div>Custom Loading...</div>}>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Custom Loading...')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should redirect to login when authentication check fails', async () => {
    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockRejectedValue(new Error('Auth failed'));

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});