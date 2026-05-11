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
                
                # Log successful login
                from .models import AuditLog
                AuditLog.log_action(
                    user=user,
                    action='login',
                    module='authentication',
                    description=f"User {user.username} logged in successfully",
                    company=user.company,
                    request=request
                )
                
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
            
            # Log logout
            from .models import AuditLog
            AuditLog.log_action(
                user=request.user,
                action='logout',
                module='authentication',
                description=f"User {request.user.username} logged out",
                company=request.user.company,
                request=request
            )
            
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
                
                # Log password change
                from .models import AuditLog
                AuditLog.log_action(
                    user=user,
                    action='password_change',
                    module='authentication',
                    description=f"User {user.username} changed their password",
                    company=user.company,
                    request=request
                )
                
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
        old_role = user.role
        
        if not role_id:
            user.role = None
            user.save()
            
            # Log role removal
            from .models import AuditLog
            AuditLog.log_action(
                user=request.user,
                action='role_assign',
                module='users',
                description=f"Removed role from user {user.username}",
                company=request.user.company,
                content_object=user,
                changes={
                    'role': {
                        'old': old_role.name if old_role else None,
                        'new': None
                    }
                },
                request=request
            )
            
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
        
        # Log role assignment
        from .models import AuditLog
        AuditLog.log_action(
            user=request.user,
            action='role_assign',
            module='users',
            description=f"Assigned role {role.name} to user {user.username}",
            company=request.user.company,
            content_object=user,
            changes={
                'role': {
                    'old': old_role.name if old_role else None,
                    'new': role.name
                }
            },
            request=request
        )
        
        return Response({
            'message': 'Role assigned successfully',
            'user': UserSerializer(user).data
        })



class UserActivationView(APIView):
    """
    Activate or deactivate user accounts.
    Implements user activation/deactivation functionality.
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
        
        # Prevent deactivation of self
        if user == request.user:
            return Response(
                {'error': 'Cannot deactivate your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        if action not in ['activate', 'deactivate']:
            return Response(
                {'error': 'Invalid action. Use "activate" or "deactivate"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user status
        user.is_active = (action == 'activate')
        user.save()
        
        # Log the action
        from .models import AuditLog
        AuditLog.log_action(
            user=request.user,
            action='update',
            module='users',
            description=f"User {user.username} {'activated' if user.is_active else 'deactivated'}",
            company=request.user.company,
            content_object=user,
            changes={
                'is_active': {
                    'old': not user.is_active,
                    'new': user.is_active
                }
            },
            request=request
        )
        
        return Response({
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'user': UserSerializer(user).data
        })


class BulkUserOperationsView(APIView):
    """
    Perform bulk operations on multiple users.
    Supports bulk activation, deactivation, role assignment, and deletion.
    """
    permission_classes = [IsAuthenticated, CanManageUsers]

    def post(self, request):
        operation = request.data.get('operation')
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response(
                {'error': 'No user IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get users from the same company
        users = User.objects.filter(
            id__in=user_ids,
            company=request.user.company
        ).exclude(id=request.user.id)  # Exclude self
        
        if not users.exists():
            return Response(
                {'error': 'No valid users found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        if operation == 'activate':
            users.update(is_active=True)
            results['success'] = users.count()
            description = f"Bulk activated {users.count()} users"
            
        elif operation == 'deactivate':
            users.update(is_active=False)
            results['success'] = users.count()
            description = f"Bulk deactivated {users.count()} users"
            
        elif operation == 'assign_role':
            role_id = request.data.get('role_id')
            if not role_id:
                return Response(
                    {'error': 'Role ID required for role assignment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                role = Role.objects.get(id=role_id, company=request.user.company)
                users.update(role=role)
                results['success'] = users.count()
                description = f"Bulk assigned role {role.name} to {users.count()} users"
            except Role.DoesNotExist:
                return Response(
                    {'error': 'Role not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif operation == 'delete':
            count = users.count()
            users.delete()
            results['success'] = count
            description = f"Bulk deleted {count} users"
            
        else:
            return Response(
                {'error': 'Invalid operation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the bulk operation
        from .models import AuditLog
        AuditLog.log_action(
            user=request.user,
            action=operation if operation != 'assign_role' else 'update',
            module='users',
            description=description,
            company=request.user.company,
            changes={'user_ids': user_ids, 'operation': operation},
            request=request
        )
        
        return Response({
            'message': f'Bulk operation completed successfully',
            'results': results
        })


class UserCSVImportView(APIView):
    """
    Import users from CSV file.
    CSV format: username,email,first_name,last_name,password,role_name,is_company_admin
    """
    permission_classes = [IsAuthenticated, CanManageUsers]

    def post(self, request):
        import csv
        import io
        
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'File must be a CSV'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            results = {
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Validate required fields
                    required_fields = ['username', 'email', 'password']
                    missing_fields = [f for f in required_fields if not row.get(f)]
                    if missing_fields:
                        results['errors'].append({
                            'row': row_num,
                            'error': f"Missing required fields: {', '.join(missing_fields)}"
                        })
                        results['failed'] += 1
                        continue
                    
                    # Check if user already exists
                    if User.objects.filter(
                        username=row['username'],
                        company=request.user.company
                    ).exists():
                        results['errors'].append({
                            'row': row_num,
                            'error': f"User {row['username']} already exists"
                        })
                        results['failed'] += 1
                        continue
                    
                    # Get or create role
                    role = None
                    if row.get('role_name'):
                        try:
                            role = Role.objects.get(
                                name=row['role_name'],
                                company=request.user.company
                            )
                        except Role.DoesNotExist:
                            results['errors'].append({
                                'row': row_num,
                                'error': f"Role {row['role_name']} not found"
                            })
                            results['failed'] += 1
                            continue
                    
                    # Create user
                    user = User.objects.create_user(
                        username=row['username'],
                        email=row['email'],
                        password=row['password'],
                        first_name=row.get('first_name', ''),
                        last_name=row.get('last_name', ''),
                        company=request.user.company,
                        role=role,
                        is_company_admin=row.get('is_company_admin', '').lower() == 'true'
                    )
                    
                    results['success'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'row': row_num,
                        'error': str(e)
                    })
                    results['failed'] += 1
            
            # Log the import
            from .models import AuditLog
            AuditLog.log_action(
                user=request.user,
                action='import',
                module='users',
                description=f"Imported {results['success']} users from CSV",
                company=request.user.company,
                changes=results,
                request=request
            )
            
            return Response({
                'message': 'CSV import completed',
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error processing CSV: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserCSVExportView(APIView):
    """
    Export users to CSV file.
    """
    permission_classes = [IsAuthenticated, CanManageUsers]

    def get(self, request):
        import csv
        from django.http import HttpResponse
        
        # Get users from the same company
        users = User.objects.filter(company=request.user.company).select_related('role')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'First Name', 'Last Name', 
            'Role', 'Is Company Admin', 'Is Active', 'Date Joined'
        ])
        
        for user in users:
            writer.writerow([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.role.name if user.role else '',
                user.is_company_admin,
                user.is_active,
                user.date_joined.strftime('%Y-%m-%d')
            ])
        
        # Log the export
        from .models import AuditLog
        AuditLog.log_action(
            user=request.user,
            action='export',
            module='users',
            description=f"Exported {users.count()} users to CSV",
            company=request.user.company,
            request=request
        )
        
        return response


class AuditLogListView(generics.ListAPIView):
    """
    List audit logs with filtering options.
    Implements Requirement 10.3: Audit trail viewing.
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    
    def get_queryset(self):
        from .models import AuditLog
        queryset = AuditLog.objects.filter(company=self.request.user.company)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by module
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.select_related('user', 'company')
    
    def get_serializer_class(self):
        from .serializers import AuditLogSerializer
        return AuditLogSerializer
