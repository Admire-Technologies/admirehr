"""
Comprehensive tests for RBAC enforcement.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.models import Company
from .models import Role, Permission

User = get_user_model()


class RBACModelTests(TestCase):
    """Test RBAC models functionality."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        # Create permissions
        self.view_employee_perm = Permission.objects.create(
            name="View Employees",
            codename="view_employee",
            module="employee",
            action="view"
        )
        
        self.add_employee_perm = Permission.objects.create(
            name="Add Employee",
            codename="add_employee",
            module="employee",
            action="add"
        )
        
        # Create role
        self.hr_role = Role.objects.create(
            name="HR Manager",
            description="HR management role",
            company=self.company
        )
        self.hr_role.permissions.add(self.view_employee_perm, self.add_employee_perm)
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            company=self.company,
            role=self.hr_role
        )

    def test_permission_creation(self):
        """Test permission model creation."""
        self.assertEqual(self.view_employee_perm.name, "View Employees")
        self.assertEqual(self.view_employee_perm.codename, "view_employee")
        self.assertEqual(self.view_employee_perm.module, "employee")
        self.assertEqual(self.view_employee_perm.action, "view")

    def test_role_creation(self):
        """Test role model creation."""
        self.assertEqual(self.hr_role.name, "HR Manager")
        self.assertEqual(self.hr_role.company, self.company)
        self.assertEqual(self.hr_role.permissions.count(), 2)

    def test_role_has_permission(self):
        """Test role permission checking."""
        self.assertTrue(self.hr_role.has_permission("view_employee"))
        self.assertTrue(self.hr_role.has_permission("add_employee"))
        self.assertFalse(self.hr_role.has_permission("delete_employee"))

    def test_user_has_permission(self):
        """Test user permission checking through role."""
        self.assertTrue(self.user.has_permission("view_employee"))
        self.assertTrue(self.user.has_permission("add_employee"))
        self.assertFalse(self.user.has_permission("delete_employee"))

    def test_company_admin_permissions(self):
        """Test company admin has all permissions."""
        admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        
        self.assertTrue(admin_user.has_permission("view_employee"))
        self.assertTrue(admin_user.has_permission("delete_employee"))
        self.assertTrue(admin_user.has_permission("any_permission"))

    def test_user_without_role(self):
        """Test user without role has no permissions."""
        user_no_role = User.objects.create_user(
            username="norole",
            email="norole@example.com",
            password="testpass123",
            company=self.company
        )
        
        self.assertFalse(user_no_role.has_permission("view_employee"))
        self.assertFalse(user_no_role.has_permission("add_employee"))

    def test_get_permissions_by_module(self):
        """Test getting permissions grouped by module."""
        permissions_by_module = self.user.get_permissions_by_module()
        
        self.assertIn("employee", permissions_by_module)
        self.assertEqual(len(permissions_by_module["employee"]), 2)
        
        permission_codenames = [p.codename for p in permissions_by_module["employee"]]
        self.assertIn("view_employee", permission_codenames)
        self.assertIn("add_employee", permission_codenames)


class RBACAPITests(APITestCase):
    """Test RBAC API endpoints."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        # Create permissions
        self.manage_roles_perm = Permission.objects.create(
            name="Manage Roles",
            codename="manage_roles",
            module="role",
            action="manage"
        )
        
        self.manage_users_perm = Permission.objects.create(
            name="Manage Users",
            codename="manage_users",
            module="user",
            action="manage"
        )
        
        # Create admin role
        self.admin_role = Role.objects.create(
            name="Admin",
            company=self.company
        )
        self.admin_role.permissions.add(self.manage_roles_perm, self.manage_users_perm)
        
        # Create regular role
        self.user_role = Role.objects.create(
            name="Regular User",
            company=self.company
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            company=self.company,
            role=self.admin_role
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpass123",
            company=self.company,
            role=self.user_role
        )

    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_role_list_with_permission(self):
        """Test role list endpoint with proper permissions."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_role_list_without_permission(self):
        """Test role list endpoint without proper permissions."""
        token = self.get_jwt_token(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/roles/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_create_with_permission(self):
        """Test role creation with proper permissions."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'name': 'New Role',
            'description': 'A new role',
            'permission_ids': [str(self.manage_users_perm.id)]
        }
        
        response = self.client.post('/api/v1/auth/roles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Role')

    def test_role_create_without_permission(self):
        """Test role creation without proper permissions."""
        token = self.get_jwt_token(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'name': 'New Role',
            'description': 'A new role',
            'permission_ids': []
        }
        
        response = self.client.post('/api/v1/auth/roles/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_list_with_permission(self):
        """Test user list endpoint with proper permissions."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_user_list_without_permission(self):
        """Test user list endpoint without proper permissions."""
        token = self.get_jwt_token(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_role_with_permission(self):
        """Test role assignment with proper permissions."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'role_id': str(self.admin_role.id)}
        
        response = self.client.post(
            f'/api/v1/auth/users/{self.regular_user.id}/assign-role/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify role was assigned
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.role, self.admin_role)

    def test_assign_role_without_permission(self):
        """Test role assignment without proper permissions."""
        token = self.get_jwt_token(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'role_id': str(self.admin_role.id)}
        
        response = self.client.post(
            f'/api/v1/auth/users/{self.admin_user.id}/assign-role/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_permissions_endpoint(self):
        """Test user permissions endpoint."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/permissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn('permissions', response.data)
        self.assertIn('role', response.data)
        self.assertIn('is_company_admin', response.data)

    def test_company_admin_bypass(self):
        """Test that company admin bypasses permission checks."""
        company_admin = User.objects.create_user(
            username="companyadmin",
            email="companyadmin@example.com",
            password="adminpass123",
            company=self.company,
            is_company_admin=True
        )
        
        token = self.get_jwt_token(company_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Should be able to access roles even without explicit permission
        response = self.client.get('/api/v1/auth/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should be able to access users even without explicit permission
        response = self.client.get('/api/v1/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RBACMultiTenantTests(APITestCase):
    """Test RBAC multi-tenant isolation."""
    
    def setUp(self):
        # Create two companies
        self.company1 = Company.objects.create(
            name="Company 1",
            code="COMP001"
        )
        
        self.company2 = Company.objects.create(
            name="Company 2",
            code="COMP002"
        )
        
        # Create permission
        self.manage_roles_perm = Permission.objects.create(
            name="Manage Roles",
            codename="manage_roles",
            module="role",
            action="manage"
        )
        
        # Create roles for each company
        self.role1 = Role.objects.create(
            name="Admin",
            company=self.company1
        )
        self.role1.permissions.add(self.manage_roles_perm)
        
        self.role2 = Role.objects.create(
            name="Admin",
            company=self.company2
        )
        self.role2.permissions.add(self.manage_roles_perm)
        
        # Create users for each company
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@company1.com",
            password="pass123",
            company=self.company1,
            role=self.role1
        )
        
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@company2.com",
            password="pass123",
            company=self.company2,
            role=self.role2
        )

    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_role_isolation(self):
        """Test that users can only see roles from their company."""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.role1.id))

    def test_user_isolation(self):
        """Test that users can only see users from their company."""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.user1.id))

    def test_cross_company_role_assignment_blocked(self):
        """Test that users cannot assign roles from other companies."""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Try to assign role from company2 to user in company1
        data = {'role_id': str(self.role2.id)}
        
        response = self.client.post(
            f'/api/v1/auth/users/{self.user1.id}/assign-role/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RBACPermissionDecoratorTests(TestCase):
    """Test permission decorators."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        
        self.permission = Permission.objects.create(
            name="Test Permission",
            codename="test_permission",
            module="test",
            action="test"
        )
        
        self.role = Role.objects.create(
            name="Test Role",
            company=self.company
        )
        self.role.permissions.add(self.permission)
        
        self.user_with_permission = User.objects.create_user(
            username="withperm",
            email="withperm@example.com",
            password="pass123",
            company=self.company,
            role=self.role
        )
        
        self.user_without_permission = User.objects.create_user(
            username="withoutperm",
            email="withoutperm@example.com",
            password="pass123",
            company=self.company
        )

    def test_require_permission_decorator(self):
        """Test require_permission decorator."""
        from .decorators import require_permission
        from django.http import HttpRequest, JsonResponse
        
        @require_permission('test_permission')
        def test_view(request):
            return JsonResponse({'success': True})
        
        # Test with user having permission
        request = HttpRequest()
        request.user = self.user_with_permission
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Test with user not having permission
        request.user = self.user_without_permission
        response = test_view(request)
        self.assertEqual(response.status_code, 403)

    def test_require_permissions_decorator(self):
        """Test require_permissions decorator (multiple permissions)."""
        from .decorators import require_permissions
        from django.http import HttpRequest, JsonResponse
        
        # Create another permission
        permission2 = Permission.objects.create(
            name="Test Permission 2",
            codename="test_permission_2",
            module="test",
            action="test2"
        )
        self.role.permissions.add(permission2)
        
        @require_permissions('test_permission', 'test_permission_2')
        def test_view(request):
            return JsonResponse({'success': True})
        
        # Test with user having all permissions
        request = HttpRequest()
        request.user = self.user_with_permission
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Test with user not having all permissions
        request.user = self.user_without_permission
        response = test_view(request)
        self.assertEqual(response.status_code, 403)