"""
Serializers for job execution monitoring.
"""

from rest_framework import serializers
from .models import JobExecution


class JobExecutionSerializer(serializers.ModelSerializer):
    """
    Serializer for job execution records.
    """
    duration = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = JobExecution
        fields = [
            'id',
            'task_id',
            'task_name',
            'status',
            'args',
            'kwargs',
            'result',
            'error_message',
            'error_traceback',
            'retry_count',
            'created_at',
            'started_at',
            'completed_at',
            'worker_name',
            'queue_name',
            'duration',
            'is_completed'
        ]
        read_only_fields = fields


class JobExecutionDetailSerializer(JobExecutionSerializer):
    """
    Detailed serializer for job execution with full error traceback.
    """
    class Meta(JobExecutionSerializer.Meta):
        fields = JobExecutionSerializer.Meta.fields


class JobStatisticsSerializer(serializers.Serializer):
    """
    Serializer for job execution statistics.
    """
    total_jobs = serializers.IntegerField()
    pending_jobs = serializers.IntegerField()
    running_jobs = serializers.IntegerField()
    successful_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    retrying_jobs = serializers.IntegerField()
    avg_duration = serializers.FloatField()
    success_rate = serializers.FloatField()


class TriggerJobSerializer(serializers.Serializer):
    """
    Serializer for triggering background jobs.
    """
    job_type = serializers.ChoiceField(choices=[
        ('payroll_generation', 'Payroll Generation'),
        ('payroll_report', 'Payroll Report'),
        ('leave_report', 'Leave Report'),
        ('attendance_report', 'Attendance Report'),
        ('leave_balance_init', 'Initialize Leave Balances'),
    ])
    
    # Common parameters
    company_id = serializers.UUIDField(required=False)
    
    # Date range parameters
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    # Payroll specific
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    department_id = serializers.UUIDField(required=False)
    
    # Report specific
    report_type = serializers.ChoiceField(
        choices=['summary', 'detailed', 'department', 'employee', 'by_type'],
        required=False,
        default='summary'
    )
    
    # Leave balance specific
    year = serializers.IntegerField(required=False)
    
    def validate(self, data):
        """Validate based on job type."""
        job_type = data.get('job_type')
        
        if job_type == 'payroll_generation':
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError(
                    "start_date and end_date are required for payroll generation"
                )
        
        elif job_type in ['payroll_report', 'leave_report', 'attendance_report']:
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError(
                    "start_date and end_date are required for reports"
                )
        
        return data
