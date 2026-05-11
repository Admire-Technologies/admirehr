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
    ViewSet for managing employees with search, filter, and import/export.
    """
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.filter(company=self.request.user.company).select_related('department', 'branch')
        
        # Search by name, email, or employee_id
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
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
        
        # Filter by role/position
        position = self.request.query_params.get('position')
        if position:
            queryset = queryset.filter(position__icontains=position)
        
        return queryset.order_by('first_name', 'last_name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=['post'])
    def import_employees(self, request):
        """
        Import employees from CSV file.
        Expected CSV format: employee_id,first_name,last_name,email,department_name,position,hire_date,status
        """
        import csv
        import io
        from django.db import transaction
        
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            created_count = 0
            errors = []
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Find or validate department
                        dept_name = row.get('department_name', '').strip()
                        if not dept_name:
                            errors.append(f"Row {row_num}: Department name is required")
                            continue
                        
                        try:
                            department = Department.objects.get(
                                name=dept_name,
                                company=request.user.company
                            )
                        except Department.DoesNotExist:
                            errors.append(f"Row {row_num}: Department '{dept_name}' not found")
                            continue
                        
                        # Create employee
                        employee_data = {
                            'employee_id': row.get('employee_id', '').strip(),
                            'first_name': row.get('first_name', '').strip(),
                            'last_name': row.get('last_name', '').strip(),
                            'email': row.get('email', '').strip(),
                            'department': department,
                            'position': row.get('position', '').strip(),
                            'hire_date': row.get('hire_date', '').strip(),
                            'status': row.get('status', 'active').strip(),
                            'company': request.user.company
                        }
                        
                        # Validate required fields
                        if not all([employee_data['employee_id'], employee_data['first_name'], 
                                   employee_data['last_name'], employee_data['email'], 
                                   employee_data['hire_date']]):
                            errors.append(f"Row {row_num}: Missing required fields")
                            continue
                        
                        # Check for duplicate employee_id
                        if Employee.objects.filter(
                            employee_id=employee_data['employee_id'],
                            company=request.user.company
                        ).exists():
                            errors.append(f"Row {row_num}: Employee ID '{employee_data['employee_id']}' already exists")
                            continue
                        
                        Employee.objects.create(**employee_data)
                        created_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
            
            return Response({
                'success': True,
                'created_count': created_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED if created_count > 0 else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'error': f'Failed to process file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def export_employees(self, request):
        """
        Export employees to CSV file.
        """
        import csv
        from django.http import HttpResponse
        
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employees.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'First Name', 'Last Name', 'Email', 'Phone',
            'Department', 'Branch', 'Position', 'Hire Date', 'Status',
            'Date of Birth', 'Address', 'Emergency Contact Name', 'Emergency Contact Phone'
        ])
        
        for employee in queryset:
            writer.writerow([
                employee.employee_id,
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.phone or '',
                employee.department.name,
                employee.branch.name if employee.branch else '',
                employee.position or '',
                employee.hire_date,
                employee.status,
                employee.date_of_birth or '',
                employee.address or '',
                employee.emergency_contact_name or '',
                employee.emergency_contact_phone or ''
            ])
        
        return response