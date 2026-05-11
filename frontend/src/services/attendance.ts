/**
 * Attendance service for API interactions.
 */

import api from '@/lib/api';
import { AttendanceRecord, BiometricData, CheckInResponse, CheckOutResponse } from '@/types';

/**
 * Check in an employee with biometric verification.
 */
export async function checkIn(
  employeeId: string,
  biometricData: BiometricData,
  terminalId?: string
): Promise<CheckInResponse> {
  const response = await api.post('/api/v1/attendance/check-in/', {
    employee_id: employeeId,
    biometric_data: biometricData,
    terminal_id: terminalId,
  });
  return response.data;
}

/**
 * Check out an employee.
 */
export async function checkOut(
  employeeId: string,
  terminalId?: string
): Promise<CheckOutResponse> {
  const response = await api.post('/api/v1/attendance/check-out/', {
    employee_id: employeeId,
    terminal_id: terminalId,
  });
  return response.data;
}

/**
 * Get attendance records with optional filtering.
 */
export async function getAttendanceRecords(params?: {
  start_date?: string;
  end_date?: string;
  employee_id?: string;
  department_id?: string;
  status?: string;
  biometric_verified?: string;
  page?: number;
}): Promise<{ results: AttendanceRecord[]; count: number }> {
  const response = await api.get('/api/v1/attendance/records/', { params });
  return response.data;
}

/**
 * Get attendance summary statistics.
 */
export async function getAttendanceSummary(params?: {
  start_date?: string;
  end_date?: string;
  employee_id?: string;
  department_id?: string;
  status?: string;
}): Promise<{
  total_records: number;
  present: number;
  late: number;
  absent: number;
  half_day: number;
  average_working_hours: number;
  total_working_hours: number;
  total_overtime_hours: number;
  unique_employees: number;
  date_range: { start: string; end: string };
}> {
  const response = await api.get('/api/v1/attendance/records/summary/', { params });
  return response.data;
}

/**
 * Get attendance reports with summary statistics.
 */
export async function getAttendanceReports(params?: {
  start_date?: string;
  end_date?: string;
  employee_id?: string;
  department_id?: string;
  status?: string;
}): Promise<{
  summary: {
    total_records: number;
    present: number;
    late: number;
    absent: number;
    half_day: number;
    average_working_hours: number;
    total_working_hours: number;
    total_overtime_hours: number;
    unique_employees: number;
    date_range: { start: string; end: string };
  };
  records: AttendanceRecord[];
}> {
  const response = await api.get('/api/v1/attendance/records/reports/', { params });
  return response.data;
}

/**
 * Get dashboard statistics for today.
 */
export async function getDashboardStats(): Promise<{
  date: string;
  total_employees: number;
  present: number;
  late: number;
  absent: number;
  on_leave: number;
  attendance_rate: number;
  average_working_hours: number;
  recent_checkins: AttendanceRecord[];
}> {
  const response = await api.get('/api/v1/attendance/records/dashboard_stats/');
  return response.data;
}

/**
 * Create manual attendance entry.
 */
export async function createManualEntry(data: {
  employee_id_input: string;
  date: string;
  check_in?: string;
  check_out?: string;
  status: string;
  notes?: string;
}): Promise<AttendanceRecord> {
  const response = await api.post('/api/v1/attendance/records/manual_entry/', data);
  return response.data;
}

/**
 * Correct/update an existing attendance record.
 */
export async function correctAttendance(
  id: string,
  data: {
    date?: string;
    check_in?: string;
    check_out?: string;
    status?: string;
    notes?: string;
  }
): Promise<AttendanceRecord> {
  const response = await api.put(`/api/v1/attendance/records/${id}/correct/`, data);
  return response.data;
}

/**
 * Get a single attendance record by ID.
 */
export async function getAttendanceRecord(id: string): Promise<AttendanceRecord> {
  const response = await api.get(`/api/v1/attendance/records/${id}/`);
  return response.data;
}

/**
 * Delete an attendance record.
 */
export async function deleteAttendanceRecord(id: string): Promise<void> {
  await api.delete(`/api/v1/attendance/records/${id}/`);
}

