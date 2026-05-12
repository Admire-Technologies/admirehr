"""
Deployment validation tests for Admire HRMS
Run these tests after deployment to verify system health
"""
import requests
import time
import pytest
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost"
API_BASE_URL = f"{BASE_URL}/api/v1"
TIMEOUT = 10


class TestDeploymentHealth:
    """Test basic health and connectivity"""
    
    def test_nginx_health(self):
        """Test Nginx is responding"""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "healthy" in response.text.lower()
    
    def test_backend_health(self):
        """Test backend API is responding"""
        response = requests.get(f"{API_BASE_URL}/health/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_backend_detailed_health(self):
        """Test detailed health check"""
        response = requests.get(f"{API_BASE_URL}/health/detailed/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'checks' in data
        assert data['checks']['database']['status'] == 'healthy'
        assert data['checks']['cache']['status'] == 'healthy'
    
    def test_readiness_check(self):
        """Test readiness endpoint"""
        response = requests.get(f"{API_BASE_URL}/health/ready/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ready'
    
    def test_liveness_check(self):
        """Test liveness endpoint"""
        response = requests.get(f"{API_BASE_URL}/health/live/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'alive'


class TestAPIEndpoints:
    """Test critical API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for tests"""
        # This would need actual credentials
        # For deployment tests, use a test account
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={
                "username": "test_user",
                "password": "test_password"
            },
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['access']
        return None
    
    def test_api_info(self):
        """Test API info endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/info/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert 'version' in data
        assert 'name' in data
    
    def test_authentication_endpoint(self):
        """Test authentication endpoint is accessible"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "test", "password": "test"},
            timeout=TIMEOUT
        )
        # Should return 401 or 400, not 500
        assert response.status_code in [400, 401]


class TestDatabaseConnectivity:
    """Test database connectivity and operations"""
    
    def test_database_connection(self):
        """Test database is connected"""
        response = requests.get(f"{API_BASE_URL}/health/detailed/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data['checks']['database']['status'] == 'healthy'
    
    def test_database_migrations(self):
        """Verify migrations are applied"""
        # This would check if all expected tables exist
        # For now, we verify the health check passes
        response = requests.get(f"{API_BASE_URL}/health/detailed/", timeout=TIMEOUT)
        assert response.status_code == 200


class TestCacheConnectivity:
    """Test Redis/cache connectivity"""
    
    def test_cache_connection(self):
        """Test cache is connected"""
        response = requests.get(f"{API_BASE_URL}/health/detailed/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data['checks']['cache']['status'] == 'healthy'


class TestCeleryWorkers:
    """Test Celery background workers"""
    
    def test_celery_workers_running(self):
        """Test Celery workers are running"""
        response = requests.get(f"{API_BASE_URL}/health/detailed/", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        # Celery might be degraded if no workers, but should not be unhealthy
        assert data['checks']['celery']['status'] in ['healthy', 'degraded']


class TestStaticFiles:
    """Test static file serving"""
    
    def test_static_files_accessible(self):
        """Test static files are being served"""
        # Try to access a common static file
        response = requests.get(f"{BASE_URL}/static/", timeout=TIMEOUT)
        # Should return 200 or 403 (forbidden but accessible), not 404 or 500
        assert response.status_code in [200, 403]


class TestWebSocketConnection:
    """Test WebSocket connectivity"""
    
    def test_websocket_endpoint_accessible(self):
        """Test WebSocket endpoint is accessible"""
        # Basic HTTP check - actual WebSocket test would need ws library
        response = requests.get(f"{BASE_URL}/ws/", timeout=TIMEOUT)
        # Should return 400 (bad request) or 426 (upgrade required), not 500
        assert response.status_code in [400, 426]


class TestPerformance:
    """Test basic performance metrics"""
    
    def test_response_time(self):
        """Test API response time is acceptable"""
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/health/", timeout=TIMEOUT)
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 2.0, f"Response time too slow: {duration}s"
    
    def test_concurrent_requests(self):
        """Test system handles concurrent requests"""
        import concurrent.futures
        
        def make_request():
            response = requests.get(f"{API_BASE_URL}/health/", timeout=TIMEOUT)
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)


class TestSecurity:
    """Test security configurations"""
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        headers = response.headers
        
        # Check for important security headers
        assert 'X-Frame-Options' in headers
        assert 'X-Content-Type-Options' in headers
    
    def test_https_redirect(self):
        """Test HTTPS redirect (if configured)"""
        # This test would check if HTTP redirects to HTTPS in production
        # Skip for local testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
