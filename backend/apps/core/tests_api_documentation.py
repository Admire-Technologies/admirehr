"""
Tests for API Documentation and Testing Tools.
Tests API documentation generation, versioning, rate limiting, and monitoring.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.authentication.models import User, Role, Permission, Company
from apps.core.throttling import get_throttle_status, reset_throttle
from apps.core.versioning import transform_data_for_version
import time


class APIDocumentationTests(APITestCase):
    """Test API documentation endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001'
        )
        
        self.role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company,
            role=self.role
        )
        
        self.client = APIClient()
    
    def test_api_schema_generation(self):
        """Test that API schema is generated successfully."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('openapi', response.data)
        self.assertIn('info', response.data)
        self.assertIn('paths', response.data)
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_redoc_ui_accessible(self):
        """Test that ReDoc UI is accessible."""
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_info_endpoint(self):
        """Test API info endpoint."""
        response = self.client.get('/api/v1/api/info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('version', response.data)
        self.assertIn('status', response.data)
        self.assertIn('documentation', response.data)
        self.assertIn('endpoints', response.data)
        self.assertEqual(response.data['version'], '1.0.0')
    
    def test_api_health_endpoint(self):
        """Test API health check endpoint."""
        response = self.client.get('/api/v1/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('cache', response.data)
    
    def test_api_metrics_requires_authentication(self):
        """Test that API metrics endpoint requires authentication."""
        response = self.client.get('/api/v1/api/metrics/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_api_metrics_with_authentication(self):
        """Test API metrics endpoint with authentication."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/api/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('requests', response.data)
        self.assertIn('response_times', response.data)


class APIVersioningTests(APITestCase):
    """Test API versioning functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001'
        )
        
        self.role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company,
            role=self.role
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_default_version_used(self):
        """Test that default version (v1) is used when not specified."""
        response = self.client.get('/api/v1/api/info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_explicit_version_in_url(self):
        """Test that explicit version in URL is recognized."""
        response = self.client.get('/api/v1/api/info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_version_rejected(self):
        """Test that invalid API version is rejected."""
        response = self.client.get('/api/v99/api/info/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_data_transformation_between_versions(self):
        """Test data transformation between API versions."""
        v1_data = {
            'emp_id': 'EMP001',
            'dept': 'Engineering'
        }
        
        v2_data = transform_data_for_version(v1_data, 'employee', 'v1', 'v2')
        
        # In v2, fields should be transformed
        self.assertIn('employee_id', v2_data)
        self.assertIn('department', v2_data)
        self.assertEqual(v2_data['employee_id'], 'EMP001')
        self.assertEqual(v2_data['department'], 'Engineering')


class RateLimitingTests(APITestCase):
    """Test API rate limiting and throttling."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001'
        )
        
        self.role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company,
            role=self.role
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            company=self.company,
            role=self.role,
            is_company_admin=True
        )
        
        self.client = APIClient()
    
    def test_throttle_status_requires_authentication(self):
        """Test that throttle status endpoint requires authentication."""
        response = self.client.get('/api/v1/api/throttle/status/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_throttle_status_for_authenticated_user(self):
        """Test throttle status endpoint for authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/api/throttle/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('throttled', response.data)
        self.assertIn('limits', response.data)
        self.assertIn('remaining', response.data)
    
    def test_get_throttle_status_function(self):
        """Test get_throttle_status utility function."""
        throttle_status = get_throttle_status(user=self.user)
        self.assertIsInstance(throttle_status, dict)
        self.assertIn('throttled', throttle_status)
        self.assertIn('limits', throttle_status)
        self.assertIn('remaining', throttle_status)
    
    def test_reset_throttle_function(self):
        """Test reset_throttle utility function."""
        # This should not raise any exceptions
        reset_throttle(user=self.user)
        reset_throttle(user=self.user, scope='user')
    
    def test_throttle_reset_requires_admin(self):
        """Test that throttle reset requires admin permissions."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/api/throttle/reset/', {
            'user_id': str(self.user.id)
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_throttle_reset_by_admin(self):
        """Test throttle reset by admin user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/v1/api/throttle/reset/', {
            'user_id': str(self.user.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_rate_limit_config_get(self):
        """Test getting rate limit configuration."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/api/throttle/config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('default', response.data)
    
    def test_rate_limit_config_update(self):
        """Test updating rate limit configuration."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put('/api/v1/api/throttle/config/', {
            'default': '2000/hour',
            'roles': {
                'Admin': '5000/hour'
            }
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify the configuration was saved
        self.company.refresh_from_db()
        self.assertIn('api_rate_limits', self.company.settings)
        self.assertEqual(self.company.settings['api_rate_limits']['default'], '2000/hour')
    
    def test_invalid_rate_limit_format_rejected(self):
        """Test that invalid rate limit format is rejected."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put('/api/v1/api/throttle/config/', {
            'default': 'invalid_format'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class APIIntegrationTests(APITestCase):
    """Integration tests for API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001'
        )
        
        self.role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        
        # Create permissions
        self.permission = Permission.objects.create(
            name='View Employees',
            codename='view_employees',
            module='employees',
            action='view'
        )
        self.role.permissions.add(self.permission)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company,
            role=self.role
        )
        
        self.client = APIClient()
    
    def test_authentication_flow(self):
        """Test complete authentication flow."""
        # Login
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # Access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Logout
        response = self.client.post('/api/v1/auth/logout/', {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
    
    def test_api_documentation_completeness(self):
        """Test that API documentation includes all major endpoints."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        paths = response.data.get('paths', {})
        
        # Check that major endpoint categories are documented
        # Use partial matching since exact paths may vary
        endpoint_patterns = [
            'auth/login',
            'employees',
            'attendance',
            'leave',
            'payroll',
        ]
        
        for pattern in endpoint_patterns:
            # Check if pattern exists in any path
            found = any(pattern in path for path in paths.keys())
            self.assertTrue(found, f'Endpoint pattern "{pattern}" not found in API documentation')
    
    def test_api_error_responses(self):
        """Test that API returns proper error responses."""
        # Test 401 Unauthorized
        response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test 400 Bad Request
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser'
            # Missing password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 404 Not Found
        response = self.client.get('/api/v1/nonexistent/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class APIPerformanceTests(APITestCase):
    """Performance tests for API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001'
        )
        
        self.role = Role.objects.create(
            name='Admin',
            company=self.company
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company,
            role=self.role
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_api_response_time(self):
        """Test that API endpoints respond within acceptable time."""
        import time
        
        endpoints = [
            '/api/v1/api/info/',
            '/api/v1/api/health/',
            '/api/v1/auth/profile/',
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be under 2 seconds (more lenient for test environment)
            self.assertLess(response_time, 2.0,
                          f'Endpoint {endpoint} took {response_time:.2f}s (should be < 2s)')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_concurrent_requests_handling(self):
        """Test that API can handle concurrent requests."""
        import concurrent.futures
        
        def make_request():
            client = APIClient()
            client.force_authenticate(user=self.user)
            response = client.get('/api/v1/api/info/')
            return response.status_code
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(code == status.HTTP_200_OK for code in results))
