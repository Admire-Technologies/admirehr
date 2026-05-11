import apiClient from '@/lib/api';
import { Department, HierarchyNode } from '@/types';

export const departmentService = {
  async getDepartments(): Promise<Department[]> {
    const response = await apiClient.get('/departments/');
    return response.data;
  },

  async getDepartment(id: string): Promise<Department> {
    const response = await apiClient.get(`/departments/${id}/`);
    return response.data;
  },

  async createDepartment(data: Partial<Department>): Promise<Department> {
    const response = await apiClient.post('/departments/', data);
    return response.data;
  },

  async updateDepartment(id: string, data: Partial<Department>): Promise<Department> {
    const response = await apiClient.put(`/departments/${id}/`, data);
    return response.data;
  },

  async deleteDepartment(id: string): Promise<void> {
    await apiClient.delete(`/departments/${id}/`);
  },

  async getDepartmentHierarchy(): Promise<HierarchyNode[]> {
    const response = await apiClient.get('/departments/hierarchy/');
    return response.data;
  },
};
