import apiClient from '@/lib/api';
import { User, LoginResponse, UserPermissionsResponse } from '@/types';

export interface LoginCredentials {
  username: string;
  password: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await apiClient.post('/auth/login/', credentials);
    const { access, refresh, user } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout/');
    } catch (error) {
      // Ignore logout errors - we still want to clear tokens
      console.error('Logout API call failed:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post('/auth/refresh/', {
      refresh: refreshToken,
    });

    const { access } = response.data;
    localStorage.setItem('access_token', access);
    
    return access;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/profile/');
    return response.data;
  },

  async getUserPermissions(): Promise<UserPermissionsResponse> {
    const response = await apiClient.get('/auth/permissions/');
    return response.data;
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};