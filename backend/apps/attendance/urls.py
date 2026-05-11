"""
URL configuration for attendance app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'records', views.AttendanceRecordViewSet, basename='attendance')

urlpatterns = [
    path('check-in/', views.CheckInView.as_view(), name='check_in'),
    path('check-out/', views.CheckOutView.as_view(), name='check_out'),
    path('', include(router.urls)),
]