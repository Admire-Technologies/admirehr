/**
 * Tests for DashboardMetrics component
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { DashboardMetrics } from '../DashboardMetrics';
import { dashboardService } from '@/services/dashboard';

// Mock the dashboard service
jest.mock('@/services/dashboard');

// Mock WebSocket context
jest.mock('@/contexts/WebSocketContext', () => ({
  useWebSocket: () => ({ isConnected: true }),
  useDashboardMetrics: (callback: any) => {
    // Simulate real-time update
    setTimeout(() => {
      callback({
        present_count: 150,
        on_leave_count: 5,
        absent_count: 10,
        pending_requests: 3,
        total_employees: 165,
        timestamp: new Date().toISOString()
      });
    }, 100);
  }
}));

describe('DashboardMetrics', () => {
  const mockMetrics = {
    present_count: 100,
    on_leave_count: 5,
    absent_count: 10,
    pending_requests: 3,
    total_employees: 115,
    timestamp: '2024-01-15T10:00:00Z'
  };

  beforeEach(() => {
    (dashboardService.getMetrics as jest.Mock).mockResolvedValue(mockMetrics);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<DashboardMetrics />);
    expect(screen.getAllByRole('generic').some(el => 
      el.className.includes('animate-pulse')
    )).toBe(true);
  });

  it('fetches and displays metrics', async () => {
    render(<DashboardMetrics />);

    await waitFor(() => {
      expect(screen.getByText('Present Today')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    expect(screen.getByText('On Leave')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Absent')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('displays connection status', async () => {
    render(<DashboardMetrics />);

    await waitFor(() => {
      expect(screen.getByText('Live')).toBeInTheDocument();
    });
  });

  it('updates metrics in real-time', async () => {
    render(<DashboardMetrics />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    // Wait for WebSocket update
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('displays last updated timestamp', async () => {
    render(<DashboardMetrics />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });
});
