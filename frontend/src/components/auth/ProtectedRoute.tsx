'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from '@/contexts/PermissionContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  anyPermission?: string[];
  module?: string;
  fallback?: React.ReactNode;
}

export default function ProtectedRoute({ 
  children, 
  requiredPermissions = [],
  anyPermission = [],
  module,
  fallback = <div className="flex items-center justify-center min-h-screen">Loading...</div>
}: ProtectedRouteProps) {
  const [isChecking, setIsChecking] = useState(true);
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { hasAllPermissions, hasAnyPermission, hasModuleAccess, isLoading: permissionsLoading } = usePermissions();

  useEffect(() => {
    const checkAccess = async () => {
      // Wait for auth and permissions to load
      if (authLoading || permissionsLoading) {
        return;
      }

      // Check authentication
      if (!isAuthenticated || !user) {
        router.push('/login');
        return;
      }

      // Check permissions
      let hasAccess = true;

      if (requiredPermissions.length > 0) {
        hasAccess = hasAccess && hasAllPermissions(requiredPermissions);
      }

      if (anyPermission.length > 0) {
        hasAccess = hasAccess && hasAnyPermission(anyPermission);
      }

      if (module) {
        hasAccess = hasAccess && hasModuleAccess(module);
      }

      if (!hasAccess) {
        router.push('/unauthorized');
        return;
      }

      setIsChecking(false);
    };

    checkAccess();
  }, [
    authLoading, 
    permissionsLoading, 
    isAuthenticated, 
    user, 
    requiredPermissions, 
    anyPermission, 
    module,
    hasAllPermissions,
    hasAnyPermission,
    hasModuleAccess,
    router
  ]);

  // Show loading while checking authentication and permissions
  if (authLoading || permissionsLoading || isChecking) {
    return <>{fallback}</>;
  }

  // Show nothing while redirecting
  if (!isAuthenticated || !user) {
    return null;
  }

  return <>{children}</>;
}