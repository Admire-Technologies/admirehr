'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-semibold text-gray-900">
                  Admire HRMS Dashboard
                </h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-700">
                  Welcome, {user?.first_name || user?.username}
                </span>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Welcome to your Dashboard
                </h2>
                <p className="text-gray-600 mb-6">
                  You are successfully authenticated and can access protected content.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8">
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      User Info
                    </h3>
                    <p className="text-sm text-gray-600">
                      <strong>Username:</strong> {user?.username}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Email:</strong> {user?.email}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Company:</strong> {user?.company?.name}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Role:</strong> {user?.role?.name}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Quick Actions
                    </h3>
                    <div className="space-y-2">
                      <button className="w-full text-left text-sm text-blue-600 hover:text-blue-800">
                        View Employees
                      </button>
                      <button className="w-full text-left text-sm text-blue-600 hover:text-blue-800">
                        Attendance Records
                      </button>
                      <button className="w-full text-left text-sm text-blue-600 hover:text-blue-800">
                        Leave Requests
                      </button>
                    </div>
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Statistics
                    </h3>
                    <p className="text-2xl font-bold text-green-600">0</p>
                    <p className="text-sm text-gray-600">Active Employees</p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Recent Activity
                    </h3>
                    <p className="text-sm text-gray-600">
                      No recent activity
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}