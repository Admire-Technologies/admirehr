"""
URL configuration for payroll app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'records', views.PayrollRecordViewSet, basename='payroll-record')
router.register(r'salary-rules', views.SalaryRuleViewSet, basename='salary-rule')
router.register(r'salary-structures', views.EmployeeSalaryStructureViewSet, basename='salary-structure')

urlpatterns = [
    path('', include(router.urls)),
    path('generate/', views.GeneratePayrollView.as_view(), name='generate-payroll'),
    path('bulk-process/', views.BulkPayrollProcessView.as_view(), name='bulk-process-payroll'),
    path('reports/', views.PayrollReportsView.as_view(), name='payroll-reports'),
    path('payslip/<uuid:payroll_id>/pdf/', views.PayslipPDFView.as_view(), name='payslip-pdf'),
]