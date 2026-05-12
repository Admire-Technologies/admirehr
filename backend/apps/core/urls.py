"""
URL patterns for core app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_jobs import (
    JobExecutionViewSet,
    TriggerJobView,
    CeleryHealthCheckView,
    JobQueueStatusView
)
from .views_api_docs import APIInfoView, APIHealthView, APIMetricsView
from .views_throttle import ThrottleStatusView, ThrottleResetView, RateLimitConfigView
from .views_health import (
    health_check,
    health_detailed,
    readiness_check,
    liveness_check,
    metrics_endpoint,
    system_status
)

app_name = 'core'

# Create router for viewsets
router = DefaultRouter()
router.register(r'jobs', JobExecutionViewSet, basename='job-execution')

urlpatterns = [
    # Health Check Endpoints (Public)
    path('health/', health_check, name='health_check_simple'),
    path('health/detailed/', health_detailed, name='health_check_detailed'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    
    # Monitoring Endpoints (Authenticated)
    path('monitoring/metrics/', metrics_endpoint, name='metrics'),
    path('monitoring/status/', system_status, name='system_status'),
    
    # API Information and Health
    path('api/info/', APIInfoView.as_view(), name='api_info'),
    path('api/health/', APIHealthView.as_view(), name='api_health'),
    path('api/metrics/', APIMetricsView.as_view(), name='api_metrics'),
    
    # API Throttling Management
    path('api/throttle/status/', ThrottleStatusView.as_view(), name='throttle_status'),
    path('api/throttle/reset/', ThrottleResetView.as_view(), name='throttle_reset'),
    path('api/throttle/config/', RateLimitConfigView.as_view(), name='rate_limit_config'),
    
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # Company management
    path('companies/register/', views.CompanyRegistrationView.as_view(), name='company_register'),
    path('companies/current/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('companies/settings/', views.CompanySettingsView.as_view(), name='company_settings'),
    
    # GDPR Compliance
    path('gdpr/export/', views.GDPRDataExportView.as_view(), name='gdpr_export'),
    path('gdpr/export/<uuid:employee_id>/', views.GDPRDataExportView.as_view(), name='gdpr_export_employee'),
    path('gdpr/delete/<uuid:employee_id>/', views.GDPRDataDeletionView.as_view(), name='gdpr_delete'),
    path('gdpr/report/', views.GDPRDataProcessingReportView.as_view(), name='gdpr_report'),
    
    # Security Management
    path('security/events/', views.SecurityEventListView.as_view(), name='security_events'),
    
    # Job Management and Monitoring
    path('jobs/trigger/', TriggerJobView.as_view(), name='trigger_job'),
    path('jobs/health/', CeleryHealthCheckView.as_view(), name='celery_health'),
    path('jobs/queue-status/', JobQueueStatusView.as_view(), name='queue_status'),
    path('', include(router.urls)),
]