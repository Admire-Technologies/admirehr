"""
URL configuration for leave management app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'requests', views.LeaveRequestViewSet, basename='leaverequest')
router.register(r'types', views.LeaveTypeViewSet, basename='leavetype')
router.register(r'balances', views.LeaveBalanceViewSet, basename='leavebalance')

urlpatterns = [
    path('', include(router.urls)),
]