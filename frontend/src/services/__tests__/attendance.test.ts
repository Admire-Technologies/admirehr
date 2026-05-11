/**
 * Tests for attendance service.
 */

import { checkIn, checkOut, getAttendanceRecords, getAttendanceReports } from '../attendance';
import api from '@/lib/api';

jest.mock('@/lib/api');

const mockApi = api as jest.Mocked<typeof api>;

describe('Attendance Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('checkIn', () => {
    it('sends check-in request with biometric data', async () => {
      const mockResponse = {
        data: {
          attendance: {
            id: '1',
            employee: 'emp-1',
            date: '2024-01-01',
            check_in: '2024-01-01T09:00:00Z',
            status: 'present',
            biometric_verified: true,
            company: 'company-1',
          },
          message: 'Check-in successful!',
          similarity_score: 0.95,
        },
      };

      mockApi.post.mockResolvedValue(mockResponse);

      const biometricData = {
        face_encoding: [0.1, 0.2, 0.3],
        quality_score: 0.95,
        capture_timestamp: '2024-01-01T09:00:00Z',
      };

      const result = await checkIn('EMP001', biometricData, 'TERMINAL_01');

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/attendance/check-in/', {
        employee_id: 'EMP001',
        biometric_data: biometricData,
        terminal_id: 'TERMINAL_01',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('sends check-in request without terminal ID', async () => {
      const mockResponse = {
        data: {
          attendance: {
            id: '1',
            employee: 'emp-1',
            date: '2024-01-01',
            check_in: '2024-01-01T09:00:00Z',
            status: 'present',
            biometric_verified: true,
            company: 'company-1',
          },
          message: 'Check-in successful!',
          similarity_score: 0.95,
        },
      };

      mockApi.post.mockResolvedValue(mockResponse);

      const biometricData = {
        face_encoding: [0.1, 0.2, 0.3],
        quality_score: 0.95,
      };

      await checkIn('EMP001', biometricData);

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/attendance/check-in/', {
        employee_id: 'EMP001',
        biometric_data: biometricData,
        terminal_id: undefined,
      });
    });
  });

  describe('checkOut', () => {
    it('sends check-out request', async () => {
      const mockResponse = {
        data: {
          attendance: {
            id: '1',
            employee: 'emp-1',
            date: '2024-01-01',
            check_in: '2024-01-01T09:00:00Z',
            check_out: '2024-01-01T17:00:00Z',
            working_hours: 8.0,
            status: 'present',
            biometric_verified: true,
            company: 'company-1',
          },
          message: 'Check-out successful!',
          working_hours: 8.0,
          overtime_hours: 0.0,
        },
      };

      mockApi.post.mockResolvedValue(mockResponse);

      const result = await checkOut('EMP001', 'TERMINAL_01');

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/attendance/check-out/', {
        employee_id: 'EMP001',
        terminal_id: 'TERMINAL_01',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getAttendanceRecords', () => {
    it('fetches attendance records without filters', async () => {
      const mockResponse = {
        data: {
          results: [
            {
              id: '1',
              employee: 'emp-1',
              date: '2024-01-01',
              status: 'present',
              biometric_verified: true,
              company: 'company-1',
            },
          ],
          count: 1,
        },
      };

      mockApi.get.mockResolvedValue(mockResponse);

      const result = await getAttendanceRecords();

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/attendance/', { params: undefined });
      expect(result).toEqual(mockResponse.data);
    });

    it('fetches attendance records with filters', async () => {
      const mockResponse = {
        data: {
          results: [],
          count: 0,
        },
      };

      mockApi.get.mockResolvedValue(mockResponse);

      const params = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        employee_id: 'EMP001',
        page: 1,
      };

      await getAttendanceRecords(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/attendance/', { params });
    });
  });

  describe('getAttendanceReports', () => {
    it('fetches attendance reports', async () => {
      const mockResponse = {
        data: {
          summary: {
            total_records: 10,
            present: 8,
            late: 2,
            absent: 0,
            average_working_hours: 8.5,
          },
          records: [],
        },
      };

      mockApi.get.mockResolvedValue(mockResponse);

      const result = await getAttendanceReports();

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/attendance/reports/', { params: undefined });
      expect(result).toEqual(mockResponse.data);
    });

    it('fetches attendance reports with filters', async () => {
      const mockResponse = {
        data: {
          summary: {
            total_records: 5,
            present: 5,
            late: 0,
            absent: 0,
            average_working_hours: 8.0,
          },
          records: [],
        },
      };

      mockApi.get.mockResolvedValue(mockResponse);

      const params = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        employee_id: 'EMP001',
      };

      await getAttendanceReports(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/attendance/reports/', { params });
    });
  });
});
