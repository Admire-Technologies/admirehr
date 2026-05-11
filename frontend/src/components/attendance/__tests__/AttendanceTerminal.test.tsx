/**
 * Tests for AttendanceTerminal component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AttendanceTerminal from '../AttendanceTerminal';
import * as attendanceService from '@/services/attendance';

// Mock the attendance service
jest.mock('@/services/attendance');

const mockCheckIn = attendanceService.checkIn as jest.MockedFunction<typeof attendanceService.checkIn>;
const mockCheckOut = attendanceService.checkOut as jest.MockedFunction<typeof attendanceService.checkOut>;

describe('AttendanceTerminal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders terminal interface correctly', () => {
    render(<AttendanceTerminal />);
    
    expect(screen.getByText('Attendance Terminal')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter Employee ID')).toBeInTheDocument();
    expect(screen.getByText('Check In')).toBeInTheDocument();
    expect(screen.getByText('Check Out')).toBeInTheDocument();
  });

  it('displays terminal ID', () => {
    render(<AttendanceTerminal terminalId="TERMINAL_02" />);
    
    expect(screen.getByText(/Terminal ID: TERMINAL_02/)).toBeInTheDocument();
  });

  it('requires employee ID for check-in', async () => {
    render(<AttendanceTerminal />);
    
    const checkInButton = screen.getByText('Check In');
    fireEvent.click(checkInButton);
    
    // Should show error message
    await waitFor(() => {
      expect(screen.getByText('Please enter Employee ID')).toBeInTheDocument();
    });
  });

  it('handles successful check-in', async () => {
    const mockResponse = {
      attendance: {
        id: '1',
        employee: 'emp-1',
        employee_name: 'John Doe',
        employee_id: 'EMP001',
        date: '2024-01-01',
        check_in: '2024-01-01T09:00:00Z',
        status: 'present' as const,
        biometric_verified: true,
        company: 'company-1',
      },
      message: 'Check-in successful!',
      similarity_score: 0.95,
      policy_summary: {
        date: '2024-01-01',
        status: 'present',
        check_in: '2024-01-01T09:00:00Z',
        check_out: null,
        working_hours: 0,
        biometric_verified: true,
        policy: {
          expected_hours: 8,
          grace_period_minutes: 15,
          work_start_time: '09:00',
          work_end_time: '17:00',
        },
      },
    };

    mockCheckIn.mockResolvedValue(mockResponse);

    const onSuccess = jest.fn();
    render(<AttendanceTerminal onSuccess={onSuccess} />);
    
    // Enter employee ID
    const input = screen.getByPlaceholderText('Enter Employee ID');
    fireEvent.change(input, { target: { value: 'EMP001' } });
    
    // Click check in
    const checkInButton = screen.getByText('Check In');
    fireEvent.click(checkInButton);
    
    // Wait for face capture simulation
    await waitFor(() => {
      expect(screen.getByText('Face captured successfully!')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Click verify button
    const verifyButton = screen.getByText('Verify & Check In');
    fireEvent.click(verifyButton);
    
    // Wait for success
    await waitFor(() => {
      expect(mockCheckIn).toHaveBeenCalledWith(
        'EMP001',
        expect.objectContaining({
          face_encoding: expect.any(Array),
          quality_score: expect.any(Number),
        }),
        'TERMINAL_01'
      );
      expect(onSuccess).toHaveBeenCalledWith(mockResponse.attendance);
    });
  });

  it('handles check-in error', async () => {
    mockCheckIn.mockRejectedValue({
      response: {
        data: {
          error: 'Biometric verification failed',
        },
      },
    });

    const onError = jest.fn();
    render(<AttendanceTerminal onError={onError} />);
    
    // Enter employee ID
    const input = screen.getByPlaceholderText('Enter Employee ID');
    fireEvent.change(input, { target: { value: 'EMP001' } });
    
    // Click check in
    const checkInButton = screen.getByText('Check In');
    fireEvent.click(checkInButton);
    
    // Wait for face capture
    await waitFor(() => {
      expect(screen.getByText('Face captured successfully!')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Click verify button
    const verifyButton = screen.getByText('Verify & Check In');
    fireEvent.click(verifyButton);
    
    // Wait for error
    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Biometric verification failed');
    });
  });

  it('handles successful check-out', async () => {
    const mockResponse = {
      attendance: {
        id: '1',
        employee: 'emp-1',
        employee_name: 'John Doe',
        employee_id: 'EMP001',
        date: '2024-01-01',
        check_in: '2024-01-01T09:00:00Z',
        check_out: '2024-01-01T17:00:00Z',
        working_hours: 8.0,
        status: 'present' as const,
        biometric_verified: true,
        company: 'company-1',
      },
      message: 'Check-out successful!',
      working_hours: 8.0,
      overtime_hours: 0.0,
      policy_summary: {
        date: '2024-01-01',
        status: 'present',
        check_in: '2024-01-01T09:00:00Z',
        check_out: '2024-01-01T17:00:00Z',
        working_hours: 8.0,
        biometric_verified: true,
        policy: {
          expected_hours: 8,
          grace_period_minutes: 15,
          work_start_time: '09:00',
          work_end_time: '17:00',
        },
      },
    };

    mockCheckOut.mockResolvedValue(mockResponse);

    const onSuccess = jest.fn();
    render(<AttendanceTerminal onSuccess={onSuccess} />);
    
    // Enter employee ID
    const input = screen.getByPlaceholderText('Enter Employee ID');
    fireEvent.change(input, { target: { value: 'EMP001' } });
    
    // Click check out
    const checkOutButton = screen.getByText('Check Out');
    fireEvent.click(checkOutButton);
    
    // Wait for success
    await waitFor(() => {
      expect(mockCheckOut).toHaveBeenCalledWith('EMP001', 'TERMINAL_01');
      expect(onSuccess).toHaveBeenCalledWith(mockResponse.attendance);
    });
  });

  it('disables buttons during processing', async () => {
    mockCheckOut.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<AttendanceTerminal />);
    
    // Enter employee ID
    const input = screen.getByPlaceholderText('Enter Employee ID');
    fireEvent.change(input, { target: { value: 'EMP001' } });
    
    // Click check out
    const checkOutButton = screen.getByText('Check Out');
    fireEvent.click(checkOutButton);
    
    // Buttons should be disabled
    await waitFor(() => {
      expect(checkOutButton).toBeDisabled();
      expect(screen.getByText('Check In')).toBeDisabled();
    });
  });

  it('displays last attendance information', async () => {
    const mockResponse = {
      attendance: {
        id: '1',
        employee: 'emp-1',
        employee_name: 'John Doe',
        employee_id: 'EMP001',
        date: '2024-01-01',
        check_in: '2024-01-01T09:00:00Z',
        check_out: '2024-01-01T17:00:00Z',
        working_hours: 8.0,
        status: 'present' as const,
        biometric_verified: true,
        company: 'company-1',
      },
      message: 'Check-out successful!',
      working_hours: 8.0,
      overtime_hours: 0.0,
      policy_summary: {
        date: '2024-01-01',
        status: 'present',
        check_in: '2024-01-01T09:00:00Z',
        check_out: '2024-01-01T17:00:00Z',
        working_hours: 8.0,
        biometric_verified: true,
        policy: {
          expected_hours: 8,
          grace_period_minutes: 15,
          work_start_time: '09:00',
          work_end_time: '17:00',
        },
      },
    };

    mockCheckOut.mockResolvedValue(mockResponse);

    render(<AttendanceTerminal />);
    
    // Enter employee ID and check out
    const input = screen.getByPlaceholderText('Enter Employee ID');
    fireEvent.change(input, { target: { value: 'EMP001' } });
    
    const checkOutButton = screen.getByText('Check Out');
    fireEvent.click(checkOutButton);
    
    // Wait for last attendance to be displayed
    await waitFor(() => {
      expect(screen.getByText('Last Attendance')).toBeInTheDocument();
      expect(screen.getByText(/Working Hours: 8.00h/)).toBeInTheDocument();
      expect(screen.getByText(/Biometric Verified:/)).toBeInTheDocument();
    });
  });

  it('shows instructions', () => {
    render(<AttendanceTerminal />);
    
    expect(screen.getByText('Instructions')).toBeInTheDocument();
    expect(screen.getByText(/Enter your Employee ID/)).toBeInTheDocument();
    expect(screen.getByText(/position your face in the camera/)).toBeInTheDocument();
  });
});
