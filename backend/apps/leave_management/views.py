"""
Leave management views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from apps.core.ws_utils import send_leave_status_change, send_notification
from .models import LeaveRequest, LeaveType, LeaveBalance
from .serializers import (
    LeaveRequestSerializer, LeaveTypeSerializer, LeaveBalanceSerializer,
    LeaveApprovalSerializer, LeaveCancellationSerializer, LeaveCalendarSerializer
)


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leave types.
    """
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name']

    def get_queryset(self):
        return LeaveType.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing leave balances.
    """
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'leave_type', 'year']

    def get_queryset(self):
        return LeaveBalance.objects.filter(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def my_balance(self, request):
        """Get leave balance for the current user's employee."""
        if not request.user.employee:
            return Response(
                {'error': 'User is not associated with an employee.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        year = request.query_params.get('year', datetime.now().year)
        balances = LeaveBalance.objects.filter(
            employee=request.user.employee,
            year=year,
            company=request.user.company
        )
        serializer = self.get_serializer(balances, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def initialize_balances(self, request):
        """Initialize leave balances for all employees for a given year."""
        year = request.data.get('year', datetime.now().year)
        
        from apps.employees.models import Employee
        employees = Employee.objects.filter(
            company=request.user.company,
            status='active'
        )
        
        leave_types = LeaveType.objects.filter(
            company=request.user.company,
            is_active=True
        )
        
        created_count = 0
        for employee in employees:
            for leave_type in leave_types:
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    company=request.user.company,
                    defaults={'accrued_days': leave_type.days_allowed}
                )
                if created:
                    created_count += 1
        
        return Response({
            'message': f'Initialized {created_count} leave balances for year {year}.',
            'year': year,
            'created_count': created_count
        })


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leave requests.
    """
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'leave_type', 'status']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['start_date', 'created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = LeaveRequest.objects.filter(company=self.request.user.company)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.select_related('employee', 'leave_type', 'approver')

    def get_serializer_context(self):
        """Add employee to serializer context."""
        context = super().get_serializer_context()
        if self.request.user.employee:
            context['employee'] = self.request.user.employee
        return context

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get leave requests for the current user's employee."""
        if not request.user.employee:
            return Response(
                {'error': 'User is not associated with an employee.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requests = self.get_queryset().filter(employee=request.user.employee)
        page = self.paginate_queryset(requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get pending leave requests that require approval."""
        if not request.user.employee:
            return Response(
                {'error': 'User is not associated with an employee.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get pending requests for employees in the same department
        # or where the current user is a manager
        requests = self.get_queryset().filter(
            status='pending',
            employee__department=request.user.employee.department
        ).exclude(employee=request.user.employee)
        
        page = self.paginate_queryset(requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve_reject(self, request, pk=None):
        """Approve or reject a leave request."""
        leave_request = self.get_object()
        
        if not request.user.employee:
            return Response(
                {'error': 'User is not associated with an employee.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = LeaveApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        
        try:
            if action_type == 'approve':
                leave_request.approve(request.user.employee)
                message = 'Leave request approved successfully.'
            else:
                rejection_reason = serializer.validated_data.get('rejection_reason', '')
                leave_request.reject(request.user.employee, rejection_reason)
                message = 'Leave request rejected successfully.'
            
            # Send WebSocket notification
            send_leave_status_change(
                company_id=str(leave_request.company.id),
                user_id=str(leave_request.employee.id),
                data={
                    'request_id': str(leave_request.id),
                    'status': leave_request.status,
                    'employee_id': str(leave_request.employee.id),
                    'approver_id': str(request.user.employee.id),
                    'leave_type': leave_request.leave_type.name,
                    'start_date': leave_request.start_date.isoformat(),
                    'end_date': leave_request.end_date.isoformat(),
                }
            )
            
            return Response({
                'message': message,
                'leave_request': LeaveRequestSerializer(leave_request).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a leave request."""
        leave_request = self.get_object()
        
        # Only the employee who created the request can cancel it
        if leave_request.employee != request.user.employee:
            return Response(
                {'error': 'You can only cancel your own leave requests.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LeaveCancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            leave_request.cancel(serializer.validated_data['cancellation_reason'])
            
            # Send WebSocket notification
            send_leave_status_change(
                company_id=str(leave_request.company.id),
                user_id=str(leave_request.employee.id),
                data={
                    'request_id': str(leave_request.id),
                    'status': leave_request.status,
                    'employee_id': str(leave_request.employee.id),
                    'leave_type': leave_request.leave_type.name,
                }
            )
            
            return Response({
                'message': 'Leave request cancelled successfully.',
                'leave_request': LeaveRequestSerializer(leave_request).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get leave calendar for visualization."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requests = LeaveRequest.objects.filter(
            company=request.user.company,
            status__in=['approved', 'pending'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('employee', 'leave_type')
        
        calendar_data = []
        for req in requests:
            calendar_data.append({
                'employee_id': str(req.employee.id),
                'employee_name': req.employee.full_name,
                'leave_type': req.leave_type.name,
                'start_date': req.start_date,
                'end_date': req.end_date,
                'days': req.days_requested,
                'status': req.status
            })
        
        serializer = LeaveCalendarSerializer(calendar_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Generate leave reports."""
        year = request.query_params.get('year', datetime.now().year)
        
        # Get leave statistics
        leave_requests = LeaveRequest.objects.filter(
            company=request.user.company,
            start_date__year=year
        )
        
        total_requests = leave_requests.count()
        approved_requests = leave_requests.filter(status='approved').count()
        rejected_requests = leave_requests.filter(status='rejected').count()
        pending_requests = leave_requests.filter(status='pending').count()
        
        # Get leave by type
        leave_by_type = {}
        for leave_type in LeaveType.objects.filter(company=request.user.company):
            days_used = leave_requests.filter(
                leave_type=leave_type,
                status='approved'
            ).aggregate(total=Sum('days_requested'))['total'] or 0
            
            leave_by_type[leave_type.name] = {
                'days_allowed': leave_type.days_allowed,
                'days_used': float(days_used),
                'requests_count': leave_requests.filter(leave_type=leave_type).count()
            }
        
        # Get upcoming leaves
        upcoming_leaves = LeaveRequest.objects.filter(
            company=request.user.company,
            status='approved',
            start_date__gte=timezone.now().date(),
            start_date__lte=timezone.now().date() + timedelta(days=30)
        ).select_related('employee', 'leave_type').order_by('start_date')
        
        upcoming_data = LeaveRequestSerializer(upcoming_leaves, many=True).data
        
        return Response({
            'year': year,
            'summary': {
                'total_requests': total_requests,
                'approved': approved_requests,
                'rejected': rejected_requests,
                'pending': pending_requests
            },
            'leave_by_type': leave_by_type,
            'upcoming_leaves': upcoming_data
        })