'use client';

/**
 * Attendance Manual Entry/Correction Component
 * 
 * Modal for creating manual attendance entries or correcting existing records.
 */

import React, { useState, useEffect } from 'react';
import { AttendanceRecord } from '@/types';
import api from '@/lib/api';

interface AttendanceManualEntryProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  record?: AttendanceRecord | null; // If provided, it's a correction
}

export default function AttendanceManualEntry({
  isOpen,
  onClose,
  onSuccess,
  record
}: AttendanceManualEntryProps) {
  const [formData, setFormData] = useState({
    employee_id_input: '',
    date: '',
    check_in: '',
    check_out: '',
    status: 'present',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isCorrection = !!record;

  useEffect(() => {
    if (record) {
      // Populate form with existing record data
      setFormData({
        employee_id_input: record.employee_id || '',
        date: record.date,
        check_in: record.check_in ? formatDateTimeLocal(record.check_in) : '',
        check_out: record.check_out ? formatDateTimeLocal(record.check_out) : '',
        status: record.status,
        notes: record.notes || ''
      });
    } else {
      // Reset form for new entry
      setFormData({
        employee_id_input: '',
        date: new Date().toISOString().split('T')[0],
        check_in: '',
        check_out: '',
        status: 'present',
        notes: ''
      });
    }
    setError(null);
  }, [record, isOpen]);

  const formatDateTimeLocal = (dateString: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: any = {
        date: formData.date,
        status: formData.status,
        notes: formData.notes
      };

      // Add check_in and check_out if provided
      if (formData.check_in) {
        payload.check_in = new Date(formData.check_in).toISOString();
      }
      if (formData.check_out) {
        payload.check_out = new Date(formData.check_out).toISOString();
      }

      if (isCorrection && record) {
        // Update existing record
        await api.put(`/api/v1/attendance/records/${record.id}/correct/`, payload);
      } else {
        // Create new manual entry
        payload.employee_id_input = formData.employee_id_input;
        await api.post('/api/v1/attendance/records/manual_entry/', payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.employee_id_input?.[0] ||
                          err.response?.data?.check_out?.[0] ||
                          'Failed to save attendance record';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">
            {isCorrection ? 'Correct Attendance Record' : 'Manual Attendance Entry'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Employee ID (only for new entries) */}
          {!isCorrection && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Employee ID *
              </label>
              <input
                type="text"
                value={formData.employee_id_input}
                onChange={(e) => handleChange('employee_id_input', e.target.value)}
                required
                placeholder="Enter Employee ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Employee Info (for corrections) */}
          {isCorrection && record && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Employee</p>
              <p className="text-lg font-semibold text-gray-800">
                {record.employee_name} ({record.employee_id})
              </p>
            </div>
          )}

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date *
            </label>
            <input
              type="date"
              value={formData.date}
              onChange={(e) => handleChange('date', e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Check In Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Check In Time
            </label>
            <input
              type="datetime-local"
              value={formData.check_in}
              onChange={(e) => handleChange('check_in', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Check Out Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Check Out Time
            </label>
            <input
              type="datetime-local"
              value={formData.check_out}
              onChange={(e) => handleChange('check_out', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              Leave empty if employee hasn't checked out yet
            </p>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status *
            </label>
            <select
              value={formData.status}
              onChange={(e) => handleChange('status', e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="present">Present</option>
              <option value="late">Late</option>
              <option value="absent">Absent</option>
              <option value="half_day">Half Day</option>
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              rows={3}
              placeholder="Add any additional notes or reasons for manual entry/correction"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Info Box */}
          <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
            <div className="flex">
              <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Note:</p>
                <p>
                  {isCorrection 
                    ? 'This will update the existing attendance record. Working hours will be recalculated automatically.'
                    : 'Manual entries are not biometrically verified. Working hours will be calculated automatically if both check-in and check-out times are provided.'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {loading ? 'Saving...' : (isCorrection ? 'Update Record' : 'Create Entry')}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
