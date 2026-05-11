"""
Dashboard services for metrics calculation and report generation.
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from django.db.models import Count, Q, Sum, Avg, F
from django.utils import timezone
from apps.core.models import Company
from apps.employees.models import Employee
from apps.attendance.models import AttendanceRecord
from apps.leave_management.models import LeaveRequest
from apps.payroll.models import PayrollRecord


class DashboardMetricsService:
    """Service for calculating real-time dashboard metrics."""
    
    def __init__(self, company: Company):
        self.company = company
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics."""
        today = timezone.now().date()
        
        # Present employees (checked in today and not checked out)
        present_count = AttendanceRecord.objects.filter(
            company=self.company,
            date=today,
            check_in__isnull=False,
            check_out__isnull=True
        ).count()
        
        # Employees on leave today
        on_leave_count = LeaveRequest.objects.filter(
            company=self.company,
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).count()
        
        # Pending leave requests
        pending_requests = LeaveRequest.objects.filter(
            company=self.company,
            status='pending'
        ).count()
        
        # Total employees
        total_employees = Employee.objects.filter(
            company=self.company,
            status='active'
        ).count()

        
        # Absent employees (not present and not on leave)
        absent_count = total_employees - present_count - on_leave_count
        
        return {
            'present_count': present_count,
            'on_leave_count': on_leave_count,
            'absent_count': max(0, absent_count),
            'pending_requests': pending_requests,
            'total_employees': total_employees,
            'timestamp': timezone.now().isoformat()
        }
    
    def get_attendance_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get attendance trends for the specified number of days."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            present = AttendanceRecord.objects.filter(
                company=self.company,
                date=current_date,
                check_in__isnull=False
            ).count()
            
            on_leave = LeaveRequest.objects.filter(
                company=self.company,
                status='approved',
                start_date__lte=current_date,
                end_date__gte=current_date
            ).count()
            
            trends.append({
                'date': current_date.isoformat(),
                'present': present,
                'on_leave': on_leave,
                'absent': max(0, Employee.objects.filter(
                    company=self.company, status='active'
                ).count() - present - on_leave)
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    def get_leave_patterns(self, months: int = 6) -> List[Dict[str, Any]]:
        """Get leave patterns for the specified number of months."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=months * 30)

        
        leave_data = LeaveRequest.objects.filter(
            company=self.company,
            start_date__gte=start_date,
            start_date__lte=end_date
        ).values('leave_type__name').annotate(
            count=Count('id'),
            total_days=Sum('days_requested')
        ).order_by('-count')
        
        return list(leave_data)
    
    def get_payroll_summary(self, period_start: date, period_end: date) -> Dict[str, Any]:
        """Get payroll summary for the specified period."""
        payroll_records = PayrollRecord.objects.filter(
            company=self.company,
            period_start__gte=period_start,
            period_end__lte=period_end
        )
        
        summary = payroll_records.aggregate(
            total_basic_salary=Sum('basic_salary'),
            total_allowances=Sum('allowances'),
            total_deductions=Sum('deductions'),
            total_net_salary=Sum('net_salary'),
            employee_count=Count('employee', distinct=True),
            avg_salary=Avg('net_salary')
        )
        
        # Department-wise breakdown
        dept_breakdown = payroll_records.values(
            'employee__department__name'
        ).annotate(
            count=Count('id'),
            total=Sum('net_salary')
        ).order_by('-total')
        
        return {
            'summary': summary,
            'department_breakdown': list(dept_breakdown),
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat()
        }


class ReportGenerationService:
    """Service for generating various reports with filtering and export."""
    
    def __init__(self, company: Company):
        self.company = company

    
    def generate_attendance_report(
        self,
        start_date: date,
        end_date: date,
        department_id: Optional[str] = None,
        employee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate attendance report with filters."""
        queryset = AttendanceRecord.objects.filter(
            company=self.company,
            date__gte=start_date,
            date__lte=end_date
        )
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Calculate statistics
        total_records = queryset.count()
        present_days = queryset.filter(check_in__isnull=False).count()
        total_hours = queryset.aggregate(
            total=Sum('working_hours')
        )['total'] or 0
        
        # Group by employee
        employee_summary = queryset.values(
            'employee__id',
            'employee__first_name',
            'employee__last_name',
            'employee__employee_id',
            'employee__department__name'
        ).annotate(
            days_present=Count('id', filter=Q(check_in__isnull=False)),
            total_hours=Sum('working_hours'),
            avg_hours=Avg('working_hours')
        ).order_by('employee__first_name')
        
        return {
            'summary': {
                'total_records': total_records,
                'present_days': present_days,
                'total_hours': float(total_hours),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'employee_data': list(employee_summary)
        }

    
    def generate_leave_report(
        self,
        start_date: date,
        end_date: date,
        department_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate leave report with filters."""
        queryset = LeaveRequest.objects.filter(
            company=self.company,
            start_date__gte=start_date,
            end_date__lte=end_date
        )
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        # Calculate statistics
        total_requests = queryset.count()
        approved_requests = queryset.filter(status='approved').count()
        pending_requests = queryset.filter(status='pending').count()
        rejected_requests = queryset.filter(status='rejected').count()
        total_days = queryset.aggregate(total=Sum('days_requested'))['total'] or 0
        
        # Group by leave type
        leave_type_summary = queryset.values(
            'leave_type__name'
        ).annotate(
            count=Count('id'),
            total_days=Sum('days_requested')
        ).order_by('-count')
        
        # Group by employee
        employee_summary = queryset.values(
            'employee__id',
            'employee__first_name',
            'employee__last_name',
            'employee__employee_id',
            'employee__department__name'
        ).annotate(
            total_requests=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            total_days=Sum('days_requested')
        ).order_by('employee__first_name')
        
        return {
            'summary': {
                'total_requests': total_requests,
                'approved': approved_requests,
                'pending': pending_requests,
                'rejected': rejected_requests,
                'total_days': total_days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'leave_type_data': list(leave_type_summary),
            'employee_data': list(employee_summary)
        }
