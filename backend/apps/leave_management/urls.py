"""
URL configuration for leave management app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'requests', views.LeaveRequestViewSet)
router.register(r'types', views.LeaveTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]