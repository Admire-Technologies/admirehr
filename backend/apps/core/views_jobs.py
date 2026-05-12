"""
Views for job execution monitoring and management.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import JobExecution
from .serializers_jobs import (
    JobExecutionSerializer,
    JobExecutionDetailSerializer,
    JobStatisticsSerializer,
    TriggerJobSerializer
)


class JobExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing job execution records.
    Provides monitoring and tracking of background tasks.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobExecutionDetailSerializer
        return JobExecutionSerializer
    
    def get_queryset(self):
        queryset = JobExecution.objects.all()
        
        # Filter by task name
        task_name = self.request.query_params.get('task_name')
        if task_name:
            queryset = queryset.filter(task_name__icontains=task_name)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get job execution statistics.
        """
        # Get time range (default: last 24 hours)
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        jobs = JobExecution.objects.filter(created_at__gte=since)
        
        stats = jobs.aggregate(
            total_jobs=Count('id'),
            pending_jobs=Count('id', filter=Q(status='pending')),
            running_jobs=Count('id', filter=Q(status='running')),
            successful_jobs=Count('id', filter=Q(status='success')),
            failed_jobs=Count('id', filter=Q(status='failed')),
            retrying_jobs=Count('id', filter=Q(status='retrying')),
        )
        
        # Calculate average duration for completed jobs
        completed_jobs = jobs.filter(
            status__in=['success', 'failed'],
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        if completed_jobs.exists():
            durations = [
                (job.completed_at - job.started_at).total_seconds()
                for job in completed_jobs
            ]
            stats['avg_duration'] = sum(durations) / len(durations)
        else:
            stats['avg_duration'] = 0
        
        # Calculate success rate
        total_completed = stats['successful_jobs'] + stats['failed_jobs']
        if total_completed > 0:
            stats['success_rate'] = (stats['successful_jobs'] / total_completed) * 100
        else:
            stats['success_rate'] = 0
        
        serializer = JobStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_failures(self, request):
        """
        Get recent failed jobs.
        """
        limit = int(request.query_params.get('limit', 10))
        
        failed_jobs = JobExecution.objects.filter(
            status='failed'
        ).order_by('-created_at')[:limit]
        
        serializer = self.get_serializer(failed_jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def task_summary(self, request):
        """
        Get summary of jobs grouped by task name.
        """
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        # Group by task name
        task_summary = JobExecution.objects.filter(
            created_at__gte=since
        ).values('task_name').annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending')),
            running=Count('id', filter=Q(status='running'))
        ).order_by('-total')
        
        return Response(list(task_summary))


class TriggerJobView(APIView):
    """
    API view for manually triggering background jobs.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Trigger a background job.
        """
        serializer = TriggerJobSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        job_type = data['job_type']
        company_id = data.get('company_id', str(request.user.company.id))
        
        try:
            if job_type == 'payroll_generation':
                from apps.payroll.tasks import bulk_generate_payroll
                
                task = bulk_generate_payroll.delay(
                    company_id=company_id,
                    period_start=data['start_date'].isoformat(),
                    period_end=data['end_date'].isoformat(),
                    employee_ids=[str(id) for id in data.get('employee_ids', [])] if data.get('employee_ids') else None,
                    department_id=str(data['department_id']) if data.get('department_id') else None
                )
                
                message = 'Payroll generation job queued successfully'
            
            elif job_type == 'payroll_report':
                from apps.payroll.tasks import generate_payroll_report
                
                task = generate_payroll_report.delay(
                    company_id=company_id,
                    period_start=data['start_date'].isoformat(),
                    period_end=data['end_date'].isoformat(),
                    report_type=data.get('report_type', 'summary')
                )
                
                message = 'Payroll report generation job queued successfully'
            
            elif job_type == 'leave_report':
                from apps.leave_management.tasks import generate_leave_report
                
                task = generate_leave_report.delay(
                    company_id=company_id,
                    start_date=data['start_date'].isoformat(),
                    end_date=data['end_date'].isoformat(),
                    report_type=data.get('report_type', 'summary')
                )
                
                message = 'Leave report generation job queued successfully'
            
            elif job_type == 'attendance_report':
                from apps.attendance.tasks import generate_attendance_report
                
                task = generate_attendance_report.delay(
                    company_id=company_id,
                    start_date=data['start_date'].isoformat(),
                    end_date=data['end_date'].isoformat(),
                    report_type=data.get('report_type', 'summary'),
                    department_id=str(data['department_id']) if data.get('department_id') else None
                )
                
                message = 'Attendance report generation job queued successfully'
            
            elif job_type == 'leave_balance_init':
                from apps.leave_management.tasks import initialize_annual_leave_balances
                
                task = initialize_annual_leave_balances.delay(
                    company_id=company_id,
                    year=data.get('year')
                )
                
                message = 'Leave balance initialization job queued successfully'
            
            else:
                return Response(
                    {'error': f'Unknown job type: {job_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': message,
                'task_id': task.id,
                'job_type': job_type
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to queue job: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CeleryHealthCheckView(APIView):
    """
    API view for checking Celery worker health.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Check Celery worker health status.
        """
        try:
            from celery import current_app
            
            # Get active workers
            inspect = current_app.control.inspect()
            
            # Check if workers are available
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            stats = inspect.stats()
            
            if not active_workers:
                return Response({
                    'status': 'unhealthy',
                    'message': 'No active Celery workers found',
                    'workers': []
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            worker_info = []
            for worker_name, tasks in active_workers.items():
                worker_info.append({
                    'name': worker_name,
                    'active_tasks': len(tasks),
                    'registered_tasks': len(registered_tasks.get(worker_name, [])),
                    'stats': stats.get(worker_name, {})
                })
            
            return Response({
                'status': 'healthy',
                'message': f'{len(active_workers)} worker(s) active',
                'workers': worker_info
            })
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to check worker health: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobQueueStatusView(APIView):
    """
    API view for checking job queue status.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get current job queue status.
        """
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            
            # Get queue information
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            queue_status = {
                'active_tasks': sum(len(tasks) for tasks in (active_tasks or {}).values()),
                'scheduled_tasks': sum(len(tasks) for tasks in (scheduled_tasks or {}).values()),
                'reserved_tasks': sum(len(tasks) for tasks in (reserved_tasks or {}).values()),
            }
            
            # Get recent job statistics
            recent_jobs = JobExecution.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).aggregate(
                total=Count('id'),
                pending=Count('id', filter=Q(status='pending')),
                running=Count('id', filter=Q(status='running')),
                success=Count('id', filter=Q(status='success')),
                failed=Count('id', filter=Q(status='failed'))
            )
            
            return Response({
                'queue_status': queue_status,
                'recent_jobs': recent_jobs,
                'timestamp': timezone.now().isoformat()
            })
        
        except Exception as e:
            return Response({
                'error': f'Failed to get queue status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
