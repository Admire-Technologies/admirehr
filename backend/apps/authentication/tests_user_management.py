"""
Unit tests for user management functionality.
Tests for Task 13: User Management and Administration.
"""

import io
import csv
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.models import Company
from .models import User, Role, Permission, AuditLog


class UserActivationTest(APITestCase):
    """Test cases for user activation/deactivation."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        self.admin_role = Role.objects.create(
            name="Admin",
            company=self.company
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            role=self.admin_role,
            is_company_admin=True
        )
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="regularpass123",
            company=self.company
        )
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_deactivate_user_success(self):
        """Test successful user deactivation."""
        url = reverse('authentication:user_activation', kwargs={'user_id': self.regular_user.id})
        data = {'action': 'deactivate'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)
        
        # Check audit log
        audit_log = AuditLog.objects.filter(
            user=self.admin_user,
            action='update',
            module='users'
        ).first()
        self.assertIsNotNone(audit_log)
        self.assertIn('deactivated', audit_log.description)

    def test_activate_user_success(self):
        """Test successful user activation."""
        # First deactivate
        self.regular_user.is_active = False
        self.regular_user.save()
        
        url = reverse('authentication:user_activation', kwargs={'user_id': self.regular_user.id})
        data = {'action': 'activate'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)

    def test_cannot_deactivate_self(self):
        """Test that user cannot deactivate their own account."""
        url = reverse('authentication:user_activation', kwargs={'user_id': self.admin_user.id})
        data = {'action': 'deactivate'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot deactivate your own account', response.data['error'])

    def test_invalid_action(self):
        """Test invalid activation action."""
        url = reverse('authentication:user_activation', kwargs={'user_id': self.regular_user.id})
        data = {'action': 'invalid_action'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_not_found(self):
        """Test activation of non-existent user."""
        import uuid
        url = reverse('authentication:user_activation', kwargs={'user_id': uuid.uuid4()})
        data = {'action': 'activate'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BulkUserOperationsTest(APITestCase):
    """Test cases for bulk user operations."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        
        # Create multiple users
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                company=self.company
            )
            self.users.append(user)
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_bulk_activate_users(self):
        """Test bulk activation of users."""
        # Deactivate all users first
        for user in self.users:
            user.is_active = False
            user.save()
        
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'activate',
            'user_ids': [str(user.id) for user in self.users]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['success'], 5)
        
        # Verify all users are active
        for user in self.users:
            user.refresh_from_db()
            self.assertTrue(user.is_active)

    def test_bulk_deactivate_users(self):
        """Test bulk deactivation of users."""
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'deactivate',
            'user_ids': [str(user.id) for user in self.users]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['success'], 5)
        
        # Verify all users are inactive
        for user in self.users:
            user.refresh_from_db()
            self.assertFalse(user.is_active)

    def test_bulk_assign_role(self):
        """Test bulk role assignment."""
        role = Role.objects.create(
            name="Employee",
            company=self.company
        )
        
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'assign_role',
            'user_ids': [str(user.id) for user in self.users],
            'role_id': str(role.id)
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['success'], 5)
        
        # Verify all users have the role
        for user in self.users:
            user.refresh_from_db()
            self.assertEqual(user.role, role)

    def test_bulk_delete_users(self):
        """Test bulk deletion of users."""
        user_ids = [str(user.id) for user in self.users[:3]]
        
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'delete',
            'user_ids': user_ids
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['success'], 3)
        
        # Verify users are deleted
        remaining_users = User.objects.filter(id__in=user_ids)
        self.assertEqual(remaining_users.count(), 0)

    def test_bulk_operation_excludes_self(self):
        """Test that bulk operations exclude the current user."""
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'deactivate',
            'user_ids': [str(self.admin_user.id)] + [str(user.id) for user in self.users]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only affect the 5 other users, not admin
        self.assertEqual(response.data['results']['success'], 5)
        
        # Verify admin is still active
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_bulk_operation_no_user_ids(self):
        """Test bulk operation with no user IDs."""
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'activate',
            'user_ids': []
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_operation_invalid_operation(self):
        """Test bulk operation with invalid operation type."""
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'invalid_op',
            'user_ids': [str(user.id) for user in self.users]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserCSVImportTest(APITestCase):
    """Test cases for CSV user import."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        self.role = Role.objects.create(
            name="Employee",
            company=self.company
        )
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def create_csv_file(self, rows):
        """Helper to create CSV file."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'username', 'email', 'first_name', 'last_name', 
            'password', 'role_name', 'is_company_admin'
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        output.seek(0)
        return output

    def test_csv_import_success(self):
        """Test successful CSV import."""
        rows = [
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'first_name': 'User',
                'last_name': 'One',
                'password': 'password123',
                'role_name': 'Employee',
                'is_company_admin': 'false'
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'first_name': 'User',
                'last_name': 'Two',
                'password': 'password123',
                'role_name': 'Employee',
                'is_company_admin': 'false'
            }
        ]
        
        csv_file = self.create_csv_file(rows)
        csv_file = io.BytesIO(csv_file.getvalue().encode('utf-8'))
        csv_file.name = 'users.csv'
        
        url = reverse('authentication:user_csv_import')
        response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['success'], 2)
        self.assertEqual(response.data['results']['failed'], 0)
        
        # Verify users were created
        self.assertTrue(User.objects.filter(username='user1', company=self.company).exists())
        self.assertTrue(User.objects.filter(username='user2', company=self.company).exists())

    def test_csv_import_missing_required_fields(self):
        """Test CSV import with missing required fields."""
        rows = [
            {
                'username': 'user1',
                'email': '',  # Missing email
                'first_name': 'User',
                'last_name': 'One',
                'password': 'password123',
                'role_name': 'Employee',
                'is_company_admin': 'false'
            }
        ]
        
        csv_file = self.create_csv_file(rows)
        csv_file = io.BytesIO(csv_file.getvalue().encode('utf-8'))
        csv_file.name = 'users.csv'
        
        url = reverse('authentication:user_csv_import')
        response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['success'], 0)
        self.assertEqual(response.data['results']['failed'], 1)

    def test_csv_import_duplicate_username(self):
        """Test CSV import with duplicate username."""
        # Create existing user
        User.objects.create_user(
            username='user1',
            email='existing@example.com',
            password='password123',
            company=self.company
        )
        
        rows = [
            {
                'username': 'user1',  # Duplicate
                'email': 'user1@example.com',
                'first_name': 'User',
                'last_name': 'One',
                'password': 'password123',
                'role_name': 'Employee',
                'is_company_admin': 'false'
            }
        ]
        
        csv_file = self.create_csv_file(rows)
        csv_file = io.BytesIO(csv_file.getvalue().encode('utf-8'))
        csv_file.name = 'users.csv'
        
        url = reverse('authentication:user_csv_import')
        response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['failed'], 1)
        self.assertIn('already exists', response.data['results']['errors'][0]['error'])

    def test_csv_import_invalid_role(self):
        """Test CSV import with invalid role name."""
        rows = [
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'first_name': 'User',
                'last_name': 'One',
                'password': 'password123',
                'role_name': 'NonExistentRole',
                'is_company_admin': 'false'
            }
        ]
        
        csv_file = self.create_csv_file(rows)
        csv_file = io.BytesIO(csv_file.getvalue().encode('utf-8'))
        csv_file.name = 'users.csv'
        
        url = reverse('authentication:user_csv_import')
        response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['failed'], 1)
        self.assertIn('not found', response.data['results']['errors'][0]['error'])

    def test_csv_import_no_file(self):
        """Test CSV import without file."""
        url = reverse('authentication:user_csv_import')
        response = self.client.post(url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No file provided', response.data['error'])

    def test_csv_import_invalid_file_type(self):
        """Test CSV import with non-CSV file."""
        file = io.BytesIO(b'not a csv')
        file.name = 'users.txt'
        
        url = reverse('authentication:user_csv_import')
        response = self.client.post(url, {'file': file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be a CSV', response.data['error'])


class UserCSVExportTest(APITestCase):
    """Test cases for CSV user export."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        self.role = Role.objects.create(
            name="Employee",
            company=self.company
        )
        
        # Create test users
        for i in range(3):
            User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                company=self.company,
                role=self.role
            )
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_csv_export_success(self):
        """Test successful CSV export."""
        url = reverse('authentication:user_csv_export')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header
        self.assertEqual(rows[0][0], 'Username')
        
        # Check data rows (4 users total: admin + 3 test users)
        self.assertEqual(len(rows), 5)  # Header + 4 users

    def test_csv_export_creates_audit_log(self):
        """Test that CSV export creates audit log entry."""
        url = reverse('authentication:user_csv_export')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check audit log
        audit_log = AuditLog.objects.filter(
            user=self.admin_user,
            action='export',
            module='users'
        ).first()
        self.assertIsNotNone(audit_log)
        self.assertIn('Exported', audit_log.description)


class AuditLogTest(APITestCase):
    """Test cases for audit log functionality."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        
        # Create some audit logs
        for i in range(5):
            AuditLog.objects.create(
                user=self.admin_user,
                company=self.company,
                action='create',
                module='users',
                description=f"Test log {i}"
            )
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_list_audit_logs(self):
        """Test listing audit logs."""
        url = reverse('authentication:audit_log_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 5)

    def test_filter_audit_logs_by_action(self):
        """Test filtering audit logs by action."""
        # Create a different action
        AuditLog.objects.create(
            user=self.admin_user,
            company=self.company,
            action='delete',
            module='users',
            description="Delete action"
        )
        
        url = reverse('authentication:audit_log_list')
        response = self.client.get(url, {'action': 'delete'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            self.assertEqual(log['action'], 'delete')

    def test_filter_audit_logs_by_module(self):
        """Test filtering audit logs by module."""
        url = reverse('authentication:audit_log_list')
        response = self.client.get(url, {'module': 'users'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data['results']:
            self.assertEqual(log['module'], 'users')

    def test_audit_log_requires_admin(self):
        """Test that audit log access requires admin privileges."""
        # Create regular user
        regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="password123",
            company=self.company
        )
        
        # Authenticate as regular user
        refresh = RefreshToken.for_user(regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = reverse('authentication:audit_log_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuditLogModelTest(TestCase):
    """Test cases for AuditLog model."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            company=self.company
        )

    def test_audit_log_creation(self):
        """Test audit log creation."""
        log = AuditLog.objects.create(
            user=self.user,
            company=self.company,
            action='create',
            module='users',
            description="Test audit log"
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.company, self.company)
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.module, 'users')

    def test_audit_log_helper_method(self):
        """Test audit log helper method."""
        log = AuditLog.log_action(
            user=self.user,
            action='update',
            module='users',
            description="Updated user profile",
            changes={'email': {'old': 'old@example.com', 'new': 'new@example.com'}}
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.action, 'update')
        self.assertEqual(log.changes['email']['new'], 'new@example.com')

    def test_audit_log_str_representation(self):
        """Test audit log string representation."""
        log = AuditLog.objects.create(
            user=self.user,
            company=self.company,
            action='login',
            module='authentication',
            description="User logged in"
        )
        
        expected_str = f"{self.user.username} - login - authentication"
        self.assertIn(expected_str, str(log))


class UserManagementSecurityTest(APITestCase):
    """Test cases for user management security and multi-tenancy."""

    def setUp(self):
        # Create two companies
        self.company1 = Company.objects.create(
            name="Company 1",
            code="COMP001",
            email="company1@example.com"
        )
        self.company2 = Company.objects.create(
            name="Company 2",
            code="COMP002",
            email="company2@example.com"
        )
        
        # Create admin for each company
        self.admin1 = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="password123",
            company=self.company1,
            is_company_admin=True
        )
        self.admin2 = User.objects.create_user(
            username="admin2",
            email="admin2@example.com",
            password="password123",
            company=self.company2,
            is_company_admin=True
        )
        
        # Create users for each company
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
            company=self.company1
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
            company=self.company2
        )

    def test_cannot_access_other_company_users(self):
        """Test that admin cannot access users from other companies."""
        # Authenticate as admin1
        refresh = RefreshToken.for_user(self.admin1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try to access user2 (from company2)
        url = reverse('authentication:user_detail', kwargs={'pk': self.user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_deactivate_other_company_users(self):
        """Test that admin cannot deactivate users from other companies."""
        # Authenticate as admin1
        refresh = RefreshToken.for_user(self.admin1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try to deactivate user2 (from company2)
        url = reverse('authentication:user_activation', kwargs={'user_id': self.user2.id})
        data = {'action': 'deactivate'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_operations_only_affect_own_company(self):
        """Test that bulk operations only affect users from the same company."""
        # Authenticate as admin1
        refresh = RefreshToken.for_user(self.admin1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try bulk operation with users from both companies
        url = reverse('authentication:bulk_user_operations')
        data = {
            'operation': 'deactivate',
            'user_ids': [str(self.user1.id), str(self.user2.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only affect user1
        self.assertEqual(response.data['results']['success'], 1)
        
        # Verify user1 is deactivated but user2 is not
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertFalse(self.user1.is_active)
        self.assertTrue(self.user2.is_active)

    def test_audit_logs_isolated_by_company(self):
        """Test that audit logs are isolated by company."""
        # Create audit logs for both companies
        AuditLog.objects.create(
            user=self.admin1,
            company=self.company1,
            action='create',
            module='users',
            description="Company 1 log"
        )
        AuditLog.objects.create(
            user=self.admin2,
            company=self.company2,
            action='create',
            module='users',
            description="Company 2 log"
        )
        
        # Authenticate as admin1
        refresh = RefreshToken.for_user(self.admin1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Get audit logs
        url = reverse('authentication:audit_log_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see company1 logs
        for log in response.data['results']:
            self.assertIn('Company 1', log['description'])
            self.assertNotIn('Company 2', log['description'])
