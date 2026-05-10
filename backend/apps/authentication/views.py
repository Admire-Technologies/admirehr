"""
Authentication views for the HRMS application.
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from .serializers import (
    LoginSerializer, UserSerializer, ChangePasswordSerializer,
    RoleSerializer, PermissionSerializer, CreateUserSerializer,
    UserPermissionsSerializer
)
from .models import User, Role, Permission
from .permissions import CanManageUsers, CanManageRoles, IsCompanyAdmin
from .decorators import require_permission


class LoginView(APIView):
    """
    User login view that returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                })
            else:
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    User logout view that blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    Get current user profile information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Change user password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password changed successfully'})
            else:
                return Response(
                    {'error': 'Invalid old password'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPermissionsView(APIView):
    """
    Get current user permissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'permissions': user.get_permissions_by_module(),
            'role': user.role,
            'is_company_admin': user.is_company_admin
        }
        serializer = UserPermissionsSerializer(data)
        return Response(serializer.data)


# Role Management Views
class RoleListCreateView(generics.ListCreateAPIView):
    """
    List and create roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, CanManageRoles]

    def get_queryset(self):
        return Role.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, and delete roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, CanManageRoles]

    def get_queryset(self):
        return Role.objects.filter(company=self.request.user.company)

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        
        # Prevent deletion of system roles
        if role.is_system_role:
            return Response(
                {'error': 'Cannot delete system role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if role is assigned to users
        if role.user_set.exists():
            return Response(
                {'error': 'Cannot delete role that is assigned to users'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


# Permission Management Views
class PermissionListView(generics.ListAPIView):
    """
    List all available permissions.
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, CanManageRoles]
    queryset = Permission.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)
        return queryset.order_by('module', 'action')


# User Management Views
class UserListCreateView(generics.ListCreateAPIView):
    """
    List and create users.
    """
    permission_classes = [IsAuthenticated, CanManageUsers]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(company=self.request.user.company)
        
        # Filter by role
        role_id = self.request.query_params.get('role')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        # Search by name or username
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('username')


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, and delete users.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]

    def get_queryset(self):
        return User.objects.filter(company=self.request.user.company)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Prevent deletion of self
        if user == request.user:
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class AssignRoleView(APIView):
    """
    Assign role to user.
    """
    permission_classes = [IsAuthenticated, CanManageUsers]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, company=request.user.company)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        role_id = request.data.get('role_id')
        if not role_id:
            user.role = None
            user.save()
            return Response({'message': 'Role removed from user'})

        try:
            role = Role.objects.get(id=role_id, company=request.user.company)
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        user.role = role
        user.save()
        
        return Response({
            'message': 'Role assigned successfully',
            'user': UserSerializer(user).data
        })