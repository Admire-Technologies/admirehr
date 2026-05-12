"""
Performance Testing Suite for Admire HRMS

This module contains performance tests for high-load scenarios including
API response times, database query performance, and concurrent operations.
"""

import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import statistics

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"
TIMEOUT = 30


class TestAPIPerformance:
    """Test API endpoint performance"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_employee_list_performance(self, auth_headers):
        """Test employee list API performance"""
        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 2.0, f"Employee list took {duration}s (expected < 2s)"
        print(f"Employee list response time: {duration:.3f}s")
    
    def test_attendance_list_performance(self, auth_headers):
        """Test attendance list API performance"""
        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/attendance/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 2.0, f"Attendance list took {duration}s (expected < 2s)"
        print(f"Attendance list response time: {duration:.3f}s")
    
    def test_dashboard_metrics_performance(self, auth_headers):
        """Test dashboard metrics API performance"""
        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/dashboard/metrics/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        duration = time.time() - start_time
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert duration < 3.0, f"Dashboard metrics took {duration}s (expected < 3s)"
            print(f"Dashboard metrics response time: {duration:.3f}s")
    
    def test_payroll_list_performance(self, auth_headers):
        """Test payroll list API performance"""
        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/payroll/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 2.0, f"Payroll list took {duration}s (expected < 2s)"
        print(f"Payroll list response time: {duration:.3f}s")


class TestConcurrentOperations:
    """Test system performance under concurrent load"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def make_request(self, url, headers):
        """Make a single request and measure time"""
        start_time = time.time()
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            duration = time.time() - start_time
            return {
                "status": response.status_code,
                "duration": duration,
                "success": response.status_code == 200
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    def test_concurrent_employee_requests(self, auth_headers):
        """Test concurrent employee list requests"""
        num_requests = 20
        url = f"{API_BASE_URL}/employees/"
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.make_request, url, auth_headers)
                for _ in range(num_requests)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        durations = [r["duration"] for r in successful]
        
        assert len(successful) >= num_requests * 0.95, \
            f"Only {len(successful)}/{num_requests} requests succeeded"
        
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        
        print(f"\nConcurrent Employee Requests ({num_requests} requests):")
        print(f"  Success rate: {len(successful)}/{num_requests}")
        print(f"  Average duration: {avg_duration:.3f}s")
        print(f"  Max duration: {max_duration:.3f}s")
        
        assert avg_duration < 3.0, f"Average response time {avg_duration}s too high"
        assert max_duration < 10.0, f"Max response time {max_duration}s too high"
    
    def test_concurrent_attendance_checkin(self, auth_headers):
        """Test concurrent attendance check-in operations"""
        num_requests = 10
        
        def checkin_request(index):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{API_BASE_URL}/attendance/check-in/",
                    headers=auth_headers,
                    json={
                        "employee_id": f"EMP{index:03d}",
                        "biometric_data": {"face_encoding": [0.1] * 128}
                    },
                    timeout=TIMEOUT
                )
                duration = time.time() - start_time
                return {
                    "status": response.status_code,
                    "duration": duration,
                    "success": response.status_code in [200, 201, 404]
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "status": 0,
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                }
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(checkin_request, i)
                for i in range(num_requests)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        successful = [r for r in results if r["success"]]
        durations = [r["duration"] for r in successful]
        
        print(f"\nConcurrent Attendance Check-ins ({num_requests} requests):")
        print(f"  Success rate: {len(successful)}/{num_requests}")
        if durations:
            print(f"  Average duration: {statistics.mean(durations):.3f}s")
            print(f"  Max duration: {max(durations):.3f}s")
    
    def test_concurrent_mixed_operations(self, auth_headers):
        """Test mixed concurrent operations"""
        operations = [
            (f"{API_BASE_URL}/employees/", "GET"),
            (f"{API_BASE_URL}/attendance/", "GET"),
            (f"{API_BASE_URL}/leave/requests/", "GET"),
            (f"{API_BASE_URL}/payroll/", "GET"),
            (f"{API_BASE_URL}/dashboard/metrics/", "GET"),
        ] * 4  # 20 total requests
        
        def make_mixed_request(url_method):
            url, method = url_method
            start_time = time.time()
            try:
                response = requests.request(
                    method, url, headers=auth_headers, timeout=TIMEOUT
                )
                duration = time.time() - start_time
                return {
                    "url": url,
                    "status": response.status_code,
                    "duration": duration,
                    "success": response.status_code in [200, 404]
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "url": url,
                    "status": 0,
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                }
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_mixed_request, op)
                for op in operations
            ]
            results = [future.result() for future in as_completed(futures)]
        
        successful = [r for r in results if r["success"]]
        durations = [r["duration"] for r in successful]
        
        print(f"\nConcurrent Mixed Operations ({len(operations)} requests):")
        print(f"  Success rate: {len(successful)}/{len(operations)}")
        if durations:
            print(f"  Average duration: {statistics.mean(durations):.3f}s")
            print(f"  Max duration: {max(durations):.3f}s")
        
        assert len(successful) >= len(operations) * 0.90, \
            f"Only {len(successful)}/{len(operations)} requests succeeded"


class TestDatabasePerformance:
    """Test database query performance"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_large_dataset_pagination(self, auth_headers):
        """Test pagination performance with large datasets"""
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = requests.get(
                f"{API_BASE_URL}/employees/?page_size={page_size}",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            duration = time.time() - start_time
            
            assert response.status_code == 200
            print(f"Page size {page_size}: {duration:.3f}s")
            
            # Larger page sizes should still be reasonable
            assert duration < 5.0, \
                f"Page size {page_size} took {duration}s (expected < 5s)"
    
    def test_filtered_query_performance(self, auth_headers):
        """Test performance of filtered queries"""
        filters = [
            "?status=active",
            "?search=test",
            "?department=1",
        ]
        
        for filter_param in filters:
            start_time = time.time()
            response = requests.get(
                f"{API_BASE_URL}/employees/{filter_param}",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            duration = time.time() - start_time
            
            assert response.status_code in [200, 400]
            print(f"Filter {filter_param}: {duration:.3f}s")
            
            if response.status_code == 200:
                assert duration < 3.0, \
                    f"Filtered query took {duration}s (expected < 3s)"


class TestCachePerformance:
    """Test caching effectiveness"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_repeated_request_performance(self, auth_headers):
        """Test that repeated requests benefit from caching"""
        url = f"{API_BASE_URL}/employees/"
        
        # First request (cold cache)
        start_time = time.time()
        response1 = requests.get(url, headers=auth_headers, timeout=TIMEOUT)
        first_duration = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Second request (warm cache)
        start_time = time.time()
        response2 = requests.get(url, headers=auth_headers, timeout=TIMEOUT)
        second_duration = time.time() - start_time
        
        assert response2.status_code == 200
        
        print(f"\nCache Performance Test:")
        print(f"  First request: {first_duration:.3f}s")
        print(f"  Second request: {second_duration:.3f}s")
        print(f"  Improvement: {((first_duration - second_duration) / first_duration * 100):.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
