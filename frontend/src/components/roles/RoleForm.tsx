'use client';

import { useState, useEffect } from 'react';
import { Role, Permission, CreateRoleData } from '@/types';
import { roleService } from '@/services/roles';

interface RoleFormProps {
  role?: Role;
  onSubmit: (data: CreateRoleData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function RoleForm({ role, onSubmit, onCancel, isLoading = false }: RoleFormProps) {
  const [formData, setFormData] = useState<CreateRoleData>({
    name: '',
    description: '',
    permission_ids: [],
  });
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [permissionsLoading, setPermissionsLoading] = useState(true);
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Get unique modules from permissions
  const modules = ['all', ...Array.from(new Set(permissions.map(p => p.module)))];

  // Filter permissions by selected module
  const filteredPermissions = selectedModule === 'all' 
    ? permissions 
    : permissions.filter(p => p.module === selectedModule);

  // Group permissions by module for display
  const groupedPermissions = filteredPermissions.reduce((acc, permission) => {
    if (!acc[permission.module]) {
      acc[permission.module] = [];
    }
    acc[permission.module].push(permission);
    return acc;
  }, {} as Record<string, Permission[]>);

  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        const data = await roleService.getPermissions();
        setPermissions(data);
      } catch (error) {
        console.error('Failed to fetch permissions:', error);
      } finally {
        setPermissionsLoading(false);
      }
    };

    fetchPermissions();
  }, []);

  useEffect(() => {
    if (role) {
      setFormData({
        name: role.name,
        description: role.description,
        permission_ids: role.permissions.map(p => p.id),
      });
    }
  }, [role]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Basic validation
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Role name is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error: any) {
      if (error.response?.data) {
        setErrors(error.response.data);
      } else {
        setErrors({ general: 'An error occurred while saving the role' });
      }
    }
  };

  const handlePermissionChange = (permissionId: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      permission_ids: checked
        ? [...prev.permission_ids, permissionId]
        : prev.permission_ids.filter(id => id !== permissionId)
    }));
  };

  const handleModuleToggle = (module: string, checked: boolean) => {
    const modulePermissions = permissions.filter(p => p.module === module);
    const modulePermissionIds = modulePermissions.map(p => p.id);

    setFormData(prev => ({
      ...prev,
      permission_ids: checked
        ? [...new Set([...prev.permission_ids, ...modulePermissionIds])]
        : prev.permission_ids.filter(id => !modulePermissionIds.includes(id))
    }));
  };

  const isModuleFullySelected = (module: string) => {
    const modulePermissions = permissions.filter(p => p.module === module);
    return modulePermissions.every(p => formData.permission_ids.includes(p.id));
  };

  const isModulePartiallySelected = (module: string) => {
    const modulePermissions = permissions.filter(p => p.module === module);
    return modulePermissions.some(p => formData.permission_ids.includes(p.id)) && 
           !isModuleFullySelected(module);
  };

  if (permissionsLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          {role ? 'Edit Role' : 'Create New Role'}
        </h3>

        {errors.general && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800">{errors.general}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Role Name *
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className={`mt-1 block w-full border rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Enter role name"
            />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter role description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Permissions
            </label>
            
            {/* Module filter */}
            <div className="mb-4">
              <select
                value={selectedModule}
                onChange={(e) => setSelectedModule(e.target.value)}
                className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Modules</option>
                {modules.slice(1).map(module => (
                  <option key={module} value={module}>
                    {module.charAt(0).toUpperCase() + module.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className="border border-gray-200 rounded-md max-h-96 overflow-y-auto">
              {Object.entries(groupedPermissions).map(([module, modulePermissions]) => (
                <div key={module} className="border-b border-gray-200 last:border-b-0">
                  <div className="bg-gray-50 px-4 py-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={isModuleFullySelected(module)}
                        ref={(input) => {
                          if (input) {
                            input.indeterminate = isModulePartiallySelected(module);
                          }
                        }}
                        onChange={(e) => handleModuleToggle(module, e.target.checked)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm font-medium text-gray-900 capitalize">
                        {module} ({modulePermissions.length})
                      </span>
                    </label>
                  </div>
                  <div className="px-4 py-2 space-y-2">
                    {modulePermissions.map((permission) => (
                      <label key={permission.id} className="flex items-start">
                        <input
                          type="checkbox"
                          checked={formData.permission_ids.includes(permission.id)}
                          onChange={(e) => handlePermissionChange(permission.id, e.target.checked)}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mt-0.5"
                        />
                        <div className="ml-2">
                          <span className="text-sm text-gray-900">{permission.name}</span>
                          {permission.description && (
                            <p className="text-xs text-gray-500">{permission.description}</p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            
            <p className="mt-2 text-sm text-gray-500">
              Selected: {formData.permission_ids.length} permissions
            </p>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : (role ? 'Update Role' : 'Create Role')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}