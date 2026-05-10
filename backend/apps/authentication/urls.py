"""
URL configuration for authentication app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, ProfileView, ChangePasswordView,
    UserPermissionsView, RoleListCreateView, RoleDetailView,
    PermissionListView, UserListCreateView, UserDetailView,
    AssignRoleView
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
]