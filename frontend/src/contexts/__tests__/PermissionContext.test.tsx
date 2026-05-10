import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { PermissionProvider, usePermissions, PermissionGate } from '../PermissionContext';
import { AuthProvider } from '../AuthContext';
import { authService } from '@/services/auth';

// Mock the auth service
jest.mock('@/services/auth');
const mockAuthService = authService as jest.Mocked<typeof authService>;

// Mock user data
const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: {
    id: '1',
    name: 'HR Manager',
    description: 'HR management role',
    permissions: [],
    is_system_role: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  company: {
    id: '1',
    name: 'Test Company',
    code: 'TEST001',
    settings: {},
    created_at: '2023-01-01T00:00:00Z',
  },
  is_company_admin: false,
  permissions: {
    employee: [
      {
        id: '1',
        name: 'View Employees',
        codename: 'view_employee',
        description: 'Can view employee list',
        module: 'employee',
        action: 'view',
      },
      {
        id: '2',
        name: 'Add Employee',
        codename: 'add_employee',
        description: 'Can add new employees',
        module: 'employee',
        action: 'add',
      },
    ],
    attendance: [
      {
        id: '3',
        name: 'View Attendance',
        codename: 'view_attendance',
        description: 'Can view attendance records',
        module: 'attendance',
        action: 'view',
      },
    ],
  },
};

const mockPermissionsResponse = {
  permissions: mockUser.permissions,
  role: mockUser.role,
  is_company_admin: false,
};

// Test component that uses permissions
function TestComponent() {
  const { hasPermission, hasModuleAccess, permissions } = usePermissions();
  
  return (
    <div>
      <div data-testid="has-view-employee">
        {hasPermission('view_employee') ? 'true' : 'false'}
      </div>
      <div data-testid="has-delete-employee">
        {hasPermission('delete_employee') ? 'true' : 'false'}
      </div>
      <div data-testid="has-employee-module">
        {hasModuleAccess('employee') ? 'true' : 'false'}
      </div>
      <div data-testid="has-payroll-module">
        {hasModuleAccess('payroll') ? 'true' : 'false'}
      </div>
      <div data-testid="permissions-count">
        {Object.keys(permissions).length}
      </div>
    </div>
  );
}

// Wrapper component with providers
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <PermissionProvider>
        {children}
      </PermissionProvider>
    </AuthProvider>
  );
}

describe('PermissionContext', () => {
  beforeEach(() => {
    // Mock auth service methods
    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
    mockAuthService.getUserPermissions.mockResolvedValue(mockPermissionsResponse);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should provide permission checking functions', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('has-view-employee')).toHaveTextContent('true');
      expect(screen.getByTestId('has-delete-employee')).toHaveTextContent('false');
      expect(screen.getByTestId('has-employee-module')).toHaveTextContent('true');
      expect(screen.getByTestId('has-payroll-module')).toHaveTextContent('false');
      expect(screen.getByTestId('permissions-count')).toHaveTextContent('2');
    });
  });

  it('should handle company admin permissions', async () => {
    const adminUser = {
      ...mockUser,
      is_company_admin: true,
    };

    const adminPermissionsResponse = {
      ...mockPermissionsResponse,
      is_company_admin: true,
    };

    mockAuthService.getCurrentUser.mockResolvedValue(adminUser);
    mockAuthService.getUserPermissions.mockResolvedValue(adminPermissionsResponse);

    function AdminTestComponent() {
      const { hasPermission } = usePermissions();
      
      return (
        <div data-testid="admin-has-any-permission">
          {hasPermission('any_permission') ? 'true' : 'false'}
        </div>
      );
    }

    render(
      <TestWrapper>
        <AdminTestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('admin-has-any-permission')).toHaveTextContent('true');
    });
  });

  it('should handle unauthenticated users', async () => {
    mockAuthService.isAuthenticated.mockReturnValue(false);

    function UnauthenticatedTestComponent() {
      const { hasPermission, permissions } = usePermissions();
      
      return (
        <div>
          <div data-testid="unauth-has-permission">
            {hasPermission('view_employee') ? 'true' : 'false'}
          </div>
          <div data-testid="unauth-permissions-count">
            {Object.keys(permissions).length}
          </div>
        </div>
      );
    }

    render(
      <TestWrapper>
        <UnauthenticatedTestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('unauth-has-permission')).toHaveTextContent('false');
      expect(screen.getByTestId('unauth-permissions-count')).toHaveTextContent('0');
    });
  });
});

describe('PermissionGate', () => {
  beforeEach(() => {
    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
    mockAuthService.getUserPermissions.mockResolvedValue(mockPermissionsResponse);
  });

  it('should render children when user has required permissions', async () => {
    render(
      <TestWrapper>
        <PermissionGate permissions={['view_employee']}>
          <div data-testid="protected-content">Protected Content</div>
        </PermissionGate>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  it('should not render children when user lacks required permissions', async () => {
    render(
      <TestWrapper>
        <PermissionGate permissions={['delete_employee']}>
          <div data-testid="protected-content">Protected Content</div>
        </PermissionGate>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });

  it('should render fallback when user lacks permissions', async () => {
    render(
      <TestWrapper>
        <PermissionGate 
          permissions={['delete_employee']}
          fallback={<div data-testid="fallback-content">No Permission</div>}
        >
          <div data-testid="protected-content">Protected Content</div>
        </PermissionGate>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('fallback-content')).toBeInTheDocument();
    });
  });

  it('should work with anyPermission prop', async () => {
    render(
      <TestWrapper>
        <PermissionGate anyPermission={['view_employee', 'delete_employee']}>
          <div data-testid="protected-content">Protected Content</div>
        </PermissionGate>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  it('should work with module prop', async () => {
    render(
      <TestWrapper>
        <PermissionGate module="employee">
          <div data-testid="protected-content">Protected Content</div>
        </PermissionGate>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  it('should not render when module access is denied', async () => {
    render(
      <TestWrapper>
        <PermissionGate module="payroll">
          <div data-testid="protected-content">Protected Content</div>
        </PermissionGate>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });
});