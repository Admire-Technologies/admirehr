'use client';

import { useState } from 'react';
import { Employee } from '@/types';
import EmployeeList from '@/components/employees/EmployeeList';
import EmployeeForm from '@/components/employees/EmployeeForm';
import EmployeeProfile from '@/components/employees/EmployeeProfile';
import EmployeeImport from '@/components/employees/EmployeeImport';

type ViewMode = 'list' | 'create' | 'edit' | 'view' | 'import';

export default function EmployeesPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | undefined>();
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCreate = () => {
    setSelectedEmployee(undefined);
    setViewMode('create');
  };

  const handleEdit = (employee: Employee) => {
    setSelectedEmployee(employee);
    setViewMode('edit');
  };

  const handleView = (employee: Employee) => {
    setSelectedEmployee(employee);
    setViewMode('view');
  };

  const handleImport = () => {
    setViewMode('import');
  };

  const handleSuccess = () => {
    setViewMode('list');
    setSelectedEmployee(undefined);
    setRefreshKey((prev) => prev + 1);
  };

  const handleCancel = () => {
    setViewMode('list');
    setSelectedEmployee(undefined);
  };

  const handleEditFromProfile = () => {
    setViewMode('edit');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Employee Management</h1>
            <p className="text-gray-600 mt-1">Manage your organization's employees</p>
          </div>
          {viewMode === 'list' && (
            <div className="flex space-x-3">
              <button
                onClick={handleImport}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Import CSV
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Add Employee
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div>
        {viewMode === 'list' && (
          <EmployeeList
            key={refreshKey}
            onEdit={handleEdit}
            onView={handleView}
            onDelete={handleSuccess}
          />
        )}

        {viewMode === 'create' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Employee</h2>
            <EmployeeForm onSuccess={handleSuccess} onCancel={handleCancel} />
          </div>
        )}

        {viewMode === 'edit' && selectedEmployee && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Edit Employee</h2>
            <EmployeeForm
              employee={selectedEmployee}
              onSuccess={handleSuccess}
              onCancel={handleCancel}
            />
          </div>
        )}

        {viewMode === 'view' && selectedEmployee && (
          <EmployeeProfile
            employee={selectedEmployee}
            onEdit={handleEditFromProfile}
            onClose={handleCancel}
          />
        )}

        {viewMode === 'import' && (
          <EmployeeImport onSuccess={handleSuccess} onCancel={handleCancel} />
        )}
      </div>
    </div>
  );
}
