"""
URL configuration for dashboard and reporting API.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Report generation and export
    path('reports/generate/', views.ReportGenerationView.as_view(), name='report-generate'),
    path('reports/export/', views.ReportExportView.as_view(), name='report-export'),
    
    # Dashboard metrics
    path('metrics/', views.DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('attendance-trends/', views.AttendanceTrendsView.as_view(), name='attendance-trends'),
    path('leave-patterns/', views.LeavePatternsView.as_view(), name='leave-patterns'),
    path('payroll-summary/', views.PayrollSummaryView.as_view(), name='payroll-summary'),
    
    # Widget management
    path('widgets/', views.DashboardWidgetViewSet.as_view({'get': 'list', 'post': 'create'}), name='widget-list'),
    path('widgets/<uuid:pk>/', views.DashboardWidgetViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='widget-detail'),
    
    # Scheduled report management
    path('scheduled-reports/', views.ScheduledReportViewSet.as_view({'get': 'list', 'post': 'create'}), name='scheduled-report-list'),
    path('scheduled-reports/<uuid:pk>/', views.ScheduledReportViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='scheduled-report-detail'),
]
