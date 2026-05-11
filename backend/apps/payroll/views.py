"""
Payroll management views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import PayrollRecord, SalaryRule, EmployeeSalaryStructure
from .serializers import (
    PayrollRecordSerializer,
    PayrollRecordDetailSerializer,
    SalaryRuleSerializer,
    EmployeeSalaryStructureSerializer,
    PayrollGenerationSerializer,
    BulkPayrollProcessSerializer,
    PayrollSummarySerializer
)
from .services import PayrollCalculationService, PayrollCalculationError
from .pdf_generator import generate_payslip_pdf
from apps.employees.models import Employee


class SalaryRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing salary rules.
    
    Provides CRUD operations for salary rules including allowances,
    deductions, and basic salary configurations.
    """
    serializer_class = SalaryRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = SalaryRule.objects.filter(company=self.request.user.company)
        
        # Filter by rule type
        rule_type = self.request.query_params.get('rule_type')
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class EmployeeSalaryStructureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee-specific salary structures.
    """
    serializer_class = EmployeeSalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = EmployeeSalaryStructure.objects.filter(
            company=self.request.user.company
        ).select_related('employee', 'salary_rule')
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class PayrollRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payroll records.
    
    Provides listing, retrieval, and management of payroll records
    with filtering by employee, department, and date range.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PayrollRecordDetailSerializer
        return PayrollRecordSerializer

    def get_queryset(self):
        queryset = PayrollRecord.objects.filter(
            company=self.request.user.company
        ).select_related('employee', 'employee__department', 'processed_by')
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by department
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        
        # Filter by period
        period_start = self.request.query_params.get('period_start')
        period_end = self.request.query_params.get('period_end')
        if period_start:
            queryset = queryset.filter(period_start__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_end__lte=period_end)
        
        # Filter by processed status
        is_processed = self.request.query_params.get('is_processed')
        if is_processed is not None:
            queryset = queryset.filter(is_processed=is_processed.lower() == 'true')
        
        return queryset.order_by('-period_start', 'employee__first_name')

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            processed_by=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def payslip(self, request, pk=None):
        """
        Get payslip data for a specific payroll record.
        """
        payroll_record = self.get_object()
        serializer = PayrollRecordDetailSerializer(payroll_record)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get payroll summary statistics for a period.
        """
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')
        department_id = request.query_params.get('department_id')
        
        if not period_start or not period_end:
            return Response(
                {'error': 'period_start and period_end are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = PayrollCalculationService(request.user.company)
        summary = service.get_payroll_summary(
            period_start=datetime.fromisoformat(period_start).date(),
            period_end=datetime.fromisoformat(period_end).date(),
            department_id=department_id
        )
        
        serializer = PayrollSummarySerializer(summary)
        return Response(serializer.data)


class GeneratePayrollView(APIView):
    """
    API view for generating payroll for a specific period.
    
    POST /api/v1/payroll/generate/
    {
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "employee_ids": ["uuid1", "uuid2"]  // optional
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PayrollGenerationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        period_start = data['period_start']
        period_end = data['period_end']
        employee_ids = data.get('employee_ids')
        
        # Initialize payroll service
        service = PayrollCalculationService(request.user.company)
        
        try:
            # Generate payroll
            results = service.bulk_generate_payroll(
                period_start=period_start,
                period_end=period_end,
                employee_ids=employee_ids
            )
            
            return Response({
                'message': 'Payroll generation completed',
                'period_start': period_start,
                'period_end': period_end,
                'results': results
            }, status=status.HTTP_201_CREATED)
            
        except PayrollCalculationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Payroll generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkPayrollProcessView(APIView):
    """
    API view for bulk payroll processing with advanced filtering.
    
    POST /api/v1/payroll/bulk-process/
    {
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "department_id": "uuid",  // optional
        "employee_ids": ["uuid1", "uuid2"]  // optional
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BulkPayrollProcessSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        period_start = data['period_start']
        period_end = data['period_end']
        department_id = data.get('department_id')
        employee_ids = data.get('employee_ids')
        
        # Build employee queryset
        employees = Employee.objects.filter(
            company=request.user.company,
            status='active'
        )
        
        if department_id:
            employees = employees.filter(department_id=department_id)
        
        if employee_ids:
            employees = employees.filter(id__in=employee_ids)
        
        # Initialize payroll service
        service = PayrollCalculationService(request.user.company)
        
        # Process payroll for filtered employees
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for employee in employees:
            results['total'] += 1
            try:
                service.generate_payroll_record(employee, period_start, period_end)
                results['successful'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'employee_id': str(employee.id),
                    'employee_name': employee.full_name,
                    'error': str(e)
                })
        
        return Response({
            'message': 'Bulk payroll processing completed',
            'results': results
        }, status=status.HTTP_200_OK)


class PayrollReportsView(APIView):
    """
    API view for generating payroll reports and analytics.
    
    GET /api/v1/payroll/reports/?period_start=2024-01-01&period_end=2024-01-31
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')
        department_id = request.query_params.get('department_id')
        report_type = request.query_params.get('type', 'summary')
        
        if not period_start or not period_end:
            return Response(
                {'error': 'period_start and period_end are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert to date objects
        period_start = datetime.fromisoformat(period_start).date()
        period_end = datetime.fromisoformat(period_end).date()
        
        # Get payroll records
        payroll_records = PayrollRecord.objects.filter(
            company=request.user.company,
            period_start=period_start,
            period_end=period_end
        ).select_related('employee', 'employee__department')
        
        if department_id:
            payroll_records = payroll_records.filter(
                employee__department_id=department_id
            )
        
        if report_type == 'summary':
            # Generate summary report
            service = PayrollCalculationService(request.user.company)
            summary = service.get_payroll_summary(
                period_start, period_end, department_id
            )
            return Response(summary)
        
        elif report_type == 'detailed':
            # Generate detailed report
            serializer = PayrollRecordSerializer(payroll_records, many=True)
            return Response({
                'period_start': period_start,
                'period_end': period_end,
                'records': serializer.data
            })
        
        elif report_type == 'department':
            # Generate department-wise report
            from django.db.models import Sum, Count
            from apps.employees.models import Department
            
            departments = Department.objects.filter(
                company=request.user.company
            )
            
            department_data = []
            for dept in departments:
                dept_payroll = payroll_records.filter(employee__department=dept)
                dept_summary = dept_payroll.aggregate(
                    employee_count=Count('id'),
                    total_net_salary=Sum('net_salary'),
                    total_gross_salary=Sum('gross_salary'),
                    total_deductions=Sum('deductions')
                )
                
                department_data.append({
                    'department_id': str(dept.id),
                    'department_name': dept.name,
                    **dept_summary
                })
            
            return Response({
                'period_start': period_start,
                'period_end': period_end,
                'departments': department_data
            })
        
        else:
            return Response(
                {'error': f'Invalid report type: {report_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PayslipPDFView(APIView):
    """
    API view for generating and downloading payslip PDF.
    
    GET /api/v1/payroll/payslip/<payroll_id>/pdf/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, payroll_id):
        # Get the payroll record
        payroll_record = get_object_or_404(
            PayrollRecord,
            id=payroll_id,
            company=request.user.company
        )
        
        try:
            # Generate PDF
            pdf_bytes, filename = generate_payslip_pdf(payroll_record)
            
            # Create HTTP response with PDF
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )