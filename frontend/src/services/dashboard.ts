/**
 * Dashboard and reporting API service
 */
import apiClient from '@/lib/api';

export interface DashboardMetrics {
  present_count: number;
  on_leave_count: number;
  absent_count: number;
  pending_requests: number;
  total_employees: number;
  timestamp: string;
}

export interface AttendanceTrend {
  date: string;
  present: number;
  on_leave: number;
  absent: number;
}

export interface LeavePattern {
  leave_type__name: string;
  count: number;
  total_days: number;
}

export interface PayrollSummary {
  summary: {
    total_basic_salary: number;
    total_allowances: number;
    total_deductions: number;
    total_net_salary: number;
    employee_count: number;
    avg_salary: number;
  };
  department_breakdown: Array<{
    employee__department__name: string;
    count: number;
    total: number;
  }>;
  period_start: string;
  period_end: string;
}

export interface ReportFilters {
  type: 'attendance' | 'leave';
  start_date: string;
  end_date: string;
  department_id?: string;
  employee_id?: string;
  status?: string;
}

export const dashboardService = {
  /**
   * Get real-time dashboard metrics
   */
  async getMetrics(): Promise<DashboardMetrics> {
    const response = await apiClient.get('/dashboard/metrics/');
    return response.data;
  },

  /**
   * Get attendance trends for specified number of days
   */
  async getAttendanceTrends(days: number = 30): Promise<AttendanceTrend[]> {
    const response = await apiClient.get('/dashboard/attendance-trends/', {
      params: { days }
    });
    return response.data.trends;
  },

  /**
   * Get leave patterns for specified number of months
   */
  async getLeavePatterns(months: number = 6): Promise<LeavePattern[]> {
    const response = await apiClient.get('/dashboard/leave-patterns/', {
      params: { months }
    });
    return response.data.patterns;
  },

  /**
   * Get payroll summary for specified period
   */
  async getPayrollSummary(periodStart: string, periodEnd: string): Promise<PayrollSummary> {
    const response = await apiClient.get('/dashboard/payroll-summary/', {
      params: {
        period_start: periodStart,
        period_end: periodEnd
      }
    });
    return response.data;
  },

  /**
   * Generate report with filters
   */
  async generateReport(filters: ReportFilters): Promise<any> {
    const response = await apiClient.get('/dashboard/reports/generate/', {
      params: filters
    });
    return response.data;
  },

  /**
   * Export report in specified format
   */
  async exportReport(filters: ReportFilters & { format: 'pdf' | 'excel' | 'csv' }): Promise<Blob> {
    const response = await apiClient.get('/dashboard/reports/export/', {
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  }
};
