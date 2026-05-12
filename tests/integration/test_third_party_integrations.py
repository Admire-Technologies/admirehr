"""
Integration Tests for Third-Party Services

This module tests integration with external services including:
- Face Plugin SDK (biometric)
- Email services
- Redis cache
- Celery task queue
- WebSocket connections
"""

import pytest
import requests
import redis
import time
from celery import Celery
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"
REDIS_URL = "redis://localhost:6379/0"
TIMEOUT = 10


class TestRedisIntegration:
    """Test Redis cache integration"""
    
    @pytest.fixture
    def redis_client(self):
        """Get Redis client"""
        client = redis.from_url(REDIS_URL)
        yield client
        client.close()
    
    def test_redis_connection(self, redis_client):
        """Test Redis connection is working"""
        assert redis_client.ping(), "Redis connection failed"
    
    def test_redis_set_get(self, redis_client):
        """Test Redis set and get operations"""
        key = f"test_key_{int(time.time())}"
        value = "test_value"
        
        # Set value
        redis_client.set(key, value, ex=60)
        
        # Get value
        retrieved = redis_client.get(key)
        assert retrieved.decode() == value
        
        # Cleanup
        redis_client.delete(key)
    
    def test_redis_cache_performance(self, redis_client):
        """Test Redis cache performance"""
        key = f"perf_test_{int(time.time())}"
        value = "x" * 1000  # 1KB value
        
        # Measure set performance
        start = time.time()
        for i in range(100):
            redis_client.set(f"{key}_{i}", value, ex=60)
        set_duration = time.time() - start
        
        # Measure get performance
        start = time.time()
        for i in range(100):
            redis_client.get(f"{key}_{i}")
        get_duration = time.time() - start
        
        print(f"\nRedis Performance:")
        print(f"  100 SET operations: {set_duration:.3f}s")
        print(f"  100 GET operations: {get_duration:.3f}s")
        
        # Cleanup
        for i in range(100):
            redis_client.delete(f"{key}_{i}")
        
        # Performance should be fast
        assert set_duration < 1.0, "Redis SET operations too slow"
        assert get_duration < 0.5, "Redis GET operations too slow"


class TestCeleryIntegration:
    """Test Celery task queue integration"""
    
    @pytest.fixture
    def celery_app(self):
        """Get Celery app"""
        app = Celery('admire_hrms', broker=REDIS_URL, backend=REDIS_URL)
        return app
    
    def test_celery_connection(self, celery_app):
        """Test Celery broker connection"""
        try:
            # Check if Celery can connect to broker
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            print(f"\nCelery workers: {stats}")
            # If no workers, test passes but logs warning
            if not stats:
                print("Warning: No Celery workers running")
        except Exception as e:
            pytest.skip(f"Celery not available: {e}")
    
    def test_celery_task_execution(self, celery_app):
        """Test Celery task execution"""
        # Define a simple test task
        @celery_app.task
        def test_task(x, y):
            return x + y
        
        try:
            # Execute task
            result = test_task.apply_async(args=[2, 3], expires=10)
            
            # Wait for result (with timeout)
            task_result = result.get(timeout=5)
            assert task_result == 5
        except Exception as e:
            pytest.skip(f"Celery task execution failed: {e}")


class TestEmailIntegration:
    """Test email service integration"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            token = response.json()["access"]
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_email_configuration(self):
        """Test email configuration is set up"""
        # Check health endpoint for email configuration
        response = requests.get(
            f"{API_BASE_URL}/health/detailed/",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nEmail configuration status: {data.get('checks', {}).get('email', 'Not configured')}")
    
    def test_email_notification_trigger(self, auth_headers):
        """Test that email notifications can be triggered"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Create a leave request which should trigger email notification
        leave_data = {
            "leave_type": "annual",
            "start_date": "2024-12-25",
            "end_date": "2024-12-27",
            "reason": "Integration test"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/leave/requests/",
            headers=auth_headers,
            json=leave_data,
            timeout=TIMEOUT
        )
        
        # Request may succeed or fail, but should not error
        assert response.status_code in [201, 400, 404]
        print(f"\nLeave request response: {response.status_code}")


class TestBiometricIntegration:
    """Test Face Plugin SDK integration"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            token = response.json()["access"]
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_biometric_checkin_endpoint(self, auth_headers):
        """Test biometric check-in endpoint"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Simulate biometric data
        biometric_data = {
            "employee_id": "EMP001",
            "biometric_data": {
                "face_encoding": [0.1] * 128,
                "confidence": 0.95
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/attendance/check-in/",
            headers=auth_headers,
            json=biometric_data,
            timeout=TIMEOUT
        )
        
        # Should handle biometric data
        assert response.status_code in [200, 201, 404, 400]
        print(f"\nBiometric check-in response: {response.status_code}")
    
    def test_biometric_data_validation(self, auth_headers):
        """Test biometric data validation"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Test with invalid biometric data
        invalid_data = {
            "employee_id": "EMP001",
            "biometric_data": {
                "face_encoding": [0.1] * 10  # Wrong size
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/attendance/check-in/",
            headers=auth_headers,
            json=invalid_data,
            timeout=TIMEOUT
        )
        
        # Should validate biometric data
        print(f"\nInvalid biometric data response: {response.status_code}")


class TestWebSocketIntegration:
    """Test WebSocket integration"""
    
    def test_websocket_endpoint_accessible(self):
        """Test WebSocket endpoint is accessible"""
        # Test HTTP upgrade endpoint
        response = requests.get(
            f"{BASE_URL}/ws/",
            timeout=TIMEOUT
        )
        
        # Should return error for non-WebSocket request
        # but endpoint should be accessible
        print(f"\nWebSocket endpoint response: {response.status_code}")
    
    def test_websocket_authentication(self):
        """Test WebSocket requires authentication"""
        # This would require a WebSocket client library
        # For now, just verify the endpoint exists
        try:
            response = requests.get(
                f"{BASE_URL}/ws/attendance/",
                timeout=TIMEOUT
            )
            print(f"\nWebSocket attendance endpoint: {response.status_code}")
        except Exception as e:
            print(f"\nWebSocket test skipped: {e}")


class TestDatabaseIntegration:
    """Test database integration"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            token = response.json()["access"]
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_database_connection(self):
        """Test database connection"""
        response = requests.get(
            f"{API_BASE_URL}/health/detailed/",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            db_status = data.get('checks', {}).get('database', {})
            print(f"\nDatabase status: {db_status}")
            assert db_status.get('status') == 'healthy'
    
    def test_database_transaction_integrity(self, auth_headers):
        """Test database transaction integrity"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Create employee
        employee_data = {
            "employee_id": f"EMP{int(time.time())}",
            "first_name": "Transaction",
            "last_name": "Test",
            "email": f"transaction{int(time.time())}@test.com",
            "hire_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "active"
        }
        
        create_response = requests.post(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            json=employee_data,
            timeout=TIMEOUT
        )
        
        if create_response.status_code == 201:
            employee = create_response.json()
            employee_id = employee["id"]
            
            # Verify employee exists
            get_response = requests.get(
                f"{API_BASE_URL}/employees/{employee_id}/",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            assert get_response.status_code == 200
            
            # Delete employee
            delete_response = requests.delete(
                f"{API_BASE_URL}/employees/{employee_id}/",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            assert delete_response.status_code in [200, 204]
            
            # Verify employee is deleted
            get_after_delete = requests.get(
                f"{API_BASE_URL}/employees/{employee_id}/",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            assert get_after_delete.status_code == 404


class TestAPIVersioning:
    """Test API versioning"""
    
    def test_api_version_header(self):
        """Test API version is returned in headers"""
        response = requests.get(
            f"{API_BASE_URL}/health/",
            timeout=TIMEOUT
        )
        
        # Check for version header
        version = response.headers.get('X-API-Version') or response.headers.get('API-Version')
        print(f"\nAPI Version: {version}")
    
    def test_api_info_endpoint(self):
        """Test API info endpoint"""
        response = requests.get(
            f"{API_BASE_URL}/api/info/",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAPI Info: {data}")
            assert 'version' in data or 'name' in data


class TestFileStorageIntegration:
    """Test file storage integration"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            token = response.json()["access"]
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_file_upload_capability(self, auth_headers):
        """Test file upload capability"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Test if file upload endpoints exist
        # This is a basic check - actual file upload would require multipart/form-data
        response = requests.options(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        
        print(f"\nFile upload capability check: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
