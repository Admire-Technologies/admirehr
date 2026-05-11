import apiClient from '@/lib/api';
import { Employee } from '@/types';

export const employeeService = {
  async getEmployees(params?: { 
    department?: string; 
    branch?: string; 
    status?: string;
    search?: string;
    position?: string;
  }): Promise<Employee[]> {
    const response = await apiClient.get('/employees/', { params });
    return response.data;
  },

  async getEmployee(id: string): Promise<Employee> {
    const response = await apiClient.get(`/employees/${id}/`);
    return response.data;
  },

  async createEmployee(data: Partial<Employee>): Promise<Employee> {
    const response = await apiClient.post('/employees/', data);
    return response.data;
  },

  async updateEmployee(id: string, data: Partial<Employee>): Promise<Employee> {
    const response = await apiClient.put(`/employees/${id}/`, data);
    return response.data;
  },

  async deleteEmployee(id: string): Promise<void> {
    await apiClient.delete(`/employees/${id}/`);
  },

  async importEmployees(file: File): Promise<{ success: boolean; created_count: number; errors: string[] }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/employees/import_employees/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async exportEmployees(params?: { 
    department?: string; 
    branch?: string; 
    status?: string;
    search?: string;
  }): Promise<Blob> {
    const response = await apiClient.get('/employees/export_employees/', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};
