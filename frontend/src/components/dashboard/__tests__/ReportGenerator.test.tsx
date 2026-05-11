/**
 * Tests for ReportGenerator component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReportGenerator } from '../ReportGenerator';
import { dashboardService } from '@/services/dashboard';

// Mock the dashboard service
jest.mock('@/services/dashboard');

describe('ReportGenerator', () => {
  const mockReportData = {
    summary: {
      total_records: 100,
      present_days: 90,
      total_hours: 720,
      start_date: '2024-01-01',
      end_date: '2024-01-31'
    },
    employee_data: [
      {
        employee__employee_id: 'EMP001',
        employee__first_name: 'John',
        employee__last_name: 'Doe',
        days_present: 20,
        total_hours: 160
      }
    ]
  };

  beforeEach(() => {
    (dashboardService.generateReport as jest.Mock).mockResolvedValue(mockReportData);
    (dashboardService.exportReport as jest.Mock).mockResolvedValue(new Blob(['test']));
    
    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'blob:test');
    global.URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders report generator form', () => {
    render(<ReportGenerator />);

    expect(screen.getByText('Generate Reports')).toBeInTheDocument();
    expect(screen.getByLabelText('Report Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
  });

  it('generates report when form is submitted', async () => {
    render(<ReportGenerator />);

    // Fill in the form
    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2024-01-01' }
    });
    fireEvent.change(screen.getByLabelText('End Date'), {
      target: { value: '2024-01-31' }
    });

    // Click generate button
    fireEvent.click(screen.getByText('Generate Report'));

    await waitFor(() => {
      expect(dashboardService.generateReport).toHaveBeenCalledWith({
        type: 'attendance',
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      });
    });

    // Check if report data is displayed
    await waitFor(() => {
      expect(screen.getByText('Report Summary')).toBeInTheDocument();
    });
  });

  it('exports report as PDF', async () => {
    render(<ReportGenerator />);

    // Fill in the form
    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2024-01-01' }
    });
    fireEvent.change(screen.getByLabelText('End Date'), {
      target: { value: '2024-01-31' }
    });

    // Click export PDF button
    fireEvent.click(screen.getByText('Export PDF'));

    await waitFor(() => {
      expect(dashboardService.exportReport).toHaveBeenCalledWith({
        type: 'attendance',
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        format: 'pdf'
      });
    });
  });

  it('shows alert when dates are missing', () => {
    const alertMock = jest.spyOn(window, 'alert').mockImplementation();
    render(<ReportGenerator />);

    // Click generate without filling dates
    fireEvent.click(screen.getByText('Generate Report'));

    expect(alertMock).toHaveBeenCalledWith('Please select start and end dates');
    alertMock.mockRestore();
  });

  it('changes report type', () => {
    render(<ReportGenerator />);

    const select = screen.getByLabelText('Report Type') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'leave' } });

    expect(select.value).toBe('leave');
  });
});
