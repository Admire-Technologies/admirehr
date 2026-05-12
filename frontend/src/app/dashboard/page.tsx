/**
 * Main dashboard page with real-time metrics and reporting
 */
'use client';

import React from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { DashboardMetrics } from '@/components/dashboard/DashboardMetrics';
import { AttendanceTrendsChart } from '@/components/dashboard/AttendanceTrendsChart';
import { LeavePatternsChart } from '@/components/dashboard/LeavePatternsChart';
import { ReportGenerator } from '@/components/dashboard/ReportGenerator';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time metrics and comprehensive reporting
          </p>
        </div>

        {/* Metrics Cards */}
        <DashboardMetrics />

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AttendanceTrendsChart />
          <LeavePatternsChart />
        </div>

        {/* Report Generation */}
        <ReportGenerator />
      </div>
    </DashboardLayout>
  );
}
