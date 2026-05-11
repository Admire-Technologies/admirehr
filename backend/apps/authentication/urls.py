"""
URL configuration for authentication app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, ProfileView, ChangePasswordView,
    UserPermissionsView, RoleListCreateView, RoleDetailView,
    PermissionListView, UserListCreateView, UserDetailView,
    AssignRoleView, UserActivationView, BulkUserOperationsView,
    UserCSVImportView, UserCSVExportView, AuditLogListView
)

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('permissions/', UserPermissionsView.as_view(), name='user_permissions'),
    
    # Role management endpoints
    path('roles/', RoleListCreateView.as_view(), name='role_list_create'),
    path('roles/<uuid:pk>/', RoleDetailView.as_view(), name='role_detail'),
    
    # Permission management endpoints
    path('permissions/list/', PermissionListView.as_view(), name='permission_list'),
    
    # User management endpoints
    path('users/', UserListCreateView.as_view(), name='user_list_create'),
    path('users/<uuid:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<uuid:user_id>/assign-role/', AssignRoleView.as_view(), name='assign_role'),
    path('users/<uuid:user_id>/activation/', UserActivationView.as_view(), name='user_activation'),
    path('users/bulk-operations/', BulkUserOperationsView.as_view(), name='bulk_user_operations'),
    path('users/import-csv/', UserCSVImportView.as_view(), name='user_csv_import'),
    path('users/export-csv/', UserCSVExportView.as_view(), name='user_csv_export'),
    
    # Audit log endpoints
    path('audit-logs/', AuditLogListView.as_view(), name='audit_log_list'),
]