'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth';
import { User } from '@/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  fallback?: React.ReactNode;
}

export default function ProtectedRoute({ 
  children, 
  requiredPermissions = [],
  fallback = <div>Loading...</div>
}: ProtectedRouteProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (!authService.isAuthenticated()) {
          setIsAuthenticated(false);
          router.push('/login');
          return;
        }

        // Verify token by fetching user profile
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
        
        // Check permissions if required
        if (requiredPermissions.length > 0) {
          const hasPermissions = requiredPermissions.every(permission => 
            currentUser.role?.permissions?.some(p => p.codename === permission)
          );
          
          if (!hasPermissions) {
            router.push('/unauthorized');
            return;
          }
        }
        
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Authentication check failed:', error);
        setIsAuthenticated(false);
        router.push('/login');
      }
    };

    checkAuth();
  }, [router, requiredPermissions]);

  if (isAuthenticated === null) {
    return <>{fallback}</>;
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  return <>{children}</>;
}