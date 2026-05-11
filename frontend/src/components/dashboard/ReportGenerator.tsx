/**
 * Report generation component with filters and export
 */
'use client';

import React, { useState } from 'react';
import { dashboardService, ReportFilters } from '@/services/dashboard';

export const ReportGenerator: React.FC = () => {
  const [filters, setFilters] = useState<ReportFilters>({
    type: 'attendance',
    start_date: '',
    end_date: '',
  });
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  const handleGenerateReport = async () => {
    if (!filters.start_date || !filters.end_date) {
      alert('Please select start and end dates');
      return;
    }

    setLoading(true);
    try {
      const data = await dashboardService.generateReport(filters);
      setReportData(data);
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'excel' | 'csv') => {
    if (!filters.start_date || !filters.end_date) {
      alert('Please select start and end dates');
      return;
    }

    setLoading(true);
    try {
      const blob = await dashboardService.exportReport({ ...filters, format });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${filters.type}_report_${filters.start_date}_to_${filters.end_date}.${
        format === 'excel' ? 'xlsx' : format
      }`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Failed to export report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6">Generate Reports</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label htmlFor="report-type" className="block text-sm font-medium mb-2">Report Type</label>
          <select
            id="report-type"
            value={filters.type}
            onChange={(e) => setFilters({ ...filters, type: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="attendance">Attendance Report</option>
            <option value="leave">Leave Report</option>
          </select>
        </div>

        <div>
          <label htmlFor="department-id" className="block text-sm font-medium mb-2">Department (Optional)</label>
          <input
            id="department-id"
            type="text"
            placeholder="Department ID"
            value={filters.department_id || ''}
            onChange={(e) => setFilters({ ...filters, department_id: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label htmlFor="start-date" className="block text-sm font-medium mb-2">Start Date</label>
          <input
            id="start-date"
            type="date"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label htmlFor="end-date" className="block text-sm font-medium mb-2">End Date</label>
          <input
            id="end-date"
            type="date"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleGenerateReport}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Report'}
        </button>

        <button
          onClick={() => handleExport('pdf')}
          disabled={loading}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
        >
          Export PDF
        </button>

        <button
          onClick={() => handleExport('excel')}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          Export Excel
        </button>

        <button
          onClick={() => handleExport('csv')}
          disabled={loading}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
        >
          Export CSV
        </button>
      </div>

      {reportData && (
        <div className="mt-6">
          <h4 className="font-semibold mb-3">Report Summary</h4>
          <div className="bg-gray-50 p-4 rounded-md">
            <pre className="text-sm overflow-auto">
              {JSON.stringify(reportData.summary, null, 2)}
            </pre>
          </div>

          {reportData.employee_data && reportData.employee_data.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold mb-3">Employee Data ({reportData.employee_data.length} records)</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(reportData.employee_data[0]).map((key) => (
                        <th
                          key={key}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                        >
                          {key.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reportData.employee_data.slice(0, 10).map((row: any, idx: number) => (
                      <tr key={idx}>
                        {Object.values(row).map((value: any, i: number) => (
                          <td key={i} className="px-4 py-2 text-sm text-gray-900">
                            {value !== null && value !== undefined ? String(value) : '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {reportData.employee_data.length > 10 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Showing 10 of {reportData.employee_data.length} records
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
