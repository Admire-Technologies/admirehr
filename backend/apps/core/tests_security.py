"""
Security tests for encryption, monitoring, and GDPR compliance.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from apps.core.models import Company, SecurityPolicy, DataBackup, SecurityEvent
from apps.core.encryption import get_data_encryption, DataEncryption
from apps.core.security_monitor import get_security_monitor, SecurityMonitor
from apps.core.gdpr import get_gdpr_compliance, GDPRCompliance
from apps.employees.models import Employee, Department
from apps.attendance.models import AttendanceRecord
from apps.authentication.models import Role, Permission

User = get_user_model()


class DataEncryptionTest(TestCase):
    """Test data encryption and decryption."""
    
    def setUp(self):
        self.encryption = DataEncryption()
    
    def test_encrypt_string(self):
        """Test encryption of string data."""
        original = "sensitive information"
        encrypted = self.encryption.encrypt(original)
        
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, original)
    
    def test_decrypt_string(self):
        """Test decryption of string data."""
        original = "sensitive information"
        encrypted = self.encryption.encrypt(original)
        decrypted = self.encryption.decrypt(encrypted)
        
        self.assertEqual(decrypted, original)
    
    def test_encrypt_dict(self):
        """Test encryption of dictionary data."""
        original = {
            'name': 'John Doe',
            'ssn': '123-45-6789',
            'salary': 50000
        }
        encrypted = self.encryption.encrypt(original)
        decrypted = self.encryption.decrypt(encrypted)
        
        self.assertEqual(decrypted, original)
    
    def test_encrypt_none(self):
        """Test encryption with None data."""
        encrypted = self.encryption.encrypt(None)
        self.assertIsNone(encrypted)
    
    def test_decrypt_none(self):
        """Test decryption with None data."""
        decrypted = self.encryption.decrypt(None)
        self.assertIsNone(decrypted)
    
    def test_encrypt_field(self):
        """Test field encryption helper."""
        original = "field value"
        encrypted = self.encryption.encrypt_field(original)
        decrypted = self.encryption.decrypt_field(encrypted)
        
        self.assertEqual(decrypted, original)
    
    def test_singleton_instance(self):
        """Test singleton pattern for encryption instance."""
        instance1 = get_data_encryption()
        instance2 = get_data_encryption()
        
        self.assertIs(instance1, instance2)


class SecurityMonitorTest(TestCase):
    """Test security monitoring and intrusion detection."""
    
    def setUp(self):
        self.monitor = SecurityMonitor()
        self.username = "testuser"
        self.ip_address = "192.168.1.100"
        # Clear cache before each test
        from django.core.cache import cache
        cache.clear()
    
    def test_record_successful_login(self):
        """Test recording successful login attempt."""
        result = self.monitor.record_login_attempt(
            self.username, self.ip_address, success=True
        )
        
        self.assertTrue(result['allowed'])
        self.assertEqual(result['attempts'], 0)
        self.assertIsNone(result['blocked_until'])
    
    def test_record_failed_login(self):
        """Test recording failed login attempt."""
        result = self.monitor.record_login_attempt(
            self.username, self.ip_address, success=False
        )
        
        self.assertTrue(result['allowed'])
        self.assertEqual(result['attempts'], 1)
    
    def test_block_after_max_attempts(self):
        """Test blocking after maximum failed attempts."""
        # Make max failed attempts
        for i in range(self.monitor.MAX_LOGIN_ATTEMPTS):
            result = self.monitor.record_login_attempt(
                self.username, self.ip_address, success=False
            )
        
        # Should be blocked now
        self.assertFalse(result['allowed'])
        self.assertIsNotNone(result['blocked_until'])
    
    def test_is_blocked(self):
        """Test checking if user is blocked."""
        # Block user
        for i in range(self.monitor.MAX_LOGIN_ATTEMPTS):
            self.monitor.record_login_attempt(
                self.username, self.ip_address, success=False
            )
        
        is_blocked, blocked_until = self.monitor.is_blocked(
            self.username, self.ip_address
        )
        
        self.assertTrue(is_blocked)
        self.assertIsNotNone(blocked_until)
    
    def test_unblock(self):
        """Test manually unblocking a user."""
        # Block user
        for i in range(self.monitor.MAX_LOGIN_ATTEMPTS):
            self.monitor.record_login_attempt(
                self.username, self.ip_address, success=False
            )
        
        # Unblock
        self.monitor.unblock(self.username, self.ip_address)
        
        is_blocked, _ = self.monitor.is_blocked(self.username, self.ip_address)
        self.assertFalse(is_blocked)
    
    def test_api_rate_limiting(self):
        """Test API request rate limiting."""
        user_id = "test-user-id"
        
        # Make requests up to limit
        for i in range(self.monitor.MAX_API_REQUESTS):
            result = self.monitor.record_api_request(
                user_id, self.ip_address, "/api/test"
            )
        
        self.assertTrue(result['allowed'])
        
        # Next request should be blocked
        result = self.monitor.record_api_request(
            user_id, self.ip_address, "/api/test"
        )
        self.assertFalse(result['allowed'])
    
    def test_record_security_event(self):
        """Test recording security events."""
        user_id = "test-user-id"
        
        self.monitor.record_security_event(
            event_type='unauthorized_access',
            user_id=user_id,
            ip_address=self.ip_address,
            details={'resource': '/admin/'}
        )
        
        events = self.monitor.get_security_events('unauthorized_access', user_id)
        self.assertEqual(len(events), 1)
    
    def test_detect_suspicious_activity(self):
        """Test suspicious activity detection."""
        user_id = "test-user-id"
        
        # Create suspicious pattern - multiple failed logins
        for i in range(3):
            self.monitor.record_login_attempt(
                user_id, self.ip_address, success=False
            )
        
        result = self.monitor.detect_suspicious_activity(user_id, self.ip_address)
        
        self.assertTrue(result['suspicious'])
        self.assertGreater(len(result['reasons']), 0)
    
    def test_singleton_instance(self):
        """Test singleton pattern for security monitor."""
        instance1 = get_security_monitor()
        instance2 = get_security_monitor()
        
        self.assertIs(instance1, instance2)


class GDPRComplianceTest(TestCase):
    """Test GDPR compliance features."""
    
    def setUp(self):
        # Create company
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        
        # Create department
        self.department = Department.objects.create(
            name="Engineering",
            company=self.company
        )
        
        # Create employee
        self.employee = Employee.objects.create(
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            phone="1234567890",
            department=self.department,
            company=self.company,
            hire_date=timezone.now().date(),
            status='active'
        )
        
        self.gdpr = GDPRCompliance()
    
    def test_export_employee_data(self):
        """Test exporting employee data."""
        data = self.gdpr.export_employee_data(self.employee)
        
        self.assertIn('export_date', data)
        self.assertIn('employee_id', data)
        self.assertIn('personal_information', data)
        self.assertIn('attendance_records', data)
        self.assertIn('leave_requests', data)
        self.assertIn('payroll_records', data)
        
        # Check personal information
        personal = data['personal_information']
        self.assertEqual(personal['first_name'], 'John')
        self.assertEqual(personal['last_name'], 'Doe')
        self.assertEqual(personal['email'], 'john.doe@test.com')
    
    def test_anonymize_employee_data(self):
        """Test anonymizing employee data."""
        original_email = self.employee.email
        
        summary = self.gdpr.delete_employee_data(self.employee, anonymize=True)
        
        # Refresh from database
        self.employee.refresh_from_db()
        
        self.assertTrue(summary['anonymized'])
        self.assertNotEqual(self.employee.email, original_email)
        self.assertTrue(self.employee.email.startswith('deleted_'))
        self.assertEqual(self.employee.status, 'terminated')
    
    def test_generate_data_processing_report(self):
        """Test generating data processing report."""
        report = self.gdpr.generate_data_processing_report(self.company)
        
        self.assertIn('company', report)
        self.assertIn('report_date', report)
        self.assertIn('data_categories', report)
        self.assertIn('security_measures', report)
        self.assertIn('data_retention', report)
        
        self.assertEqual(report['company'], self.company.name)
    
    def test_singleton_instance(self):
        """Test singleton pattern for GDPR compliance."""
        instance1 = get_gdpr_compliance()
        instance2 = get_gdpr_compliance()
        
        self.assertIs(instance1, instance2)


class SecurityPolicyTest(TestCase):
    """Test security policy configuration."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
    
    def test_create_password_policy(self):
        """Test creating password policy."""
        policy = SecurityPolicy.objects.create(
            company=self.company,
            name="Strong Password Policy",
            policy_type='password',
            configuration={
                'min_length': 12,
                'require_uppercase': True,
                'require_special_chars': True
            }
        )
        
        self.assertEqual(policy.policy_type, 'password')
        self.assertEqual(policy.get_config('min_length'), 12)
    
    def test_get_password_policy(self):
        """Test retrieving password policy."""
        SecurityPolicy.objects.create(
            company=self.company,
            name="Password Policy",
            policy_type='password',
            is_active=True,
            configuration={'min_length': 10}
        )
        
        policy = SecurityPolicy.get_password_policy(self.company)
        self.assertIsNotNone(policy)
    
    def test_default_password_policy(self):
        """Test default password policy."""
        default = SecurityPolicy.get_default_password_policy()
        
        self.assertIn('min_length', default)
        self.assertIn('require_uppercase', default)
        self.assertIn('max_login_attempts', default)


class SecurityEventTest(TestCase):
    """Test security event logging."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
    
    def test_create_security_event(self):
        """Test creating security event."""
        event = SecurityEvent.objects.create(
            company=self.company,
            event_type='login_failure',
            severity='medium',
            user=self.user,
            ip_address='192.168.1.100',
            description='Failed login attempt'
        )
        
        self.assertEqual(event.event_type, 'login_failure')
        self.assertEqual(event.severity, 'medium')
        self.assertFalse(event.resolved)
    
    def test_log_event_helper(self):
        """Test log_event helper method."""
        event = SecurityEvent.log_event(
            event_type='unauthorized_access',
            company=self.company,
            description='Attempted to access restricted resource',
            user=self.user,
            ip_address='192.168.1.100',
            severity='high'
        )
        
        self.assertIsNotNone(event)
        self.assertEqual(event.severity, 'high')


class DataBackupTest(TestCase):
    """Test data backup tracking."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="test@company.com"
        )
    
    def test_create_backup_record(self):
        """Test creating backup record."""
        backup = DataBackup.objects.create(
            company=self.company,
            backup_type='full',
            status='pending'
        )
        
        self.assertEqual(backup.backup_type, 'full')
        self.assertEqual(backup.status, 'pending')
        self.assertTrue(backup.encrypted)
    
    def test_backup_duration(self):
        """Test backup duration calculation."""
        backup = DataBackup.objects.create(
            company=self.company,
            backup_type='full',
            status='completed',
            started_at=timezone.now(),
            completed_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        duration = backup.duration_seconds
        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0)
    
    def test_file_size_mb(self):
        """Test file size conversion to MB."""
        backup = DataBackup.objects.create(
            company=self.company,
            backup_type='full',
            status='completed',
            file_size_bytes=10485760  # 10 MB
        )
        
        self.assertEqual(backup.file_size_mb, 10.0)
