import apiClient from '@/lib/api';
import { Role, Permission, CreateRoleData } from '@/types';

export const roleService = {
  async getRoles(): Promise<Role[]> {
    const response = await apiClient.get('/auth/roles/');
    return response.data;
  },

  async getRole(id: string): Promise<Role> {
    const response = await apiClient.get(`/auth/roles/${id}/`);
    return response.data;
  },

  async createRole(data: CreateRoleData): Promise<Role> {
    const response = await apiClient.post('/auth/roles/', data);
    return response.data;
  },

  async updateRole(id: string, data: Partial<CreateRoleData>): Promise<Role> {
    const response = await apiClient.put(`/auth/roles/${id}/`, data);
    return response.data;
  },

  async deleteRole(id: string): Promise<void> {
    await apiClient.delete(`/auth/roles/${id}/`);
  },

  async getPermissions(module?: string): Promise<Permission[]> {
    const params = module ? { module } : {};
    const response = await apiClient.get('/auth/permissions/list/', { params });
    return response.data;
  },
};