import apiClient from '@/lib/api';
import { Employee } from '@/types';

export const employeeService = {
  async getEmployees(params?: { 
    department?: string; 
    branch?: string; 
    status?: string;
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
};
