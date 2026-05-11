/**
 * Main dashboard page with real-time metrics and reporting
 */
'use client';

import React from 'react';
import { DashboardMetrics } from '@/components/dashboard/DashboardMetrics';
import { AttendanceTrendsChart } from '@/components/dashboard/AttendanceTrendsChart';
import { LeavePatternsChart } from '@/components/dashboard/LeavePatternsChart';
import { ReportGenerator } from '@/components/dashboard/ReportGenerator';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">
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
    </div>
  );
}
