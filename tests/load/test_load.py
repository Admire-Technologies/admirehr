"""
Load Testing Suite for Admire HRMS

This module contains load tests for concurrent user scenarios using
locust for distributed load testing.
"""

from locust import HttpUser, task, between, events
import random
import json
from datetime import datetime, timedelta


class HRMSUser(HttpUser):
    """Simulates a typical HRMS user"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login when user starts"""
        self.login()
    
    def login(self):
        """Authenticate and get token"""
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "username": "admin",
                "password": "admin123"
            },
            catch_response=True
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
            self.headers = {}
    
    @task(10)
    def view_employees(self):
        """View employee list"""
        with self.client.get(
            "/api/v1/employees/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/employees/ [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(5)
    def view_employee_detail(self):
        """View specific employee details"""
        # Simulate viewing a random employee
        employee_id = random.randint(1, 100)
        with self.client.get(
            f"/api/v1/employees/{employee_id}/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/employees/[id]/ [GET]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(8)
    def view_attendance(self):
        """View attendance records"""
        with self.client.get(
            "/api/v1/attendance/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/attendance/ [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    def checkin_attendance(self):
        """Perform attendance check-in"""
        with self.client.post(
            "/api/v1/attendance/check-in/",
            headers=self.headers,
            json={
                "employee_id": f"EMP{random.randint(1, 100):03d}",
                "biometric_data": {"face_encoding": [random.random() for _ in range(128)]}
            },
            catch_response=True,
            name="/api/v1/attendance/check-in/ [POST]"
        ) as response:
            if response.status_code in [200, 201, 404, 400]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(6)
    def view_leave_requests(self):
        """View leave requests"""
        with self.client.get(
            "/api/v1/leave/requests/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/leave/requests/ [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def create_leave_request(self):
        """Create a leave request"""
        start_date = datetime.now() + timedelta(days=random.randint(7, 30))
        end_date = start_date + timedelta(days=random.randint(1, 5))
        
        with self.client.post(
            "/api/v1/leave/requests/",
            headers=self.headers,
            json={
                "leave_type": random.choice(["annual", "sick", "personal"]),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "reason": "Load test leave request"
            },
            catch_response=True,
            name="/api/v1/leave/requests/ [POST]"
        ) as response:
            if response.status_code in [201, 400, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(4)
    def view_payroll(self):
        """View payroll records"""
        with self.client.get(
            "/api/v1/payroll/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/payroll/ [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(7)
    def view_dashboard(self):
        """View dashboard metrics"""
        with self.client.get(
            "/api/v1/dashboard/metrics/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/dashboard/metrics/ [GET]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    def search_employees(self):
        """Search employees"""
        search_terms = ["john", "jane", "test", "admin", "emp"]
        search_term = random.choice(search_terms)
        
        with self.client.get(
            f"/api/v1/employees/?search={search_term}",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/employees/?search= [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


class ManagerUser(HttpUser):
    """Simulates a manager user with approval tasks"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login when user starts"""
        self.login()
    
    def login(self):
        """Authenticate and get token"""
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "username": "admin",
                "password": "admin123"
            },
            catch_response=True
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
            self.headers = {}
    
    @task(5)
    def view_pending_leave_requests(self):
        """View pending leave requests"""
        with self.client.get(
            "/api/v1/leave/requests/?status=pending",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/leave/requests/?status=pending [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    def view_team_attendance(self):
        """View team attendance"""
        with self.client.get(
            "/api/v1/attendance/?date=" + datetime.now().strftime("%Y-%m-%d"),
            headers=self.headers,
            catch_response=True,
            name="/api/v1/attendance/?date= [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def generate_reports(self):
        """Generate attendance reports"""
        with self.client.get(
            "/api/v1/attendance/reports/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/attendance/reports/ [GET]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


class HRAdminUser(HttpUser):
    """Simulates an HR admin user with management tasks"""
    
    wait_time = between(3, 7)
    
    def on_start(self):
        """Login when user starts"""
        self.login()
    
    def login(self):
        """Authenticate and get token"""
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "username": "admin",
                "password": "admin123"
            },
            catch_response=True
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
            self.headers = {}
    
    @task(4)
    def manage_employees(self):
        """View and manage employees"""
        with self.client.get(
            "/api/v1/employees/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/employees/ [ADMIN LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def manage_departments(self):
        """View departments"""
        with self.client.get(
            "/api/v1/departments/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/departments/ [LIST]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    def view_payroll_summary(self):
        """View payroll summary"""
        with self.client.get(
            "/api/v1/payroll/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/payroll/ [ADMIN LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    def manage_users(self):
        """View users"""
        with self.client.get(
            "/api/v1/users/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/users/ [LIST]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("Load test completed.")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
