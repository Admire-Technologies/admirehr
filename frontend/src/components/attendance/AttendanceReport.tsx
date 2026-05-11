'use client';

/**
 * Attendance Report Component
 * 
 * Generates attendance reports with date range filtering and export capabilities.
 */

import React, { useState } from 'react';
import { getAttendanceReports } from '@/services/attendance';
import { AttendanceRecord } from '@/types';

interface ReportSummary {
  total_records: number;
  present: number;
  late: number;
  absent: number;
  half_day: number;
  average_working_hours: number;
  total_working_hours: number;
  total_overtime_hours: number;
  unique_employees: number;
  date_range: {
    start: string;
    end: string;
  };
}

export default function AttendanceReport() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [showRecords, setShowRecords] = useState(false);

  const handleGenerateReport = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params: any = {
        start_date: startDate,
        end_date: endDate
      };

      if (employeeId) {
        params.employee_id = employeeId;
      }

      const response = await getAttendanceReports(params);
      setSummary(response.summary);
      setRecords(response.records);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'excel') => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params: any = {
        start_date: startDate,
        end_date: endDate,
        export_format: format
      };

      if (employeeId) {
        params.employee_id = employeeId;
      }

      // Make API call to get file
      const response = await fetch(
        `/api/v1/attendance/records/reports/?${new URLSearchParams(params)}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_report_${startDate}_${endDate}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError('Failed to export report');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ label, value, color = 'blue' }: { label: string; value: string | number; color?: string }) => (
    <div className={`bg-${color}-50 p-4 rounded-lg border border-${color}-200`}>
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className={`text-2xl font-bold text-${color}-700`}>{value}</div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Report Parameters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Generate Attendance Report</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date *
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date *
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Employee ID (Optional)
            </label>
            <input
              type="text"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="Leave empty for all"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleGenerateReport}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
          
          {summary && (
            <>
              <button
                onClick={() => handleExport('pdf')}
                disabled={loading}
                className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 transition-colors"
              >
                Export PDF
              </button>
              <button
                onClick={() => handleExport('excel')}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 transition-colors"
              >
                Export Excel
              </button>
            </>
          )}
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}
      </div>

      {/* Report Summary */}
      {summary && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-800">Report Summary</h3>
            <span className="text-sm text-gray-600">
              {summary.date_range.start} to {summary.date_range.end}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Records" value={summary.total_records} color="blue" />
            <StatCard label="Present" value={summary.present} color="green" />
            <StatCard label="Late" value={summary.late} color="yellow" />
            <StatCard label="Absent" value={summary.absent} color="red" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Half Day" value={summary.half_day} color="indigo" />
            <StatCard label="Avg Hours/Day" value={summary.average_working_hours.toFixed(2)} color="purple" />
            <StatCard label="Total Hours" value={summary.total_working_hours.toFixed(2)} color="pink" />
            <StatCard label="Overtime Hours" value={summary.total_overtime_hours.toFixed(2)} color="orange" />
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-600">Unique Employees: </span>
                <span className="text-lg font-semibold text-gray-800">{summary.unique_employees}</span>
              </div>
              <button
                onClick={() => setShowRecords(!showRecords)}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                {showRecords ? 'Hide' : 'Show'} Detailed Records
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Records */}
      {summary && showRecords && records.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-bold text-gray-800">Detailed Records</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check In</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check Out</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hours</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {records.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(record.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{record.employee_name}</div>
                      <div className="text-sm text-gray-500">{record.employee_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.check_in ? new Date(record.check_in).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.check_out ? new Date(record.check_out).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.working_hours ? `${record.working_hours.toFixed(2)}h` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        record.status === 'present' ? 'bg-green-100 text-green-800' :
                        record.status === 'late' ? 'bg-yellow-100 text-yellow-800' :
                        record.status === 'absent' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {record.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
