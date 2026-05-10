import apiClient from '@/lib/api';
import { User, CreateUserData, AssignRoleData } from '@/types';

export const userService = {
  async getUsers(params?: { role?: string; search?: string }): Promise<User[]> {
    const response = await apiClient.get('/auth/users/', { params });
    return response.data;
  },

  async getUser(id: string): Promise<User> {
    const response = await apiClient.get(`/auth/users/${id}/`);
    return response.data;
  },

  async createUser(data: CreateUserData): Promise<User> {
    const response = await apiClient.post('/auth/users/', data);
    return response.data;
  },

  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const response = await apiClient.put(`/auth/users/${id}/`, data);
    return response.data;
  },

  async deleteUser(id: string): Promise<void> {
    await apiClient.delete(`/auth/users/${id}/`);
  },

  async assignRole(userId: string, data: AssignRoleData): Promise<User> {
    const response = await apiClient.post(`/auth/users/${userId}/assign-role/`, data);
    return response.data.user;
  },
};