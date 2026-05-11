"""
Serializers for dashboard and reporting API.
"""
from rest_framework import serializers
from .models import DashboardWidget, ScheduledReport


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializer for dashboard widget configuration."""
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'widget_type', 'position', 'size', 'settings',
            'is_visible', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['company'] = self.context['request'].user.company
        return super().create(validated_data)


class ScheduledReportSerializer(serializers.ModelSerializer):
    """Serializer for scheduled report configuration."""
    
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'name', 'report_type', 'frequency', 'format',
            'recipients', 'filters', 'is_active', 'last_run',
            'next_run', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'next_run', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['company'] = self.context['request'].user.company
        return super().create(validated_data)


class DashboardMetricsSerializer(serializers.Serializer):
    """Serializer for dashboard metrics data."""
    present_count = serializers.IntegerField()
    on_leave_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    total_employees = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
