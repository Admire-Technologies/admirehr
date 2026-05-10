"""
URL patterns for core app.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Health check and dashboard
    path('health/', views.health_check, name='health_check'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # Company management
    path('companies/register/', views.CompanyRegistrationView.as_view(), name='company_register'),
    path('companies/current/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('companies/settings/', views.CompanySettingsView.as_view(), name='company_settings'),
]