'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { Permission, UserPermissionsResponse } from '@/types';
import { authService } from '@/services/auth';
import { useAuth } from './AuthContext';

interface PermissionContextType {
  permissions: Record<string, Permission[]>;
  hasPermission: (permissionCode: string) => boolean;
  hasAnyPermission: (permissionCodes: string[]) => boolean;
  hasAllPermissions: (permissionCodes: string[]) => boolean;
  hasModuleAccess: (module: string) => boolean;
  isLoading: boolean;
  refreshPermissions: () => Promise<void>;
}

const PermissionContext = createContext<PermissionContextType | undefined>(undefined);

export function PermissionProvider({ children }: { children: React.ReactNode }) {
  const [permissions, setPermissions] = useState<Record<string, Permission[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const { user, isAuthenticated } = useAuth();

  const fetchPermissions = async () => {
    if (!isAuthenticated || !user) {
      setPermissions({});
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const response = await authService.getUserPermissions();
      setPermissions(response.permissions);
    } catch (error) {
      console.error('Failed to fetch permissions:', error);
      setPermissions({});
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, [isAuthenticated, user]);

  const hasPermission = (permissionCode: string): boolean => {
    if (!user) return false;
    
    // Company admins have all permissions
    if (user.is_company_admin) return true;
    
    // Check if user has the specific permission
    for (const modulePermissions of Object.values(permissions)) {
      if (modulePermissions.some(p => p.codename === permissionCode)) {
        return true;
      }
    }
    
    return false;
  };

  const hasAnyPermission = (permissionCodes: string[]): boolean => {
    return permissionCodes.some(code => hasPermission(code));
  };

  const hasAllPermissions = (permissionCodes: string[]): boolean => {
    return permissionCodes.every(code => hasPermission(code));
  };

  const hasModuleAccess = (module: string): boolean => {
    if (!user) return false;
    
    // Company admins have access to all modules
    if (user.is_company_admin) return true;
    
    // Check if user has any permission in the module
    return permissions[module] && permissions[module].length > 0;
  };

  const refreshPermissions = async () => {
    await fetchPermissions();
  };

  const value = {
    permissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasModuleAccess,
    isLoading,
    refreshPermissions,
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
}

export function usePermissions() {
  const context = useContext(PermissionContext);
  if (context === undefined) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
}

// Higher-order component for permission-based rendering
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  requiredPermissions: string[],
  fallback?: React.ComponentType<P>
) {
  return function PermissionWrappedComponent(props: P) {
    const { hasAllPermissions } = usePermissions();
    
    if (!hasAllPermissions(requiredPermissions)) {
      if (fallback) {
        const FallbackComponent = fallback;
        return <FallbackComponent {...props} />;
      }
      return null;
    }
    
    return <Component {...props} />;
  };
}

// Component for conditional rendering based on permissions
interface PermissionGateProps {
  children: React.ReactNode;
  permissions?: string[];
  anyPermission?: string[];
  module?: string;
  fallback?: React.ReactNode;
}

export function PermissionGate({
  children,
  permissions = [],
  anyPermission = [],
  module,
  fallback = null
}: PermissionGateProps) {
  const { hasAllPermissions, hasAnyPermission, hasModuleAccess } = usePermissions();
  
  let hasAccess = true;
  
  if (permissions.length > 0) {
    hasAccess = hasAccess && hasAllPermissions(permissions);
  }
  
  if (anyPermission.length > 0) {
    hasAccess = hasAccess && hasAnyPermission(anyPermission);
  }
  
  if (module) {
    hasAccess = hasAccess && hasModuleAccess(module);
  }
  
  return hasAccess ? <>{children}</> : <>{fallback}</>;
}