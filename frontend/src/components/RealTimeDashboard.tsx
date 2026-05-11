/**
 * Example component demonstrating real-time dashboard with WebSocket updates.
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  useDashboardMetrics,
  useAttendanceUpdates,
  useNotifications,
  useWebSocket,
} from '@/contexts/WebSocketContext';
import type {
  DashboardMetricsData,
  AttendanceUpdateData,
  NotificationData,
} from '@/lib/websocket';

interface DashboardStats {
  presentCount: number;
  onLeaveCount: number;
  pendingRequests: number;
  lastUpdate: string | null;
}

export const RealTimeDashboard: React.FC = () => {
  const { isConnected } = useWebSocket();
  const [stats, setStats] = useState<DashboardStats>({
    presentCount: 0,
    onLeaveCount: 0,
    pendingRequests: 0,
    lastUpdate: null,
  });
  const [recentAttendance, setRecentAttendance] = useState<AttendanceUpdateData[]>([]);
  const [notifications, setNotifications] = useState<NotificationData[]>([]);

  // Subscribe to dashboard metrics updates
  useDashboardMetrics((data: DashboardMetricsData) => {
    console.log('Dashboard metrics updated:', data);
    setStats({
      presentCount: data.present_count,
      onLeaveCount: data.on_leave_count,
      pendingRequests: data.pending_requests,
      lastUpdate: data.timestamp,
    });
  });

  // Subscribe to attendance updates
  useAttendanceUpdates((data: AttendanceUpdateData) => {
    console.log('Attendance update received:', data);
    setRecentAttendance((prev) => [data, ...prev].slice(0, 10)); // Keep last 10
  });

  // Subscribe to notifications
  useNotifications((data: NotificationData) => {
    console.log('Notification received:', data);
    setNotifications((prev) => [data, ...prev].slice(0, 5)); // Keep last 5
  });

  return (
    <div className="p-6 space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Real-Time Dashboard</h1>
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Dashboard Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Present Today"
          value={stats.presentCount}
          icon="👥"
          color="blue"
        />
        <MetricCard
          title="On Leave"
          value={stats.onLeaveCount}
          icon="🏖️"
          color="yellow"
        />
        <MetricCard
          title="Pending Requests"
          value={stats.pendingRequests}
          icon="📋"
          color="purple"
        />
      </div>

      {stats.lastUpdate && (
        <p className="text-xs text-gray-500">
          Last updated: {new Date(stats.lastUpdate).toLocaleString()}
        </p>
      )}

      {/* Recent Attendance */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Recent Attendance</h2>
        {recentAttendance.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent attendance updates</p>
        ) : (
          <div className="space-y-2">
            {recentAttendance.map((attendance, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-gray-50 rounded"
              >
                <div>
                  <span className="font-medium">Employee {attendance.employee_id.slice(0, 8)}</span>
                  <span className="text-sm text-gray-600 ml-2">
                    {attendance.action === 'check_in' ? '✅ Checked In' : '🚪 Checked Out'}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(attendance.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Notifications</h2>
        {notifications.length === 0 ? (
          <p className="text-gray-500 text-sm">No notifications</p>
        ) : (
          <div className="space-y-2">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-3 rounded border-l-4 ${getNotificationColor(notification.type)}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium">{notification.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(notification.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'yellow' | 'purple';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    purple: 'bg-purple-50 border-purple-200',
  };

  return (
    <div className={`p-6 rounded-lg border-2 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
        </div>
        <span className="text-4xl">{icon}</span>
      </div>
    </div>
  );
};

const getNotificationColor = (type: string): string => {
  switch (type) {
    case 'success':
      return 'border-green-500 bg-green-50';
    case 'warning':
      return 'border-yellow-500 bg-yellow-50';
    case 'error':
      return 'border-red-500 bg-red-50';
    default:
      return 'border-blue-500 bg-blue-50';
  }
};
