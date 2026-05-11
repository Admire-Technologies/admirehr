"""
Tests for biometric attendance system.
"""

import json
from decimal import Decimal
from datetime import datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.core.models import Company
from apps.employees.models import Employee, Department
from apps.attendance.models import AttendanceRecord
from apps.attendance.encryption import BiometricEncryption, get_biometric_encryption
from apps.attendance.face_plugin_service import FacePluginService, BiometricVerificationError
from apps.attendance.policy import AttendancePolicy, get_attendance_policy

User = get_user_model()


class BiometricEncryptionTest(TestCase):
    """Test biometric data encryption and decryption."""
    
    def setUp(self):
        self.encryption = BiometricEncryption()
        self.sample_biometric_data = {
            'face_encoding': [0.1, 0.2, 0.3, 0.4, 0.5],
            'quality_score': 0.95,
            'capture_timestamp': '2024-01-01T09:00:00Z',
            'face_descriptor': {
                'encoding_version': '1.0',
                'algorithm': 'face_plugin_sdk'
            }
        }
    
    def test_encrypt_biometric_data(self):
        """Test encryption of biometric data."""
        encrypted = self.encryption.encrypt_biometric_data(self.sample_biometric_data)
        
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, str)
        self.assertNotIn('face_encoding', encrypted)  # Should be encrypted
    
    def test_decrypt_biometric_data(self):
        """Test decryption of biometric data."""
        encrypted = self.encryption.encrypt_biometric_data(self.sample_biometric_data)
        decrypted = self.encryption.decrypt_biometric_data(encrypted)
        
        self.assertEqual(decrypted, self.sample_biometric_data)
        self.assertEqual(decrypted['face_encoding'], self.sample_biometric_data['face_encoding'])
        self.assertEqual(decrypted['quality_score'], self.sample_biometric_data['quality_score'])
    
    def test_encrypt_none_data(self):
        """Test encryption with None data."""
        encrypted = self.encryption.encrypt_biometric_data(None)
        self.assertIsNone(encrypted)
    
    def test_decrypt_none_data(self):
        """Test decryption with None data."""
        decrypted = self.encryption.decrypt_biometric_data(None)
        self.assertIsNone(decrypted)
    
    def test_hash_biometric_template(self):
        """Test hashing of biometric template."""
        hash1 = self.encryption.hash_biometric_template(self.sample_biometric_data)
        hash2 = self.encryption.hash_biometric_template(self.sample_biometric_data)
        
        self.assertIsNotNone(hash1)
        self.assertEqual(hash1, hash2)  # Same data should produce same hash
    
    def test_get_biometric_encryption_singleton(self):
        """Test singleton pattern for encryption instance."""
        instance1 = get_biometric_encryption()
        instance2 = get_biometric_encryption()
        
        self.assertIs(instance1, instance2)


class FacePluginServiceTest(TestCase):
    """Test Face Plugin SDK integration service."""
    
    def setUp(self):
        self.service = FacePluginService()
        self.sample_capture_data = {
            'face_encoding': [0.1] * 128,
            'quality_score': 0.95,
            'capture_timestamp': '2024-01-01T09:00:00Z'
        }
    
    def test_process_face_capture_success(self):
        """Test successful face capture processing."""
        processed = self.service.process_face_capture(self.sample_capture_data)
        
        self.assertIsNotNone(processed)
        self.assertIn('face_encoding', processed)
        self.assertIn('quality_score', processed)
        self.assertIn('face_descriptor', processed)
        self.assertEqual(processed['quality_score'], 0.95)
    
    def test_process_face_capture_low_quality(self):
        """Test face capture with low quality score."""
        low_quality_data = self.sample_capture_data.copy()
        low_quality_data['quality_score'] = 0.5
        
        with self.assertRaises(Exception):  # Should raise ValidationError
            self.service.process_face_capture(low_quality_data)
    
    def test_process_face_capture_missing_encoding(self):
        """Test face capture with missing encoding."""
        invalid_data = {'quality_score': 0.95}
        
        with self.assertRaises(Exception):  # Should raise ValidationError
            self.service.process_face_capture(invalid_data)
    
    def test_enroll_face(self):
        """Test face enrollment."""
        encrypted = self.service.enroll_face(self.sample_capture_data)
        
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, str)
    
    def test_verify_face_match(self):
        """Test face verification with matching faces."""
        # Enroll face
        encrypted = self.service.enroll_face(self.sample_capture_data)
        
        # Verify with same face (should match)
        processed = self.service.process_face_capture(self.sample_capture_data)
        is_match, similarity = self.service.verify_face(processed, encrypted)
        
        self.assertTrue(is_match)
        self.assertGreater(similarity, self.service.MATCH_THRESHOLD)
    
    def test_verify_face_no_match(self):
        """Test face verification with non-matching faces."""
        # Enroll face
        encrypted = self.service.enroll_face(self.sample_capture_data)
        
        # Verify with different face (use negated values for maximum difference)
        different_face = self.sample_capture_data.copy()
        different_face['face_encoding'] = [-x for x in self.sample_capture_data['face_encoding']]
        
        processed = self.service.process_face_capture(different_face)
        is_match, similarity = self.service.verify_face(processed, encrypted)
        
        self.assertFalse(is_match)
        self.assertLess(similarity, self.service.MATCH_THRESHOLD)
    
    def test_validate_biometric_data_structure(self):
        """Test biometric data structure validation."""
        # Valid data
        self.assertTrue(
            self.service.validate_biometric_data_structure(self.sample_capture_data)
        )
        
        # Invalid data - missing required field
        invalid_data = {'quality_score': 0.95}
        self.assertFalse(
            self.service.validate_biometric_data_structure(invalid_data)
        )
        
        # Invalid data - wrong type
        self.assertFalse(
            self.service.validate_biometric_data_structure("not a dict")
        )


class AttendancePolicyTest(TestCase):
    """Test attendance policy validation and enforcement."""
    
    def setUp(self):
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            grace_period_minutes=15,
            working_hours_per_day=Decimal('8.0'),
            overtime_threshold_hours=Decimal('8.0')
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Engineering',
            company=self.company
        )
        
        # Create employee
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            company=self.company,
            hire_date=timezone.now().date()
        )
        
        self.policy = AttendancePolicy(self.company)
    
    def test_validate_check_in_on_time(self):
        """Test on-time check-in validation."""
        # Check in at 9:00 AM (on time)
        check_in_time = timezone.now().replace(hour=9, minute=0, second=0)
        
        is_valid, status, message = self.policy.validate_check_in(
            self.employee,
            check_in_time
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(status, 'present')
    
    def test_validate_check_in_late(self):
        """Test late check-in validation."""
        # Check in at 9:30 AM (late, beyond grace period)
        check_in_time = timezone.now().replace(hour=9, minute=30, second=0)
        
        is_valid, status, message = self.policy.validate_check_in(
            self.employee,
            check_in_time
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(status, 'late')
    
    def test_validate_check_in_within_grace_period(self):
        """Test check-in within grace period."""
        # Check in at 9:10 AM (within 15-minute grace period)
        check_in_time = timezone.now().replace(hour=9, minute=10, second=0)
        
        is_valid, status, message = self.policy.validate_check_in(
            self.employee,
            check_in_time
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(status, 'present')
    
    def test_validate_check_in_already_checked_in(self):
        """Test validation when already checked in."""
        today = timezone.now().date()
        existing_attendance = AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now(),
            company=self.company
        )
        
        check_in_time = timezone.now()
        is_valid, status, message = self.policy.validate_check_in(
            self.employee,
            check_in_time,
            existing_attendance
        )
        
        self.assertFalse(is_valid)
    
    def test_calculate_working_hours(self):
        """Test working hours calculation."""
        check_in = timezone.now().replace(hour=9, minute=0)
        check_out = timezone.now().replace(hour=17, minute=30)
        
        working_hours = self.policy.calculate_working_hours(check_in, check_out)
        
        self.assertEqual(working_hours, Decimal('8.50'))
    
    def test_calculate_overtime(self):
        """Test overtime calculation."""
        # 10 hours worked, 8 hours threshold = 2 hours overtime
        working_hours = Decimal('10.0')
        overtime = self.policy.calculate_overtime(working_hours)
        
        self.assertEqual(overtime, Decimal('2.0'))
    
    def test_calculate_no_overtime(self):
        """Test no overtime when under threshold."""
        working_hours = Decimal('7.5')
        overtime = self.policy.calculate_overtime(working_hours)
        
        self.assertEqual(overtime, Decimal('0.0'))
    
    def test_handle_multiple_check_ins(self):
        """Test handling multiple check-in attempts."""
        today = timezone.now().date()
        existing_attendance = AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=timezone.now(),
            company=self.company
        )
        
        result = self.policy.handle_multiple_check_ins(
            existing_attendance,
            timezone.now()
        )
        
        self.assertEqual(result['action'], 'reject')
        self.assertIn('message', result)
    
    def test_get_attendance_summary(self):
        """Test attendance summary generation."""
        today = timezone.now().date()
        check_in = timezone.now().replace(hour=9, minute=0)
        check_out = timezone.now().replace(hour=17, minute=0)
        
        attendance = AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=check_in,
            check_out=check_out,
            working_hours=Decimal('8.0'),
            status='present',
            biometric_verified=True,
            company=self.company
        )
        
        summary = self.policy.get_attendance_summary(attendance)
        
        self.assertIn('date', summary)
        self.assertIn('status', summary)
        self.assertIn('working_hours', summary)
        self.assertIn('policy', summary)
        self.assertEqual(summary['status'], 'present')
        self.assertEqual(summary['working_hours'], 8.0)


class AttendanceIntegrationTest(TestCase):
    """Integration tests for complete attendance flow."""
    
    def setUp(self):
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            grace_period_minutes=15,
            working_hours_per_day=Decimal('8.0'),
            overtime_threshold_hours=Decimal('8.0')
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Engineering',
            company=self.company
        )
        
        # Create employee with biometric data
        self.face_service = FacePluginService()
        sample_biometric = {
            'face_encoding': [0.1] * 128,
            'quality_score': 0.95,
            'capture_timestamp': timezone.now().isoformat()
        }
        encrypted_biometric = self.face_service.enroll_face(sample_biometric)
        
        self.employee = Employee.objects.create(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            department=self.department,
            company=self.company,
            hire_date=timezone.now().date(),
            biometric_data=encrypted_biometric
        )
    
    def test_complete_attendance_cycle(self):
        """Test complete check-in and check-out cycle."""
        today = timezone.now().date()
        
        # Check in
        check_in_time = timezone.now().replace(hour=9, minute=0)
        attendance = AttendanceRecord.objects.create(
            employee=self.employee,
            date=today,
            check_in=check_in_time,
            status='present',
            biometric_verified=True,
            company=self.company
        )
        
        self.assertIsNotNone(attendance.check_in)
        self.assertIsNone(attendance.check_out)
        self.assertTrue(attendance.biometric_verified)
        
        # Check out
        check_out_time = timezone.now().replace(hour=17, minute=30)
        attendance.check_out = check_out_time
        
        policy = AttendancePolicy(self.company)
        attendance.working_hours = policy.calculate_working_hours(
            attendance.check_in,
            attendance.check_out
        )
        attendance.save()
        
        self.assertIsNotNone(attendance.check_out)
        self.assertEqual(attendance.working_hours, Decimal('8.50'))
    
    def test_biometric_verification_flow(self):
        """Test biometric verification in attendance flow."""
        # Capture new face
        capture_data = {
            'face_encoding': [0.1] * 128,
            'quality_score': 0.95,
            'capture_timestamp': timezone.now().isoformat()
        }
        
        # Process capture
        processed = self.face_service.process_face_capture(capture_data)
        
        # Verify against stored biometric
        is_match, similarity = self.face_service.verify_face(
            processed,
            self.employee.biometric_data
        )
        
        self.assertTrue(is_match)
        self.assertGreater(similarity, 0.6)
