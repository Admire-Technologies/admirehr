/**
 * Dashboard metrics component with real-time updates
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useDashboardMetrics, useWebSocket } from '@/contexts/WebSocketContext';
import { dashboardService, DashboardMetrics as MetricsType } from '@/services/dashboard';

interface MetricCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'green' | 'yellow' | 'red';
  trend?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color, trend }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
  };

  return (
    <div className={`p-6 rounded-lg border-2 ${colorClasses[color]} transition-all duration-300`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium mb-1">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
          {trend !== undefined && (
            <p className="text-xs mt-2">
              {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend)}%
            </p>
          )}
        </div>
        <span className="text-4xl">{icon}</span>
      </div>
    </div>
  );
};

export const DashboardMetrics: React.FC = () => {
  const { isConnected } = useWebSocket();
  const [metrics, setMetrics] = useState<MetricsType | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch initial metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await dashboardService.getMetrics();
        setMetrics(data);
      } catch (error) {
        console.error('Error fetching metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  // Subscribe to real-time updates
  useDashboardMetrics((data: any) => {
    setMetrics(data);
  });

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-gray-100 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  if (!metrics) {
    return <div className="text-center text-gray-500">No metrics available</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Dashboard Metrics</h2>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-xs text-gray-600">
            {isConnected ? 'Live' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Present Today"
          value={metrics.present_count}
          icon="👥"
          color="green"
        />
        <MetricCard
          title="On Leave"
          value={metrics.on_leave_count}
          icon="🏖️"
          color="yellow"
        />
        <MetricCard
          title="Absent"
          value={metrics.absent_count}
          icon="❌"
          color="red"
        />
        <MetricCard
          title="Pending Requests"
          value={metrics.pending_requests}
          icon="📋"
          color="blue"
        />
      </div>

      {metrics.timestamp && (
        <p className="text-xs text-gray-500 mt-4">
          Last updated: {new Date(metrics.timestamp).toLocaleString()}
        </p>
      )}
    </div>
  );
};
