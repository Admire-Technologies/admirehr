/**
 * Attendance trends chart component using Recharts
 */
'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { dashboardService, AttendanceTrend } from '@/services/dashboard';

interface AttendanceTrendsChartProps {
  days?: number;
}

export const AttendanceTrendsChart: React.FC<AttendanceTrendsChartProps> = ({ days = 30 }) => {
  const [data, setData] = useState<AttendanceTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDays, setSelectedDays] = useState(days);

  useEffect(() => {
    const fetchTrends = async () => {
      setLoading(true);
      try {
        const trends = await dashboardService.getAttendanceTrends(selectedDays);
        setData(trends);
      } catch (error) {
        console.error('Error fetching attendance trends:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrends();
  }, [selectedDays]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="h-80 bg-gray-100 animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Attendance Trends</h3>
        <select
          value={selectedDays}
          onChange={(e) => setSelectedDays(Number(e.target.value))}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          />
          <YAxis />
          <Tooltip
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="present"
            stroke="#10b981"
            strokeWidth={2}
            name="Present"
          />
          <Line
            type="monotone"
            dataKey="on_leave"
            stroke="#f59e0b"
            strokeWidth={2}
            name="On Leave"
          />
          <Line
            type="monotone"
            dataKey="absent"
            stroke="#ef4444"
            strokeWidth={2}
            name="Absent"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
