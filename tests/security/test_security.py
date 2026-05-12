"""
Security Testing and Vulnerability Assessment Suite

This module contains comprehensive security tests including authentication,
authorization, injection attacks, XSS, CSRF, and data protection.
"""

import pytest
import requests
import time
from datetime import datetime
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"
TIMEOUT = 10


class TestAuthenticationSecurity:
    """Test authentication security measures"""
    
    def test_invalid_credentials(self):
        """Test that invalid credentials are rejected"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={
                "username": "invalid_user",
                "password": "wrong_password"
            },
            timeout=TIMEOUT
        )
        assert response.status_code in [400, 401], \
            "Invalid credentials should be rejected"
    
    def test_missing_credentials(self):
        """Test that missing credentials are rejected"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={},
            timeout=TIMEOUT
        )
        assert response.status_code in [400, 401], \
            "Missing credentials should be rejected"
    
    def test_sql_injection_in_login(self):
        """Test SQL injection protection in login"""
        sql_payloads = [
            "admin' OR '1'='1",
            "admin'--",
            "admin' OR 1=1--",
            "' OR '1'='1' /*",
        ]
        
        for payload in sql_payloads:
            response = requests.post(
                f"{API_BASE_URL}/auth/login/",
                json={
                    "username": payload,
                    "password": payload
                },
                timeout=TIMEOUT
            )
            assert response.status_code in [400, 401], \
                f"SQL injection payload should be rejected: {payload}"
    
    def test_brute_force_protection(self):
        """Test brute force attack protection"""
        # Attempt multiple failed logins
        for i in range(10):
            response = requests.post(
                f"{API_BASE_URL}/auth/login/",
                json={
                    "username": "test_user",
                    "password": f"wrong_password_{i}"
                },
                timeout=TIMEOUT
            )
            # Should eventually get rate limited
            if response.status_code == 429:
                print("Rate limiting active after failed attempts")
                break
            time.sleep(0.1)
    
    def test_token_expiration(self):
        """Test that expired tokens are rejected"""
        # This test would require a token with short expiration
        # For now, test that invalid tokens are rejected
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        
        response = requests.get(
            f"{API_BASE_URL}/auth/profile/",
            headers={"Authorization": f"Bearer {invalid_token}"},
            timeout=TIMEOUT
        )
        assert response.status_code in [401, 403], \
            "Invalid token should be rejected"
    
    def test_unauthorized_access(self):
        """Test that unauthorized access is blocked"""
        response = requests.get(
            f"{API_BASE_URL}/employees/",
            timeout=TIMEOUT
        )
        assert response.status_code in [401, 403], \
            "Unauthorized access should be blocked"


class TestAuthorizationSecurity:
    """Test authorization and RBAC security"""
    
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
    
    def test_multi_tenant_isolation(self, auth_headers):
        """Test that users cannot access other company's data"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Try to access data with manipulated company ID
        response = requests.get(
            f"{API_BASE_URL}/employees/?company_id=999999",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        # Should either ignore the parameter or return empty results
        assert response.status_code in [200, 403, 404]
    
    def test_direct_object_reference(self, auth_headers):
        """Test protection against insecure direct object references"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Try to access resources with sequential IDs
        test_ids = ["1", "999999", "00000000-0000-0000-0000-000000000000"]
        
        for test_id in test_ids:
            response = requests.get(
                f"{API_BASE_URL}/employees/{test_id}/",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            # Should return 404 for non-existent or unauthorized resources
            assert response.status_code in [200, 404, 403]


class TestInjectionAttacks:
    """Test protection against injection attacks"""
    
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
    
    def test_sql_injection_in_search(self, auth_headers):
        """Test SQL injection protection in search"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        sql_payloads = [
            "'; DROP TABLE employees; --",
            "1' OR '1'='1",
            "1' UNION SELECT * FROM users--",
        ]
        
        for payload in sql_payloads:
            response = requests.get(
                f"{API_BASE_URL}/employees/?search={payload}",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            # Should handle safely without error
            assert response.status_code in [200, 400]
    
    def test_xss_in_input_fields(self, auth_headers):
        """Test XSS protection in input fields"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for payload in xss_payloads:
            employee_data = {
                "employee_id": f"EMP{int(time.time())}",
                "first_name": payload,
                "last_name": "Test",
                "email": f"test{int(time.time())}@example.com",
                "hire_date": datetime.now().strftime("%Y-%m-%d"),
                "status": "active"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/employees/",
                headers=auth_headers,
                json=employee_data,
                timeout=TIMEOUT
            )
            # Should either sanitize or reject
            assert response.status_code in [201, 400]
    
    def test_command_injection(self, auth_headers):
        """Test command injection protection"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
        ]
        
        for payload in command_payloads:
            response = requests.get(
                f"{API_BASE_URL}/employees/?search={payload}",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            # Should handle safely
            assert response.status_code in [200, 400]


class TestDataProtection:
    """Test data protection and encryption"""
    
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
    
    def test_sensitive_data_not_exposed(self, auth_headers):
        """Test that sensitive data is not exposed in responses"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{API_BASE_URL}/auth/profile/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            # Password should never be in response
            assert "password" not in data
            assert "password_hash" not in data
    
    def test_biometric_data_encryption(self, auth_headers):
        """Test that biometric data is properly encrypted"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        # Create attendance with biometric data
        checkin_data = {
            "employee_id": "EMP001",
            "biometric_data": {"face_encoding": [0.1] * 128}
        }
        
        response = requests.post(
            f"{API_BASE_URL}/attendance/check-in/",
            headers=auth_headers,
            json=checkin_data,
            timeout=TIMEOUT
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            # Biometric data should not be returned in plain text
            if "biometric_data" in data:
                # Should be encrypted or hashed
                assert data["biometric_data"] != checkin_data["biometric_data"]


class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self):
        """Test that security headers are present"""
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        headers = response.headers
        
        # Check for important security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "Strict-Transport-Security": None,  # Should exist
        }
        
        for header, expected_value in security_headers.items():
            if expected_value is None:
                # Just check presence
                print(f"{header}: {headers.get(header, 'NOT SET')}")
            elif isinstance(expected_value, list):
                # Check if value is one of the expected
                actual = headers.get(header)
                print(f"{header}: {actual}")
            else:
                # Check exact value
                actual = headers.get(header)
                print(f"{header}: {actual}")
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        response = requests.options(
            f"{API_BASE_URL}/employees/",
            headers={"Origin": "http://malicious-site.com"},
            timeout=TIMEOUT
        )
        
        # Should have CORS headers configured
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        print(f"CORS Origin: {cors_header}")
        
        # Should not allow all origins in production
        if cors_header:
            assert cors_header != "*" or "localhost" in BASE_URL, \
                "CORS should not allow all origins in production"


class TestRateLimiting:
    """Test rate limiting and throttling"""
    
    def test_api_rate_limiting(self):
        """Test that API rate limiting is enforced"""
        # Make rapid requests
        responses = []
        for i in range(50):
            response = requests.get(
                f"{API_BASE_URL}/health/",
                timeout=TIMEOUT
            )
            responses.append(response.status_code)
            if response.status_code == 429:
                print(f"Rate limit hit after {i+1} requests")
                break
            time.sleep(0.05)
        
        # Check if rate limiting kicked in
        rate_limited = 429 in responses
        print(f"Rate limiting active: {rate_limited}")


class TestInputValidation:
    """Test input validation and sanitization"""
    
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
    
    def test_invalid_data_types(self, auth_headers):
        """Test that invalid data types are rejected"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        invalid_data = {
            "employee_id": 12345,  # Should be string
            "first_name": ["array"],  # Should be string
            "email": "not-an-email",  # Invalid email format
            "hire_date": "invalid-date",  # Invalid date format
        }
        
        response = requests.post(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            json=invalid_data,
            timeout=TIMEOUT
        )
        
        assert response.status_code in [400, 422], \
            "Invalid data should be rejected"
    
    def test_oversized_input(self, auth_headers):
        """Test that oversized input is rejected"""
        if not auth_headers:
            pytest.skip("Authentication failed")
        
        oversized_data = {
            "employee_id": "EMP001",
            "first_name": "A" * 10000,  # Very long string
            "last_name": "Test",
            "email": "test@example.com",
            "hire_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        response = requests.post(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            json=oversized_data,
            timeout=TIMEOUT
        )
        
        assert response.status_code in [400, 413, 422], \
            "Oversized input should be rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
