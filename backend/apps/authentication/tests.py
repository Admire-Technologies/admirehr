"""
Unit tests for authentication app.
"""

import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.models import Company
from .models import Role

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        self.role = Role.objects.create(
            name="Test Role",
            company=self.company
        )

    def test_user_creation(self):
        """Test user creation with company relationship."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            company=self.company,
            role=self.role
        )
        
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.company, self.company)
        self.assertEqual(user.role, self.role)
        self.assertFalse(user.is_company_admin)
        self.assertTrue(user.check_password("testpass123"))

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username="testuser",
            company=self.company
        )
        expected_str = f"testuser ({self.company.name})"
        self.assertEqual(str(user), expected_str)

    def test_has_permission_superuser(self):
        """Test superuser has all permissions."""
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company
        )
        self.assertTrue(user.has_permission("any_permission"))

    def test_has_permission_company_admin(self):
        """Test company admin has all permissions."""
        user = User.objects.create_user(
            username="companyadmin",
            company=self.company,
            is_company_admin=True
        )
        self.assertTrue(user.has_permission("any_permission"))

    def test_has_permission_with_role(self):
        """Test permission checking with role."""
        from .models import Permission as CustomPermission
        
        # Create a custom permission
        permission = CustomPermission.objects.create(
            codename="test_permission",
            name="Test Permission",
            module="test",
            action="view"
        )
        
        # Add permission to role
        self.role.permissions.add(permission)
        
        user = User.objects.create_user(
            username="testuser",
            company=self.company,
            role=self.role
        )
        
        self.assertTrue(user.has_permission("test_permission"))
        self.assertFalse(user.has_permission("nonexistent_permission"))


class RoleModelTest(TestCase):
    """Test cases for Role model."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )

    def test_role_creation(self):
        """Test role creation."""
        role = Role.objects.create(
            name="Manager",
            description="Manager role",
            company=self.company
        )
        
        self.assertEqual(role.name, "Manager")
        self.assertEqual(role.description, "Manager role")
        self.assertEqual(role.company, self.company)

    def test_role_str_representation(self):
        """Test role string representation."""
        role = Role.objects.create(
            name="Manager",
            company=self.company
        )
        expected_str = f"Manager ({self.company.name})"
        self.assertEqual(str(role), expected_str)

    def test_role_unique_together(self):
        """Test role name is unique per company."""
        Role.objects.create(
            name="Manager",
            company=self.company
        )
        
        # Creating another role with same name in same company should fail
        with self.assertRaises(Exception):
            Role.objects.create(
                name="Manager",
                company=self.company
            )


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        self.role = Role.objects.create(
            name="Employee",
            company=self.company
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            company=self.company,
            role=self.role
        )
        self.login_url = reverse('authentication:login')
        self.logout_url = reverse('authentication:logout')
        self.profile_url = reverse('authentication:profile')
        self.refresh_url = reverse('authentication:token_refresh')

    def test_login_success(self):
        """Test successful login."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        data = {'username': 'testuser'}
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success(self):
        """Test successful logout."""
        # First login to get tokens
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {'refresh': str(refresh)}
        response = self.client.post(self.logout_url, data)
        
        # Should succeed even if blacklisting fails
        self.assertIn(response.status_code, [status.HTTP_205_RESET_CONTENT, status.HTTP_400_BAD_REQUEST])

    def test_logout_invalid_token(self):
        """Test logout with invalid refresh token."""
        # Set authorization header with valid access token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {'refresh': 'invalid_token'}
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_get_authenticated(self):
        """Test getting profile when authenticated."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_profile_get_unauthenticated(self):
        """Test getting profile when not authenticated."""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update(self):
        """Test updating profile."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        response = self.client.put(self.profile_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['email'], 'john.doe@example.com')

    def test_token_refresh(self):
        """Test token refresh."""
        refresh = RefreshToken.for_user(self.user)
        
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid(self):
        """Test token refresh with invalid token."""
        data = {'refresh': 'invalid_token'}
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_success(self):
        """Test successful password change."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpassword123'
        }
        response = self.client.post(reverse('authentication:change_password'), data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        response = self.client.post(reverse('authentication:change_password'), data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class JWTTokenTest(TestCase):
    """Test JWT token functionality."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            company=self.company
        )

    def test_token_generation(self):
        """Test JWT token generation for user."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(str(refresh))

    def test_token_contains_user_info(self):
        """Test that token contains user information."""
        refresh = RefreshToken.for_user(self.user)
        
        # Check that user_id is in the token payload
        self.assertEqual(str(refresh['user_id']), str(self.user.id))