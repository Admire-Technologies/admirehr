'use client';

/**
 * Attendance Dashboard Component
 * 
 * Real-time attendance dashboard with WebSocket updates.
 */

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { AttendanceRecord, AttendanceWebSocketEvent } from '@/types';
import api from '@/lib/api';

interface DashboardStats {
  date: string;
  total_employees: number;
  present: number;
  late: number;
  absent: number;
  on_leave: number;
  attendance_rate: number;
  average_working_hours: number;
  recent_checkins: AttendanceRecord[];
}

export default function AttendanceDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  useEffect(() => {
    // Handle WebSocket updates
    if (lastMessage) {
      try {
        const event: AttendanceWebSocketEvent = JSON.parse(lastMessage);
        if (event.type === 'attendance.update') {
          // Refresh dashboard stats when attendance updates
          fetchDashboardStats();
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    }
  }, [lastMessage]);

  const fetchDashboardStats = async () => {
    try {
      const response = await api.get('/api/v1/attendance/records/dashboard_stats/');
      setStats(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ 
    title, 
    value, 
    subtitle, 
    color = 'blue',
    icon 
  }: { 
    title: string; 
    value: string | number; 
    subtitle?: string; 
    color?: string;
    icon?: React.ReactNode;
  }) => (
    <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className={`text-${color}-600`}>{icon}</div>}
      </div>
      <div className={`text-3xl font-bold text-${color}-600 mb-1`}>{value}</div>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error}
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Attendance Dashboard</h2>
          <p className="text-sm text-gray-600">
            {new Date(stats.date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </p>
        </div>
        <button
          onClick={fetchDashboardStats}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Employees"
          value={stats.total_employees}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        />

        <StatCard
          title="Present"
          value={stats.present}
          subtitle={`${stats.attendance_rate.toFixed(1)}% attendance rate`}
          color="green"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <StatCard
          title="Late"
          value={stats.late}
          color="yellow"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <StatCard
          title="Absent"
          value={stats.absent}
          color="red"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Working Hours</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Average Today</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats.average_working_hours.toFixed(2)}h
              </p>
            </div>
            <svg className="w-12 h-12 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">On Leave</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Employees</p>
              <p className="text-2xl font-bold text-indigo-600">{stats.on_leave}</p>
            </div>
            <svg className="w-12 h-12 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Recent Check-ins */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">Recent Check-ins</h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {stats.recent_checkins.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No check-ins yet today
            </div>
          ) : (
            stats.recent_checkins.map((record) => (
              <div key={record.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold">
                          {record.employee_name?.charAt(0) || '?'}
                        </span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {record.employee_name}
                      </p>
                      <p className="text-sm text-gray-500">{record.employee_id}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {record.check_in ? new Date(record.check_in).toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit'
                      }) : '-'}
                    </p>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      record.status === 'present' ? 'bg-green-100 text-green-800' :
                      record.status === 'late' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {record.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
