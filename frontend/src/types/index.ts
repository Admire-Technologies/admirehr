// Core types for the HRMS application

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role | null;
  company: Company;
  employee?: Employee;
  is_company_admin: boolean;
  permissions?: Record<string, Permission[]>;
}

export interface Company {
  id: string;
  name: string;
  code: string;
  settings: Record<string, any>;
  created_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  is_system_role: boolean;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  name: string;
  codename: string;
  description: string;
  module: string;
  action: string;
}

export interface Employee {
  id: string;
  employee_id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  email: string;
  phone?: string;
  department: string;
  department_name?: string;
  branch?: string;
  branch_name?: string;
  position?: string;
  company: string;
  hire_date: string;
  status: 'active' | 'inactive' | 'terminated';
  date_of_birth?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  biometric_data?: any;
  created_at?: string;
  updated_at?: string;
}

export interface Department {
  id: string;
  name: string;
  description?: string;
  company: string;
  parent?: string;
  parent_name?: string;
  is_active: boolean;
  employee_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Branch {
  id: string;
  name: string;
  code: string;
  address?: string;
  phone?: string;
  email?: string;
  parent?: string;
  parent_name?: string;
  is_active: boolean;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  employee_count?: number;
  full_address?: string;
  created_at?: string;
  updated_at?: string;
}

export interface HierarchyNode {
  id: string;
  name: string;
  employee_count: number;
  parent?: string;
  children: HierarchyNode[];
}

export interface AttendanceRecord {
  id: string;
  employee: string;
  date: string;
  check_in?: string;
  check_out?: string;
  working_hours?: number;
  status: 'present' | 'absent' | 'late' | 'half_day';
  biometric_verified: boolean;
  company: string;
}

export interface LeaveRequest {
  id: string;
  employee: string;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  days_requested: number;
  status: 'pending' | 'approved' | 'rejected';
  approver?: string;
  company: string;
}

export interface LeaveType {
  id: string;
  name: string;
  days_allowed: number;
  company: string;
}

export interface PayrollRecord {
  id: string;
  employee: string;
  period_start: string;
  period_end: string;
  basic_salary: number;
  allowances: number;
  deductions: number;
  net_salary: number;
  company: string;
}

// API Response types
export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface UserPermissionsResponse {
  permissions: Record<string, Permission[]>;
  role: Role | null;
  is_company_admin: boolean;
}

// Form types
export interface CreateUserData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  role_id?: string;
  is_company_admin: boolean;
}

export interface CreateRoleData {
  name: string;
  description: string;
  permission_ids: string[];
}

export interface AssignRoleData {
  role_id: string | null;
}