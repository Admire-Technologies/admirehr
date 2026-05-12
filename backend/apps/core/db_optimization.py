"""
Database optimization utilities for Admire HRMS
Provides query optimization helpers and database performance monitoring
"""

from django.db import connection
from django.db.models import Prefetch, Q
from contextlib import contextmanager
import time
import logging

logger = logging.getLogger(__name__)


@contextmanager
def query_debugger(operation_name: str = "Database Operation"):
    """
    Context manager to log query count and execution time
    
    Usage:
        with query_debugger("Employee List Query"):
            employees = Employee.objects.select_related('department').all()
    """
    queries_before = len(connection.queries)
    start_time = time.time()
    
    try:
        yield
    finally:
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(
            f"{operation_name} - Queries: {query_count}, Time: {execution_time:.2f}ms"
        )
        
        # Log slow queries (> 100ms)
        if execution_time > 100:
            logger.warning(
                f"Slow query detected in {operation_name}: {execution_time:.2f}ms"
            )


class QueryOptimizer:
    """
    Provides optimized querysets for common data access patterns
    """
    
    @staticmethod
    def get_employees_optimized(queryset):
        """
        Optimize employee queryset with select_related and prefetch_related
        
        Args:
            queryset: Base employee queryset
        
        Returns:
            Optimized queryset with related data preloaded
        """
        return queryset.select_related(
            'department',
            'department__parent',
            'company',
            'user',
            'user__role'
        ).prefetch_related(
            'user__role__permissions'
        )
    
    @staticmethod
    def get_attendance_records_optimized(queryset):
        """
        Optimize attendance records queryset
        
        Args:
            queryset: Base attendance queryset
        
        Returns:
            Optimized queryset with related data preloaded
        """
        return queryset.select_related(
            'employee',
            'employee__department',
            'company'
        ).order_by('-date', '-check_in')
    
    @staticmethod
    def get_leave_requests_optimized(queryset):
        """
        Optimize leave requests queryset
        
        Args:
            queryset: Base leave request queryset
        
        Returns:
            Optimized queryset with related data preloaded
        """
        return queryset.select_related(
            'employee',
            'employee__department',
            'leave_type',
            'approver',
            'company'
        ).order_by('-created_at')
    
    @staticmethod
    def get_payroll_records_optimized(queryset):
        """
        Optimize payroll records queryset
        
        Args:
            queryset: Base payroll queryset
        
        Returns:
            Optimized queryset with related data preloaded
        """
        return queryset.select_related(
            'employee',
            'employee__department',
            'company'
        ).prefetch_related(
            'salary_components'
        ).order_by('-period_start')
    
    @staticmethod
    def get_dashboard_data_optimized(company_id: str, date=None):
        """
        Get optimized dashboard data with minimal queries
        
        Args:
            company_id: Company ID to filter by
            date: Optional date for filtering (defaults to today)
        
        Returns:
            Dictionary with dashboard metrics
        """
        from django.db.models import Count, Sum, Avg
        from apps.employees.models import Employee
        from apps.attendance.models import AttendanceRecord
        from apps.leave_management.models import LeaveRequest
        from datetime import date as date_module
        
        if date is None:
            date = date_module.today()
        
        # Single query for employee counts
        employee_stats = Employee.objects.filter(
            company_id=company_id,
            status='active'
        ).aggregate(
            total_employees=Count('id')
        )
        
        # Single query for attendance stats
        attendance_stats = AttendanceRecord.objects.filter(
            company_id=company_id,
            date=date
        ).aggregate(
            present_count=Count('id', filter=Q(status='present')),
            late_count=Count('id', filter=Q(status='late')),
            absent_count=Count('id', filter=Q(status='absent'))
        )
        
        # Single query for leave stats
        leave_stats = LeaveRequest.objects.filter(
            company_id=company_id,
            start_date__lte=date,
            end_date__gte=date
        ).aggregate(
            on_leave_count=Count('id', filter=Q(status='approved'))
        )
        
        # Single query for pending leave requests
        pending_leaves = LeaveRequest.objects.filter(
            company_id=company_id,
            status='pending'
        ).count()
        
        return {
            'total_employees': employee_stats['total_employees'] or 0,
            'present_count': attendance_stats['present_count'] or 0,
            'late_count': attendance_stats['late_count'] or 0,
            'absent_count': attendance_stats['absent_count'] or 0,
            'on_leave_count': leave_stats['on_leave_count'] or 0,
            'pending_leaves': pending_leaves,
            'date': date.isoformat()
        }


class DatabaseIndexManager:
    """
    Manages database indexes for optimal query performance
    """
    
    @staticmethod
    def get_recommended_indexes():
        """
        Returns list of recommended database indexes
        
        These should be added to model Meta classes or via migrations
        """
        return {
            'employees': [
                ('company_id', 'status'),  # Composite index for active employees
                ('company_id', 'department_id'),  # Department filtering
                ('employee_id',),  # Employee ID lookup
                ('email',),  # Email lookup
            ],
            'attendance_records': [
                ('company_id', 'date'),  # Daily attendance queries
                ('employee_id', 'date'),  # Employee attendance history
                ('company_id', 'date', 'status'),  # Status filtering
                ('date', 'check_in'),  # Time-based queries
            ],
            'leave_requests': [
                ('company_id', 'status'),  # Pending requests
                ('employee_id', 'status'),  # Employee leave history
                ('company_id', 'start_date', 'end_date'),  # Date range queries
                ('approver_id', 'status'),  # Approver's pending requests
            ],
            'payroll_records': [
                ('company_id', 'period_start', 'period_end'),  # Period queries
                ('employee_id', 'period_start'),  # Employee payroll history
            ],
            'users': [
                ('company_id', 'is_active'),  # Active users
                ('email',),  # Login lookup
            ],
            'departments': [
                ('company_id',),  # Company departments
                ('parent_id',),  # Hierarchical queries
            ],
        }
    
    @staticmethod
    def analyze_query_performance(sql_query: str):
        """
        Analyze query performance using EXPLAIN
        
        Args:
            sql_query: SQL query to analyze
        
        Returns:
            Query execution plan
        """
        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN ANALYZE {sql_query}")
            return cursor.fetchall()


def bulk_create_optimized(model_class, objects, batch_size=1000):
    """
    Optimized bulk create with batching
    
    Args:
        model_class: Django model class
        objects: List of model instances to create
        batch_size: Number of objects per batch
    
    Returns:
        List of created objects
    """
    created_objects = []
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        created_batch = model_class.objects.bulk_create(
            batch,
            ignore_conflicts=False
        )
        created_objects.extend(created_batch)
        
        logger.info(f"Bulk created {len(created_batch)} {model_class.__name__} objects")
    
    return created_objects


def bulk_update_optimized(model_class, objects, fields, batch_size=1000):
    """
    Optimized bulk update with batching
    
    Args:
        model_class: Django model class
        objects: List of model instances to update
        fields: List of field names to update
        batch_size: Number of objects per batch
    """
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        model_class.objects.bulk_update(batch, fields, batch_size=batch_size)
        
        logger.info(f"Bulk updated {len(batch)} {model_class.__name__} objects")
