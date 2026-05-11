/**
 * Leave patterns chart component using Recharts
 */
'use client';

import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { dashboardService, LeavePattern } from '@/services/dashboard';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

interface LeavePatternsChartProps {
  months?: number;
  chartType?: 'bar' | 'pie';
}

export const LeavePatternsChart: React.FC<LeavePatternsChartProps> = ({
  months = 6,
  chartType = 'bar'
}) => {
  const [data, setData] = useState<LeavePattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonths, setSelectedMonths] = useState(months);
  const [selectedChartType, setSelectedChartType] = useState(chartType);

  useEffect(() => {
    const fetchPatterns = async () => {
      setLoading(true);
      try {
        const patterns = await dashboardService.getLeavePatterns(selectedMonths);
        setData(patterns);
      } catch (error) {
        console.error('Error fetching leave patterns:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPatterns();
  }, [selectedMonths]);

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
        <h3 className="text-lg font-semibold">Leave Patterns</h3>
        <div className="flex gap-2">
          <select
            value={selectedMonths}
            onChange={(e) => setSelectedMonths(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value={3}>Last 3 months</option>
            <option value={6}>Last 6 months</option>
            <option value={12}>Last 12 months</option>
          </select>
          <select
            value={selectedChartType}
            onChange={(e) => setSelectedChartType(e.target.value as 'bar' | 'pie')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="bar">Bar Chart</option>
            <option value="pie">Pie Chart</option>
          </select>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="text-center text-gray-500 py-12">No leave data available</div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          {selectedChartType === 'bar' ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="leave_type__name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" name="Requests" />
              <Bar dataKey="total_days" fill="#10b981" name="Total Days" />
            </BarChart>
          ) : (
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="leave_type__name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => entry.leave_type__name}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          )}
        </ResponsiveContainer>
      )}
    </div>
  );
};
