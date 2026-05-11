'use client';

import { Employee } from '@/types';

interface EmployeeProfileProps {
  employee: Employee;
  onEdit?: () => void;
  onClose?: () => void;
}

export default function EmployeeProfile({ employee, onEdit, onClose }: EmployeeProfileProps) {
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800';
      case 'terminated':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-3xl font-bold">
              {employee.full_name || `${employee.first_name} ${employee.last_name}`}
            </h2>
            <p className="text-indigo-100 mt-1">{employee.position || 'Employee'}</p>
            <p className="text-indigo-100 text-sm mt-1">ID: {employee.employee_id}</p>
          </div>
          <div className="flex space-x-2">
            {onEdit && (
              <button
                onClick={onEdit}
                className="px-4 py-2 bg-white text-indigo-600 rounded-md hover:bg-indigo-50 text-sm font-medium"
              >
                Edit
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-indigo-700 text-white rounded-md hover:bg-indigo-800 text-sm font-medium"
              >
                Close
              </button>
            )}
          </div>
        </div>
        <div className="mt-4">
          <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getStatusBadgeClass(employee.status)}`}>
            {employee.status.charAt(0).toUpperCase() + employee.status.slice(1)}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Contact Information */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Contact Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Email</p>
              <p className="mt-1 text-sm text-gray-900">{employee.email}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Phone</p>
              <p className="mt-1 text-sm text-gray-900">{employee.phone || '-'}</p>
            </div>
            <div className="md:col-span-2">
              <p className="text-sm font-medium text-gray-500">Address</p>
              <p className="mt-1 text-sm text-gray-900">{employee.address || '-'}</p>
            </div>
          </div>
        </div>

        {/* Professional Information */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Professional Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Department</p>
              <p className="mt-1 text-sm text-gray-900">{employee.department_name || '-'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Branch</p>
              <p className="mt-1 text-sm text-gray-900">{employee.branch_name || '-'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Position</p>
              <p className="mt-1 text-sm text-gray-900">{employee.position || '-'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Hire Date</p>
              <p className="mt-1 text-sm text-gray-900">{formatDate(employee.hire_date)}</p>
            </div>
          </div>
        </div>

        {/* Personal Information */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Personal Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Date of Birth</p>
              <p className="mt-1 text-sm text-gray-900">{formatDate(employee.date_of_birth)}</p>
            </div>
          </div>
        </div>

        {/* Emergency Contact */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Emergency Contact</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Contact Name</p>
              <p className="mt-1 text-sm text-gray-900">{employee.emergency_contact_name || '-'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Contact Phone</p>
              <p className="mt-1 text-sm text-gray-900">{employee.emergency_contact_phone || '-'}</p>
            </div>
          </div>
        </div>

        {/* System Information */}
        {(employee.created_at || employee.updated_at) && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">System Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {employee.created_at && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Created At</p>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(employee.created_at)}</p>
                </div>
              )}
              {employee.updated_at && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Last Updated</p>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(employee.updated_at)}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
