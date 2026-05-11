import apiClient from '@/lib/api';
import { Branch, HierarchyNode } from '@/types';

export const branchService = {
  async getBranches(): Promise<Branch[]> {
    const response = await apiClient.get('/branches/');
    return response.data;
  },

  async getBranch(id: string): Promise<Branch> {
    const response = await apiClient.get(`/branches/${id}/`);
    return response.data;
  },

  async createBranch(data: Partial<Branch>): Promise<Branch> {
    const response = await apiClient.post('/branches/', data);
    return response.data;
  },

  async updateBranch(id: string, data: Partial<Branch>): Promise<Branch> {
    const response = await apiClient.put(`/branches/${id}/`, data);
    return response.data;
  },

  async deleteBranch(id: string): Promise<void> {
    await apiClient.delete(`/branches/${id}/`);
  },

  async getBranchHierarchy(): Promise<HierarchyNode[]> {
    const response = await apiClient.get('/branches/hierarchy/');
    return response.data;
  },
};
