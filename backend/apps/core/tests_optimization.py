"""
Tests for system optimization features
"""

from django.test import TestCase, TransactionTestCase
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.core.cache_utils import CacheManager, cache_result, generate_cache_key
from apps.core.db_optimization import QueryOptimizer, query_debugger, bulk_create_optimized
from apps.core.error_handlers import (
    HRMSException,
    BiometricVerificationError,
    retry_on_db_error
)
from apps.core.logging_utils import audit_logger, performance_logger
from apps.core.websocket_optimization import (
    message_batcher,
    connection_manager,
    performance_monitor,
    send_to_group_optimized
)
from apps.core.models import Company
from apps.employees.models import Employee, Department
from apps.attendance.models import AttendanceRecord
from datetime import date, datetime
import time

User = get_user_model()


class CacheUtilsTestCase(TestCase):
    """Test caching utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        cache.clear()
    
    def tearDown(self):
        """Clean up cache"""
        cache.clear()
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = generate_cache_key('test', 'arg1', 'arg2', param='value')
        key2 = generate_cache_key('test', 'arg1', 'arg2', param='value')
        key3 = generate_cache_key('test', 'arg1', 'arg3', param='value')
        
        # Same arguments should generate same key
        self.assertEqual(key1, key2)
        
        # Different arguments should generate different key
        self.assertNotEqual(key1, key3)
    
    def test_cache_result_decorator(self):
        """Test cache result decorator"""
        call_count = {'count': 0}
        
        @cache_result(timeout=60, key_prefix='test_func')
        def expensive_function(value):
            call_count['count'] += 1
            return value * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count['count'], 1)
        
        # Second call should use cache
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count['count'], 1)  # Not incremented
        
        # Different argument should execute function
        result3 = expensive_function(10)
        self.assertEqual(result3, 20)
        self.assertEqual(call_count['count'], 2)
    
    def test_cache_manager_employee_list(self):
        """Test CacheManager employee list caching"""
        company_id = str(self.company.id)
        test_data = [{'id': '1', 'name': 'John'}]
        
        # Set cache
        CacheManager.set_employee_list(company_id, test_data)
        
        # Get from cache
        cached_data = CacheManager.get_employee_list(company_id)
        self.assertEqual(cached_data, test_data)
        
        # Invalidate cache
        CacheManager.invalidate_employee_cache(company_id)
        
        # Should return None after invalidation
        cached_data = CacheManager.get_employee_list(company_id)
        self.assertIsNone(cached_data)
    
    def test_cache_manager_dashboard_metrics(self):
        """Test CacheManager dashboard metrics caching"""
        company_id = str(self.company.id)
        metrics = {
            'present_count': 100,
            'on_leave_count': 5
        }
        
        # Set cache
        CacheManager.set_dashboard_metrics(company_id, metrics)
        
        # Get from cache
        cached_metrics = CacheManager.get_dashboard_metrics(company_id)
        self.assertEqual(cached_metrics, metrics)


class DatabaseOptimizationTestCase(TransactionTestCase):
    """Test database optimization utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.department = Department.objects.create(
            name="Engineering",
            company=self.company
        )
        
        # Create test employees
        self.employees = []
        for i in range(5):
            employee = Employee.objects.create(
                employee_id=f"EMP{i:03d}",
                first_name=f"Employee{i}",
                last_name="Test",
                email=f"employee{i}@test.com",
                department=self.department,
                company=self.company,
                hire_date=date.today(),
                status='active'
            )
            self.employees.append(employee)
    
    def test_query_optimizer_employees(self):
        """Test QueryOptimizer for employees"""
        queryset = Employee.objects.filter(company=self.company)
        optimized = QueryOptimizer.get_employees_optimized(queryset)
        
        # Should have select_related applied
        self.assertIn('department', optimized.query.select_related)
        self.assertIn('company', optimized.query.select_related)
    
    def test_query_debugger(self):
        """Test query debugger context manager"""
        with query_debugger("Test Operation"):
            # Execute some queries
            employees = list(Employee.objects.filter(company=self.company))
            self.assertEqual(len(employees), 5)
        
        # Should complete without errors
        self.assertTrue(True)
    
    def test_bulk_create_optimized(self):
        """Test optimized bulk create"""
        new_employees = []
        for i in range(10):
            new_employees.append(
                Employee(
                    employee_id=f"BULK{i:03d}",
                    first_name=f"Bulk{i}",
                    last_name="Test",
                    email=f"bulk{i}@test.com",
                    department=self.department,
                    company=self.company,
                    hire_date=date.today(),
                    status='active'
                )
            )
        
        created = bulk_create_optimized(Employee, new_employees, batch_size=5)
        self.assertEqual(len(created), 10)
        
        # Verify all were created
        total_count = Employee.objects.filter(company=self.company).count()
        self.assertEqual(total_count, 15)  # 5 from setUp + 10 new


class ErrorHandlingTestCase(TestCase):
    """Test error handling utilities"""
    
    def test_custom_exception_creation(self):
        """Test custom exception classes"""
        exc = BiometricVerificationError(
            message="Test error",
            details={'confidence': 0.5}
        )
        
        self.assertEqual(exc.message, "Test error")
        self.assertEqual(exc.details['confidence'], 0.5)
        self.assertEqual(exc.status_code, 422)
    
    def test_retry_on_db_error(self):
        """Test retry decorator"""
        attempt_count = {'count': 0}
        
        @retry_on_db_error(max_retries=3, delay=0.1)
        def flaky_function():
            attempt_count['count'] += 1
            if attempt_count['count'] < 2:
                from django.db import OperationalError
                raise OperationalError("Connection lost")
            return "success"
        
        result = flaky_function()
        self.assertEqual(result, "success")
        self.assertEqual(attempt_count['count'], 2)


class LoggingUtilsTestCase(TestCase):
    """Test logging utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_audit_logger_log_action(self):
        """Test audit logger action logging"""
        # Should not raise any exceptions
        audit_logger.log_action(
            action='create',
            user=self.user,
            resource_type='employee',
            resource_id='test-id',
            details={'field': 'value'},
            company=self.company
        )
        
        self.assertTrue(True)
    
    def test_audit_logger_log_login(self):
        """Test audit logger login logging"""
        # Should not raise any exceptions
        audit_logger.log_login(
            user=self.user,
            success=True,
            ip_address='127.0.0.1'
        )
        
        self.assertTrue(True)
    
    def test_performance_logger_query_performance(self):
        """Test performance logger"""
        # Should not raise any exceptions
        performance_logger.log_query_performance(
            operation='test_query',
            query_count=5,
            duration_ms=45.2
        )
        
        self.assertTrue(True)


class WebSocketOptimizationTestCase(TestCase):
    """Test WebSocket optimization utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        # Clear any existing state
        message_batcher.batches.clear()
        connection_manager.connections.clear()
        performance_monitor.reset_stats()
    
    def test_message_batcher_add_message(self):
        """Test message batcher"""
        group_name = f"company_{self.company.id}"
        
        # Add messages
        for i in range(5):
            message_batcher.add_message(group_name, {'id': i})
        
        # Should have messages in batch
        self.assertEqual(len(message_batcher.batches[group_name]), 5)
        
        # Flush batch
        message_batcher.flush_group(group_name)
        
        # Batch should be empty after flush
        self.assertEqual(len(message_batcher.batches[group_name]), 0)
    
    def test_connection_manager(self):
        """Test connection manager"""
        group_name = f"company_{self.company.id}"
        channel_name = "test_channel_1"
        
        # Add connection
        connection_manager.add_connection(
            group_name,
            channel_name,
            metadata={'user_id': 'test'}
        )
        
        # Check connection count
        self.assertEqual(connection_manager.get_connection_count(group_name), 1)
        
        # Remove connection
        connection_manager.remove_connection(group_name, channel_name)
        
        # Should be 0 after removal
        self.assertEqual(connection_manager.get_connection_count(group_name), 0)
    
    def test_performance_monitor(self):
        """Test performance monitor"""
        group_name = f"company_{self.company.id}"
        
        # Record messages
        performance_monitor.record_message(group_name, latency_ms=50.0)
        performance_monitor.record_message(group_name, latency_ms=75.0)
        
        # Get stats
        stats = performance_monitor.get_stats(group_name)
        
        self.assertEqual(stats['message_count'], 2)
        self.assertEqual(stats['avg_latency_ms'], 62.5)
        self.assertEqual(stats['max_latency_ms'], 75.0)
        self.assertEqual(stats['min_latency_ms'], 50.0)


class IntegrationTestCase(TransactionTestCase):
    """Integration tests for optimization features"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.department = Department.objects.create(
            name="Engineering",
            company=self.company
        )
        
        cache.clear()
    
    def tearDown(self):
        """Clean up"""
        cache.clear()
    
    def test_end_to_end_employee_caching(self):
        """Test end-to-end employee caching workflow"""
        company_id = str(self.company.id)
        
        # Create employees
        employees = []
        for i in range(10):
            employees.append(
                Employee(
                    employee_id=f"EMP{i:03d}",
                    first_name=f"Employee{i}",
                    last_name="Test",
                    email=f"employee{i}@test.com",
                    department=self.department,
                    company=self.company,
                    hire_date=date.today(),
                    status='active'
                )
            )
        
        bulk_create_optimized(Employee, employees, batch_size=5)
        
        # Fetch with optimization
        queryset = Employee.objects.filter(company=self.company)
        optimized_queryset = QueryOptimizer.get_employees_optimized(queryset)
        
        # Convert to list for caching
        employee_list = list(optimized_queryset.values('id', 'employee_id', 'first_name'))
        
        # Cache the result
        CacheManager.set_employee_list(company_id, employee_list)
        
        # Retrieve from cache
        cached_list = CacheManager.get_employee_list(company_id)
        
        self.assertIsNotNone(cached_list)
        self.assertEqual(len(cached_list), 10)
        
        # Invalidate cache
        CacheManager.invalidate_employee_cache(company_id)
        
        # Should be None after invalidation
        cached_list = CacheManager.get_employee_list(company_id)
        self.assertIsNone(cached_list)
    
    def test_dashboard_optimization_workflow(self):
        """Test optimized dashboard data retrieval"""
        # Create test data
        employee = Employee.objects.create(
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            department=self.department,
            company=self.company,
            hire_date=date.today(),
            status='active'
        )
        
        AttendanceRecord.objects.create(
            employee=employee,
            company=self.company,
            date=date.today(),
            check_in=datetime.now(),
            status='present',
            biometric_verified=True
        )
        
        # Get optimized dashboard data
        dashboard_data = QueryOptimizer.get_dashboard_data_optimized(
            str(self.company.id),
            date.today()
        )
        
        self.assertEqual(dashboard_data['total_employees'], 1)
        self.assertEqual(dashboard_data['present_count'], 1)
        self.assertIn('date', dashboard_data)
        
        # Cache the dashboard data
        CacheManager.set_dashboard_metrics(
            str(self.company.id),
            dashboard_data,
            date=str(date.today())
        )
        
        # Retrieve from cache
        cached_data = CacheManager.get_dashboard_metrics(
            str(self.company.id),
            date=str(date.today())
        )
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['present_count'], 1)
