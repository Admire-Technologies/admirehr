"""
GDPR compliance utilities for data export and deletion.

Implements right to access (data export) and right to be forgotten (data deletion)
as required by GDPR regulations.
"""

import json
import logging
from datetime import datetime
from django.core.serializers import serialize
from django.apps import apps
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


class GDPRCompliance:
    """
    Handles GDPR compliance operations for employee data.
    """
    
    def export_employee_data(self, employee):
        """
        Export all data related to an employee (Right to Access).
        
        Args:
            employee: Employee instance
        
        Returns:
            dict: Complete employee data in JSON format
        """
        from apps.employees.models import Employee
        from apps.attendance.models import AttendanceRecord
        from apps.leave_management.models import LeaveRequest
        from apps.payroll.models import PayrollRecord
        from apps.authentication.models import User, AuditLog
        
        data = {
            'export_date': datetime.now().isoformat(),
            'employee_id': str(employee.id),
            'personal_information': self._export_employee_personal_data(employee),
            'attendance_records': self._export_attendance_data(employee),
            'leave_requests': self._export_leave_data(employee),
            'payroll_records': self._export_payroll_data(employee),
            'user_account': self._export_user_account_data(employee),
            'audit_logs': self._export_audit_logs(employee),
        }
        
        return data
    
    def _export_employee_personal_data(self, employee):
        """Export employee personal information."""
        return {
            'employee_id': employee.employee_id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'email': employee.email,
            'phone': employee.phone,
            'department': employee.department.name if employee.department else None,
            'branch': employee.branch.name if employee.branch else None,
            'position': employee.position,
            'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
            'status': employee.status,
            'date_of_birth': employee.date_of_birth.isoformat() if employee.date_of_birth else None,
            'address': employee.address,
            'emergency_contact_name': employee.emergency_contact_name,
            'emergency_contact_phone': employee.emergency_contact_phone,
            'created_at': employee.created_at.isoformat() if hasattr(employee, 'created_at') else None,
            'updated_at': employee.updated_at.isoformat() if hasattr(employee, 'updated_at') else None,
        }
    
    def _export_attendance_data(self, employee):
        """Export attendance records."""
        from apps.attendance.models import AttendanceRecord
        
        records = AttendanceRecord.objects.filter(employee=employee).order_by('-date')
        
        return [
            {
                'date': record.date.isoformat(),
                'check_in': record.check_in.isoformat() if record.check_in else None,
                'check_out': record.check_out.isoformat() if record.check_out else None,
                'working_hours': str(record.working_hours) if record.working_hours else None,
                'status': record.status,
                'biometric_verified': record.biometric_verified,
            }
            for record in records
        ]
    
    def _export_leave_data(self, employee):
        """Export leave requests."""
        from apps.leave_management.models import LeaveRequest
        
        requests = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
        
        return [
            {
                'leave_type': request.leave_type.name if request.leave_type else None,
                'start_date': request.start_date.isoformat(),
                'end_date': request.end_date.isoformat(),
                'days_requested': request.days_requested,
                'status': request.status,
                'reason': request.reason if hasattr(request, 'reason') else None,
                'created_at': request.created_at.isoformat() if hasattr(request, 'created_at') else None,
            }
            for request in requests
        ]
    
    def _export_payroll_data(self, employee):
        """Export payroll records."""
        from apps.payroll.models import PayrollRecord
        
        records = PayrollRecord.objects.filter(employee=employee).order_by('-period_start')
        
        return [
            {
                'period_start': record.period_start.isoformat(),
                'period_end': record.period_end.isoformat(),
                'basic_salary': str(record.basic_salary),
                'allowances': str(record.allowances),
                'deductions': str(record.deductions),
                'net_salary': str(record.net_salary),
                'status': record.status if hasattr(record, 'status') else None,
            }
            for record in records
        ]
    
    def _export_user_account_data(self, employee):
        """Export user account information if exists."""
        from apps.authentication.models import User
        
        try:
            user = employee.user_account
            return {
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_company_admin': user.is_company_admin,
                'role': user.role.name if user.role else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            }
        except Exception:
            return None
    
    def _export_audit_logs(self, employee):
        """Export audit logs related to the employee."""
        from apps.authentication.models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        
        # Get audit logs where employee is the content object
        content_type = ContentType.objects.get_for_model(employee)
        logs = AuditLog.objects.filter(
            content_type=content_type,
            object_id=str(employee.id)
        ).order_by('-timestamp')[:100]  # Limit to last 100 logs
        
        return [
            {
                'action': log.action,
                'module': log.module,
                'description': log.description,
                'timestamp': log.timestamp.isoformat(),
                'user': log.user.username if log.user else 'System',
            }
            for log in logs
        ]
    
    def delete_employee_data(self, employee, anonymize=True):
        """
        Delete or anonymize employee data (Right to be Forgotten).
        
        Args:
            employee: Employee instance
            anonymize: If True, anonymize data instead of deleting (recommended for audit trail)
        
        Returns:
            dict: Summary of deletion/anonymization
        """
        from apps.attendance.models import AttendanceRecord
        from apps.leave_management.models import LeaveRequest
        from apps.payroll.models import PayrollRecord
        from apps.authentication.models import User
        
        summary = {
            'employee_id': str(employee.id),
            'anonymized': anonymize,
            'deleted_records': {},
            'anonymized_records': {},
        }
        
        if anonymize:
            # Anonymize employee data
            employee.first_name = f"Deleted_{employee.id}"
            employee.last_name = "User"
            employee.email = f"deleted_{employee.id}@anonymized.local"
            employee.phone = ""
            employee.address = ""
            employee.emergency_contact_name = ""
            employee.emergency_contact_phone = ""
            employee.date_of_birth = None
            employee.biometric_data = None
            employee.status = 'terminated'
            employee.save()
            
            summary['anonymized_records']['employee'] = 1
            
            # Anonymize user account if exists
            try:
                user = employee.user_account
                user.username = f"deleted_{user.id}"
                user.email = f"deleted_{user.id}@anonymized.local"
                user.is_active = False
                user.save()
                summary['anonymized_records']['user_account'] = 1
            except Exception:
                pass
            
            # Keep attendance, leave, and payroll records for audit purposes
            # but they're now linked to an anonymized employee
            summary['anonymized_records']['attendance_records'] = AttendanceRecord.objects.filter(employee=employee).count()
            summary['anonymized_records']['leave_requests'] = LeaveRequest.objects.filter(employee=employee).count()
            summary['anonymized_records']['payroll_records'] = PayrollRecord.objects.filter(employee=employee).count()
        
        else:
            # Hard delete (not recommended due to audit trail requirements)
            summary['deleted_records']['attendance_records'] = AttendanceRecord.objects.filter(employee=employee).delete()[0]
            summary['deleted_records']['leave_requests'] = LeaveRequest.objects.filter(employee=employee).delete()[0]
            summary['deleted_records']['payroll_records'] = PayrollRecord.objects.filter(employee=employee).delete()[0]
            
            # Delete user account
            try:
                user = employee.user_account
                summary['deleted_records']['user_account'] = 1
                user.delete()
            except Exception:
                pass
            
            # Delete employee
            employee.delete()
            summary['deleted_records']['employee'] = 1
        
        logger.info(f"GDPR data deletion/anonymization completed for employee {employee.id}: {summary}")
        
        return summary
    
    def generate_data_processing_report(self, company):
        """
        Generate a report of data processing activities for GDPR compliance.
        
        Args:
            company: Company instance
        
        Returns:
            dict: Data processing report
        """
        from apps.employees.models import Employee
        from apps.attendance.models import AttendanceRecord
        from apps.authentication.models import AuditLog
        
        report = {
            'company': company.name,
            'report_date': datetime.now().isoformat(),
            'data_categories': {
                'employees': {
                    'total': Employee.objects.filter(company=company).count(),
                    'active': Employee.objects.filter(company=company, status='active').count(),
                    'data_types': [
                        'Personal identification',
                        'Contact information',
                        'Employment details',
                        'Biometric data (face recognition)',
                    ]
                },
                'attendance_records': {
                    'total': AttendanceRecord.objects.filter(company=company).count(),
                    'data_types': [
                        'Biometric verification data',
                        'Time and location data',
                    ]
                },
                'audit_logs': {
                    'total': AuditLog.objects.filter(company=company).count(),
                    'data_types': [
                        'User activity logs',
                        'Data modification history',
                    ]
                }
            },
            'security_measures': [
                'Data encryption for sensitive information',
                'JWT-based authentication',
                'Role-based access control',
                'Audit logging for all data modifications',
                'Secure password policies',
                'Rate limiting and intrusion detection',
            ],
            'data_retention': {
                'employee_records': 'Retained while employed + 7 years after termination',
                'attendance_records': 'Retained for 3 years',
                'payroll_records': 'Retained for 7 years (legal requirement)',
                'audit_logs': 'Retained for 1 year',
            }
        }
        
        return report


# Singleton instance
_gdpr_instance = None


def get_gdpr_compliance():
    """
    Get singleton instance of GDPRCompliance.
    
    Returns:
        GDPRCompliance instance
    """
    global _gdpr_instance
    if _gdpr_instance is None:
        _gdpr_instance = GDPRCompliance()
    return _gdpr_instance
