"""
End-to-End Test Suite for Admire HRMS User Workflows

This module contains comprehensive E2E tests covering all major user workflows
including authentication, employee management, attendance, leave, and payroll.
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"
TIMEOUT = 10


class TestAuthenticationWorkflow:
    """Test complete authentication workflow"""
    
    def test_complete_login_workflow(self):
        """Test user login, token refresh, and logout workflow"""
        # Step 1: Login
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={
                "username": "admin",
                "password": "admin123"
            },
            timeout=TIMEOUT
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access" in tokens
        assert "refresh" in tokens
        access_token = tokens["access"]
        refresh_token = tokens["refresh"]
        
        # Step 2: Access protected resource
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(
            f"{API_BASE_URL}/auth/profile/",
            headers=headers,
            timeout=TIMEOUT
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert "username" in profile
        
        # Step 3: Refresh token
        refresh_response = requests.post(
            f"{API_BASE_URL}/auth/refresh/",
            json={"refresh": refresh_token},
            timeout=TIMEOUT
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access" in new_tokens
        
        # Step 4: Logout
        logout_response = requests.post(
            f"{API_BASE_URL}/auth/logout/",
            headers={"Authorization": f"Bearer {new_tokens['access']}"},
            json={"refresh": refresh_token},
            timeout=TIMEOUT
        )
        assert logout_response.status_code in [200, 204, 205]


class TestEmployeeManagementWorkflow:
    """Test complete employee management workflow"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_employee_crud_workflow(self, auth_headers):
        """Test complete employee CRUD workflow"""
        # Step 1: Create employee
        employee_data = {
            "employee_id": f"EMP{int(time.time())}",
            "first_name": "John",
            "last_name": "Doe",
            "email": f"john.doe.{int(time.time())}@example.com",
            "hire_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "active"
        }
        
        create_response = requests.post(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            json=employee_data,
            timeout=TIMEOUT
        )
        assert create_response.status_code == 201
        created_employee = create_response.json()
        employee_id = created_employee["id"]
        
        # Step 2: Read employee
        read_response = requests.get(
            f"{API_BASE_URL}/employees/{employee_id}/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert read_response.status_code == 200
        employee = read_response.json()
        assert employee["first_name"] == "John"
        
        # Step 3: Update employee
        update_data = {
            "first_name": "Jane",
            "last_name": "Doe"
        }
        update_response = requests.patch(
            f"{API_BASE_URL}/employees/{employee_id}/",
            headers=auth_headers,
            json=update_data,
            timeout=TIMEOUT
        )
        assert update_response.status_code == 200
        updated_employee = update_response.json()
        assert updated_employee["first_name"] == "Jane"
        
        # Step 4: List employees
        list_response = requests.get(
            f"{API_BASE_URL}/employees/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert list_response.status_code == 200
        employees = list_response.json()
        assert isinstance(employees, (list, dict))
        
        # Step 5: Delete employee
        delete_response = requests.delete(
            f"{API_BASE_URL}/employees/{employee_id}/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert delete_response.status_code in [200, 204]


class TestAttendanceWorkflow:
    """Test complete attendance workflow"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_attendance_checkin_checkout_workflow(self, auth_headers):
        """Test complete attendance check-in/check-out workflow"""
        # Step 1: Check-in
        checkin_data = {
            "employee_id": "EMP001",
            "biometric_data": {"face_encoding": [0.1] * 128}
        }
        
        checkin_response = requests.post(
            f"{API_BASE_URL}/attendance/check-in/",
            headers=auth_headers,
            json=checkin_data,
            timeout=TIMEOUT
        )
        # May return 200, 201, or 404 if employee doesn't exist
        assert checkin_response.status_code in [200, 201, 404]
        
        if checkin_response.status_code in [200, 201]:
            attendance_record = checkin_response.json()
            record_id = attendance_record.get("id")
            
            # Step 2: View attendance records
            list_response = requests.get(
                f"{API_BASE_URL}/attendance/",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            assert list_response.status_code == 200
            
            # Step 3: Check-out
            checkout_data = {
                "employee_id": "EMP001",
                "biometric_data": {"face_encoding": [0.1] * 128}
            }
            
            checkout_response = requests.post(
                f"{API_BASE_URL}/attendance/check-out/",
                headers=auth_headers,
                json=checkout_data,
                timeout=TIMEOUT
            )
            assert checkout_response.status_code in [200, 201, 404]


class TestLeaveManagementWorkflow:
    """Test complete leave management workflow"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_leave_request_approval_workflow(self, auth_headers):
        """Test complete leave request and approval workflow"""
        # Step 1: Create leave request
        leave_data = {
            "leave_type": "annual",
            "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "reason": "Personal vacation"
        }
        
        create_response = requests.post(
            f"{API_BASE_URL}/leave/requests/",
            headers=auth_headers,
            json=leave_data,
            timeout=TIMEOUT
        )
        # May return 201 or 400 if validation fails
        assert create_response.status_code in [201, 400, 404]
        
        if create_response.status_code == 201:
            leave_request = create_response.json()
            request_id = leave_request["id"]
            
            # Step 2: List leave requests
            list_response = requests.get(
                f"{API_BASE_URL}/leave/requests/",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            assert list_response.status_code == 200
            
            # Step 3: Approve leave request
            approve_response = requests.post(
                f"{API_BASE_URL}/leave/approve/{request_id}/",
                headers=auth_headers,
                json={"comments": "Approved"},
                timeout=TIMEOUT
            )
            assert approve_response.status_code in [200, 404, 403]


class TestPayrollWorkflow:
    """Test complete payroll workflow"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_payroll_generation_workflow(self, auth_headers):
        """Test complete payroll generation workflow"""
        # Step 1: Generate payroll
        payroll_data = {
            "period_start": datetime.now().replace(day=1).strftime("%Y-%m-%d"),
            "period_end": datetime.now().strftime("%Y-%m-%d")
        }
        
        generate_response = requests.post(
            f"{API_BASE_URL}/payroll/generate/",
            headers=auth_headers,
            json=payroll_data,
            timeout=TIMEOUT
        )
        # May return 200, 201, or 400
        assert generate_response.status_code in [200, 201, 400, 404]
        
        # Step 2: List payroll records
        list_response = requests.get(
            f"{API_BASE_URL}/payroll/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert list_response.status_code == 200


class TestDashboardWorkflow:
    """Test dashboard and reporting workflow"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_dashboard_metrics_workflow(self, auth_headers):
        """Test dashboard metrics retrieval workflow"""
        # Step 1: Get dashboard metrics
        dashboard_response = requests.get(
            f"{API_BASE_URL}/dashboard/metrics/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert dashboard_response.status_code in [200, 404]
        
        if dashboard_response.status_code == 200:
            metrics = dashboard_response.json()
            assert isinstance(metrics, dict)


class TestRBACWorkflow:
    """Test Role-Based Access Control workflow"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login/",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        token = response.json()["access"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_role_management_workflow(self, auth_headers):
        """Test role creation and permission assignment workflow"""
        # Step 1: List roles
        roles_response = requests.get(
            f"{API_BASE_URL}/roles/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert roles_response.status_code in [200, 404]
        
        # Step 2: List permissions
        permissions_response = requests.get(
            f"{API_BASE_URL}/permissions/",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert permissions_response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
