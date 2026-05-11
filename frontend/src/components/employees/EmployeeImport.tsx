'use client';

import { useState } from 'react';
import { employeeService } from '@/services/employees';

interface EmployeeImportProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function EmployeeImport({ onSuccess, onCancel }: EmployeeImportProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ created_count: number; errors: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await employeeService.importEmployees(file);
      setResult(response);
      
      if (response.created_count > 0 && onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to import employees');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = () => {
    const csvContent = 'employee_id,first_name,last_name,email,department_name,position,hire_date,status\nEMP001,John,Doe,john.doe@example.com,Engineering,Software Engineer,2024-01-15,active\n';
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'employee_import_template.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Import Employees from CSV</h3>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Instructions:</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Download the CSV template below</li>
          <li>Fill in employee information following the template format</li>
          <li>Required fields: employee_id, first_name, last_name, email, department_name, hire_date</li>
          <li>Department must already exist in the system</li>
          <li>Date format: YYYY-MM-DD (e.g., 2024-01-15)</li>
          <li>Status options: active, inactive, terminated (default: active)</li>
        </ul>
        <button
          onClick={downloadTemplate}
          className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Download CSV Template
        </button>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-2">
            Select CSV File
          </label>
          <input
            type="file"
            id="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-indigo-50 file:text-indigo-700
              hover:file:bg-indigo-100"
          />
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Result Message */}
        {result && (
          <div className={`border px-4 py-3 rounded ${
            result.created_count > 0 
              ? 'bg-green-50 border-green-200 text-green-700' 
              : 'bg-yellow-50 border-yellow-200 text-yellow-700'
          }`}>
            <p className="font-medium">
              {result.created_count > 0 
                ? `Successfully imported ${result.created_count} employee(s)` 
                : 'No employees were imported'}
            </p>
            {result.errors.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium">Errors:</p>
                <ul className="text-sm mt-1 space-y-1 list-disc list-inside max-h-40 overflow-y-auto">
                  {result.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end space-x-3">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={loading || !file}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Importing...' : 'Import Employees'}
          </button>
        </div>
      </form>
    </div>
  );
}
