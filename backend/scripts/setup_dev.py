#!/usr/bin/env python
"""
Development setup script for Admire HRMS.
This script creates initial data for development.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admire_hrms.settings')
django.setup()

from apps.core.models import Company
from apps.authentication.models import User, Role
from apps.employees.models import Department, Employee
from django.contrib.auth.models import Permission


def create_sample_data():
    """Create sample data for development."""
    
    # Create a sample company
    company, created = Company.objects.get_or_create(
        code='DEMO',
        defaults={
            'name': 'Demo Company',
            'settings': {
                'working_hours_per_day': 8,
                'working_days_per_week': 5,
            }
        }
    )
    
    if created:
        print(f"Created company: {company.name}")
    
    # Create admin role
    admin_role, created = Role.objects.get_or_create(
        name='Admin',
        company=company,
        defaults={'description': 'Full system access'}
    )
    
    if created:
        # Add all permissions to admin role
        admin_role.permissions.set(Permission.objects.all())
        print(f"Created admin role: {admin_role.name}")
    
    # Create HR role
    hr_role, created = Role.objects.get_or_create(
        name='HR Manager',
        company=company,
        defaults={'description': 'HR management access'}
    )
    
    if created:
        print(f"Created HR role: {hr_role.name}")
    
    # Create sample departments
    it_dept, created = Department.objects.get_or_create(
        name='Information Technology',
        company=company,
        defaults={'description': 'IT Department'}
    )
    
    hr_dept, created = Department.objects.get_or_create(
        name='Human Resources',
        company=company,
        defaults={'description': 'HR Department'}
    )
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        company=company,
        defaults={
            'email': 'admin@demo.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': admin_role,
            'is_company_admin': True,
            'is_staff': True,
        }
    )
    
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"Created admin user: {admin_user.username}")
    
    # Create sample employee
    sample_employee, created = Employee.objects.get_or_create(
        employee_id='EMP001',
        company=company,
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@demo.com',
            'department': it_dept,
            'position': 'Software Developer',
            'hire_date': '2024-01-01',
        }
    )
    
    if created:
        print(f"Created sample employee: {sample_employee.full_name}")
    
    print("Sample data creation completed!")


if __name__ == '__main__':
    create_sample_data()