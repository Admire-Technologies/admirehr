/**
 * Tests for AttendanceList component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AttendanceList from '../AttendanceList';
import * as attendanceService from '@/services/attendance';

// Mock the attendance service
jest.mock('@/services/attendance');

const mockRecords = [
  {
    id: '1',
    employee: 'emp1',
    employee_name: 'John Doe',
    employee_id: 'EMP001',
    department_name: 'Engineering',
    date: '2024-01-15',
    check_in: '2024-01-15T09:00:00Z',
    check_out: '2024-01-15T17:00:00Z',
    working_hours: 8.0,
    status: 'present' as const,
    biometric_verified: true,
    company: 'company1'
  },
  {
    id: '2',
    employee: 'emp2',
    employee_name: 'Jane Smith',
    employee_id: 'EMP002',
    department_name: 'HR',
    date: '2024-01-15',
    check_in: '2024-01-15T09:30:00Z',
    check_out: '2024-01-15T17:30:00Z',
    working_hours: 8.0,
    status: 'late' as const,
    biometric_verified: true,
    company: 'company1'
  }
];

describe('AttendanceList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<AttendanceList />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders attendance records after loading', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 2
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('displays status badges with correct colors', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 2
    });

    render(<AttendanceList />);

    await waitFor(() => {
      const presentBadge = screen.getByText('PRESENT');
      const lateBadge = screen.getByText('LATE');
      
      expect(presentBadge).toHaveClass('bg-green-100', 'text-green-800');
      expect(lateBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });
  });

  it('filters records by date range', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 2
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Set date filters
    const startDateInput = screen.getByLabelText('Start Date');
    const endDateInput = screen.getByLabelText('End Date');
    
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-01-31' } });

    // Click apply filters
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);

    await waitFor(() => {
      expect(attendanceService.getAttendanceRecords).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: '2024-01-01',
          end_date: '2024-01-31'
        })
      );
    });
  });

  it('filters records by status', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: [mockRecords[1]], // Only late record
      count: 1
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    // Select status filter
    const statusSelect = screen.getByLabelText('Status');
    fireEvent.change(statusSelect, { target: { value: 'late' } });

    // Click apply filters
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);

    await waitFor(() => {
      expect(attendanceService.getAttendanceRecords).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'late'
        })
      );
    });
  });

  it('clears filters when clear button is clicked', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 2
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Set some filters
    const startDateInput = screen.getByLabelText('Start Date');
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });

    // Clear filters
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);

    expect(startDateInput).toHaveValue('');
  });

  it('calls onRecordClick when a record is clicked', async () => {
    const onRecordClick = jest.fn();
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 2
    });

    render(<AttendanceList onRecordClick={onRecordClick} />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click on a record row
    const recordRow = screen.getByText('John Doe').closest('tr');
    fireEvent.click(recordRow!);

    expect(onRecordClick).toHaveBeenCalledWith(mockRecords[0]);
  });

  it('calls onCorrect when correct button is clicked', async () => {
    const onCorrect = jest.fn();
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 2
    });

    render(<AttendanceList onCorrect={onCorrect} />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click correct button
    const correctButtons = screen.getAllByText('Correct');
    fireEvent.click(correctButtons[0]);

    expect(onCorrect).toHaveBeenCalledWith(mockRecords[0]);
  });

  it('displays error message when fetch fails', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockRejectedValue({
      response: { data: { error: 'Failed to fetch records' } }
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch records')).toBeInTheDocument();
    });
  });

  it('displays empty state when no records found', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: [],
      count: 0
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('No attendance records found')).toBeInTheDocument();
    });
  });

  it('handles pagination correctly', async () => {
    (attendanceService.getAttendanceRecords as jest.Mock).mockResolvedValue({
      results: mockRecords,
      count: 50
    });

    render(<AttendanceList />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click next page
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(attendanceService.getAttendanceRecords).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2
        })
      );
    });
  });
});
