"""
URL configuration for attendance app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.AttendanceRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check-in/', views.CheckInView.as_view(), name='check_in'),
    path('check-out/', views.CheckOutView.as_view(), name='check_out'),
]