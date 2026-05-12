'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePermissions } from '@/contexts/PermissionContext';
import {
  LayoutDashboard,
  Users,
  Clock,
  Calendar,
  DollarSign,
  Building2,
  UserCog,
  Shield,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href?: string;
  permission?: string;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <LayoutDashboard className="w-5 h-5" />,
    href: '/dashboard',
    permission: 'view_dashboard',
  },
  {
    id: 'employees',
    label: 'Employees',
    icon: <Users className="w-5 h-5" />,
    href: '/employees',
    permission: 'view_employee',
  },
  {
    id: 'attendance',
    label: 'Attendance',
    icon: <Clock className="w-5 h-5" />,
    permission: 'view_attendance',
    children: [
      {
        id: 'attendance-terminal',
        label: 'Terminal',
        icon: null,
        href: '/attendance/terminal',
        permission: 'view_attendance',
      },
      {
        id: 'attendance-records',
        label: 'Records',
        icon: null,
        href: '/attendance/records',
        permission: 'view_attendance',
      },
      {
        id: 'attendance-reports',
        label: 'Reports',
        icon: null,
        href: '/attendance/reports',
        permission: 'view_attendance',
      },
    ],
  },
  {
    id: 'leave',
    label: 'Leave Management',
    icon: <Calendar className="w-5 h-5" />,
    permission: 'view_leave',
    children: [
      {
        id: 'leave-requests',
        label: 'My Requests',
        icon: null,
        href: '/leave/requests',
        permission: 'view_leave',
      },
      {
        id: 'leave-approvals',
        label: 'Approvals',
        icon: null,
        href: '/leave/approvals',
        permission: 'approve_leave',
      },
      {
        id: 'leave-calendar',
        label: 'Calendar',
        icon: null,
        href: '/leave/calendar',
        permission: 'view_leave',
      },
    ],
  },
  {
    id: 'payroll',
    label: 'Payroll',
    icon: <DollarSign className="w-5 h-5" />,
    permission: 'view_payroll',
    children: [
      {
        id: 'payroll-records',
        label: 'Records',
        icon: null,
        href: '/payroll/records',
        permission: 'view_payroll',
      },
      {
        id: 'payroll-generate',
        label: 'Generate',
        icon: null,
        href: '/payroll/generate',
        permission: 'manage_payroll',
      },
      {
        id: 'payroll-reports',
        label: 'Reports',
        icon: null,
        href: '/payroll/reports',
        permission: 'view_payroll',
      },
    ],
  },
  {
    id: 'organization',
    label: 'Organization',
    icon: <Building2 className="w-5 h-5" />,
    permission: 'manage_organization',
    children: [
      {
        id: 'departments',
        label: 'Departments',
        icon: null,
        href: '/organization/departments',
        permission: 'manage_organization',
      },
      {
        id: 'branches',
        label: 'Branches',
        icon: null,
        href: '/organization/branches',
        permission: 'manage_organization',
      },
    ],
  },
  {
    id: 'users',
    label: 'User Management',
    icon: <UserCog className="w-5 h-5" />,
    permission: 'manage_users',
    children: [
      {
        id: 'users-list',
        label: 'Users',
        icon: null,
        href: '/users',
        permission: 'manage_users',
      },
      {
        id: 'roles',
        label: 'Roles & Permissions',
        icon: null,
        href: '/users/roles',
        permission: 'manage_roles',
      },
    ],
  },
  {
    id: 'security',
    label: 'Security',
    icon: <Shield className="w-5 h-5" />,
    permission: 'view_security',
    children: [
      {
        id: 'audit-logs',
        label: 'Audit Logs',
        icon: null,
        href: '/security/audit-logs',
        permission: 'view_security',
      },
      {
        id: 'security-settings',
        label: 'Settings',
        icon: null,
        href: '/security/settings',
        permission: 'manage_security',
      },
    ],
  },
];

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { hasPermission } = usePermissions();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpanded = (itemId: string) => {
    setExpandedItems((prev) =>
      prev.includes(itemId)
        ? prev.filter((id) => id !== itemId)
        : [...prev, itemId]
    );
  };

  const filterMenuByPermissions = (items: MenuItem[]): MenuItem[] => {
    return items
      .filter((item) => !item.permission || hasPermission(item.permission))
      .map((item) => ({
        ...item,
        children: item.children
          ? filterMenuByPermissions(item.children)
          : undefined,
      }))
      .filter((item) => !item.children || item.children.length > 0);
  };

  const filteredMenu = filterMenuByPermissions(menuItems);

  const renderMenuItem = (item: MenuItem, level: number = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.id);
    const isActive = item.href === pathname;

    if (hasChildren) {
      return (
        <div key={item.id} className="mb-1">
          <button
            onClick={() => toggleExpanded(item.id)}
            className={`w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              isActive
                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-200'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
            aria-expanded={isExpanded}
            aria-label={`Toggle ${item.label} menu`}
          >
            <span className="flex items-center gap-3">
              {item.icon}
              <span>{item.label}</span>
            </span>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-1" role="group">
              {item.children?.map((child) => renderMenuItem(child, level + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <Link
        key={item.id}
        href={item.href || '#'}
        onClick={onClose}
        className={`flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors mb-1 ${
          isActive
            ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-200'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
        } ${level > 0 ? 'pl-8' : ''}`}
        aria-current={isActive ? 'page' : undefined}
      >
        {item.icon}
        <span>{item.label}</span>
      </Link>
    );
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Main navigation"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800">
            <Link
              href="/dashboard"
              className="flex items-center gap-2"
              aria-label="Admire HRMS Home"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                Admire HRMS
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto px-3 py-4" role="navigation">
            {filteredMenu.map((item) => renderMenuItem(item))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-800">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              © 2024 Admire HRMS
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
