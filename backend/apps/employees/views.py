"""
Employee management views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Employee, Department, Branch
from .serializers import EmployeeSerializer, DepartmentSerializer, BranchSerializer


class BranchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing branches.
    """
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Branch.objects.filter(company=self.request.user.company).select_related('parent')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """
        Get branch hierarchy with employee counts.
        """
        branches = self.get_queryset()
        
        # Build hierarchy tree
        branch_dict = {}
        for b in branches:
            branch_dict[str(b.id)] = {
                'id': str(b.id),
                'name': b.name,
                'code': b.code,
                'employee_count': b.employee_set.filter(status='active').count(),
                'parent': str(b.parent.id) if b.parent else None,
                'children': []
            }
        
        # Build tree structure
        root_branches = []
        for branch_id, branch_data in branch_dict.items():
            if branch_data['parent']:
                parent = branch_dict.get(branch_data['parent'])
                if parent:
                    parent['children'].append(branch_data)
            else:
                root_branches.append(branch_data)
        
        return Response(root_branches)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments.
    """
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Department.objects.filter(company=self.request.user.company).select_related('parent')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """
        Get department hierarchy with employee counts.
        """
        departments = self.get_queryset()
        
        # Build hierarchy tree
        dept_dict = {}
        for d in departments:
            dept_dict[str(d.id)] = {
                'id': str(d.id),
                'name': d.name,
                'description': d.description,
                'employee_count': d.employee_set.filter(status='active').count(),
                'parent': str(d.parent.id) if d.parent else None,
                'children': []
            }
        
        # Build tree structure
        root_departments = []
        for dept_id, dept_data in dept_dict.items():
            if dept_data['parent']:
                parent = dept_dict.get(dept_data['parent'])
                if parent:
                    parent['children'].append(dept_data)
            else:
                root_departments.append(dept_data)
        
        return Response(root_departments)

    def destroy(self, request, *args, **kwargs):
        """
        Prevent deletion if department has employees.
        """
        department = self.get_object()
        employee_count = department.employee_set.filter(status='active').count()
        
        if employee_count > 0:
            return Response(
                {'error': f'Cannot delete department with {employee_count} active employees. Please reassign employees first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees.
    """
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.filter(company=self.request.user.company).select_related('department', 'branch')
        
        # Filter by department
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)