"""
Management command to create default permissions for RBAC system.
"""

from django.core.management.base import BaseCommand
from apps.authentication.models import Permission


class Command(BaseCommand):
    help = 'Create default permissions for RBAC system'

    def handle(self, *args, **options):
        """Create default permissions."""
        
        # Define default permissions
        default_permissions = [
            # Employee Management
            {'name': 'View Employees', 'codename': 'view_employee', 'module': 'employee', 'action': 'view', 'description': 'Can view employee list and details'},
            {'name': 'Add Employee', 'codename': 'add_employee', 'module': 'employee', 'action': 'add', 'description': 'Can create new employees'},
            {'name': 'Change Employee', 'codename': 'change_employee', 'module': 'employee', 'action': 'change', 'description': 'Can edit employee information'},
            {'name': 'Delete Employee', 'codename': 'delete_employee', 'module': 'employee', 'action': 'delete', 'description': 'Can delete employees'},
            
            # Attendance Management
            {'name': 'View Attendance', 'codename': 'view_attendance', 'module': 'attendance', 'action': 'view', 'description': 'Can view attendance records'},
            {'name': 'Add Attendance', 'codename': 'add_attendance', 'module': 'attendance', 'action': 'add', 'description': 'Can create attendance records'},
            {'name': 'Change Attendance', 'codename': 'change_attendance', 'module': 'attendance', 'action': 'change', 'description': 'Can edit attendance records'},
            {'name': 'Delete Attendance', 'codename': 'delete_attendance', 'module': 'attendance', 'action': 'delete', 'description': 'Can delete attendance records'},
            {'name': 'Manage Attendance Terminal', 'codename': 'manage_attendance_terminal', 'module': 'attendance', 'action': 'manage', 'description': 'Can manage attendance terminals'},
            
            # Leave Management
            {'name': 'View Leave Requests', 'codename': 'view_leave', 'module': 'leave', 'action': 'view', 'description': 'Can view leave requests'},
            {'name': 'Add Leave Request', 'codename': 'add_leave', 'module': 'leave', 'action': 'add', 'description': 'Can create leave requests'},
            {'name': 'Change Leave Request', 'codename': 'change_leave', 'module': 'leave', 'action': 'change', 'description': 'Can edit leave requests'},
            {'name': 'Delete Leave Request', 'codename': 'delete_leave', 'module': 'leave', 'action': 'delete', 'description': 'Can delete leave requests'},
            {'name': 'Approve Leave', 'codename': 'approve_leave', 'module': 'leave', 'action': 'approve', 'description': 'Can approve/reject leave requests'},
            {'name': 'Manage Leave Types', 'codename': 'manage_leave_types', 'module': 'leave', 'action': 'manage', 'description': 'Can manage leave types and policies'},
            
            # Payroll Management
            {'name': 'View Payroll', 'codename': 'view_payroll', 'module': 'payroll', 'action': 'view', 'description': 'Can view payroll records'},
            {'name': 'Add Payroll', 'codename': 'add_payroll', 'module': 'payroll', 'action': 'add', 'description': 'Can create payroll records'},
            {'name': 'Change Payroll', 'codename': 'change_payroll', 'module': 'payroll', 'action': 'change', 'description': 'Can edit payroll records'},
            {'name': 'Delete Payroll', 'codename': 'delete_payroll', 'module': 'payroll', 'action': 'delete', 'description': 'Can delete payroll records'},
            {'name': 'Process Payroll', 'codename': 'process_payroll', 'module': 'payroll', 'action': 'process', 'description': 'Can process payroll calculations'},
            {'name': 'Manage Salary Rules', 'codename': 'manage_salary_rules', 'module': 'payroll', 'action': 'manage', 'description': 'Can manage salary rules and structures'},
            
            # Reports and Analytics
            {'name': 'View Reports', 'codename': 'view_report', 'module': 'report', 'action': 'view', 'description': 'Can view reports and analytics'},
            {'name': 'Generate Reports', 'codename': 'generate_report', 'module': 'report', 'action': 'generate', 'description': 'Can generate custom reports'},
            {'name': 'Export Reports', 'codename': 'export_report', 'module': 'report', 'action': 'export', 'description': 'Can export reports to various formats'},
            
            # User Management
            {'name': 'View Users', 'codename': 'view_user', 'module': 'user', 'action': 'view', 'description': 'Can view user accounts'},
            {'name': 'Add User', 'codename': 'add_user', 'module': 'user', 'action': 'add', 'description': 'Can create user accounts'},
            {'name': 'Change User', 'codename': 'change_user', 'module': 'user', 'action': 'change', 'description': 'Can edit user accounts'},
            {'name': 'Delete User', 'codename': 'delete_user', 'module': 'user', 'action': 'delete', 'description': 'Can delete user accounts'},
            {'name': 'Manage Users', 'codename': 'manage_users', 'module': 'user', 'action': 'manage', 'description': 'Full user management permissions'},
            
            # Role Management
            {'name': 'View Roles', 'codename': 'view_role', 'module': 'role', 'action': 'view', 'description': 'Can view roles'},
            {'name': 'Add Role', 'codename': 'add_role', 'module': 'role', 'action': 'add', 'description': 'Can create roles'},
            {'name': 'Change Role', 'codename': 'change_role', 'module': 'role', 'action': 'change', 'description': 'Can edit roles'},
            {'name': 'Delete Role', 'codename': 'delete_role', 'module': 'role', 'action': 'delete', 'description': 'Can delete roles'},
            {'name': 'Manage Roles', 'codename': 'manage_roles', 'module': 'role', 'action': 'manage', 'description': 'Full role management permissions'},
            
            # Department Management
            {'name': 'View Departments', 'codename': 'view_department', 'module': 'department', 'action': 'view', 'description': 'Can view departments'},
            {'name': 'Add Department', 'codename': 'add_department', 'module': 'department', 'action': 'add', 'description': 'Can create departments'},
            {'name': 'Change Department', 'codename': 'change_department', 'module': 'department', 'action': 'change', 'description': 'Can edit departments'},
            {'name': 'Delete Department', 'codename': 'delete_department', 'module': 'department', 'action': 'delete', 'description': 'Can delete departments'},
            
            # System Administration
            {'name': 'System Settings', 'codename': 'manage_system_settings', 'module': 'system', 'action': 'manage', 'description': 'Can manage system settings'},
            {'name': 'Company Settings', 'codename': 'manage_company_settings', 'module': 'system', 'action': 'manage', 'description': 'Can manage company settings'},
            {'name': 'Audit Logs', 'codename': 'view_audit_logs', 'module': 'system', 'action': 'view', 'description': 'Can view audit logs'},
        ]
        
        created_count = 0
        updated_count = 0
        
        for perm_data in default_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {permission.name}')
                )
            else:
                # Update existing permission
                for key, value in perm_data.items():
                    if key != 'codename':
                        setattr(permission, key, value)
                permission.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated permission: {permission.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nPermission creation completed!\n'
                f'Created: {created_count} permissions\n'
                f'Updated: {updated_count} permissions\n'
                f'Total: {Permission.objects.count()} permissions'
            )
        )