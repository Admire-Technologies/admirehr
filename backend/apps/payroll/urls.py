"""
URL configuration for payroll app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.PayrollRecordViewSet)
router.register(r'salary-rules', views.SalaryRuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('generate/', views.GeneratePayrollView.as_view(), name='generate_payroll'),
]