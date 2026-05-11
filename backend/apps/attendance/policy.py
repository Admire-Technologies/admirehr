"""
Attendance policy validation and enforcement.

This module handles attendance policy rules such as:
- Multiple check-ins without check-out
- Late arrival detection
- Early departure detection
- Overtime calculation
- Grace period handling
"""

import logging
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.utils import timezone

logger = logging.getLogger(__name__)


class AttendancePolicy:
    """
    Handles attendance policy validation and enforcement.
    """
    
    # Default policy settings (can be overridden by company settings)
    DEFAULT_WORK_START_TIME = time(9, 0)  # 9:00 AM
    DEFAULT_WORK_END_TIME = time(17, 0)   # 5:00 PM
    DEFAULT_GRACE_PERIOD_MINUTES = 15
    DEFAULT_WORKING_HOURS_PER_DAY = Decimal('8.0')
    DEFAULT_OVERTIME_THRESHOLD = Decimal('8.0')
    
    def __init__(self, company=None):
        """
        Initialize attendance policy with company-specific settings.
        
        Args:
            company: Company instance with policy settings
        """
        self.company = company
        self._load_policy_settings()
    
    def _load_policy_settings(self):
        """Load policy settings from company or use defaults."""
        if self.company:
            self.grace_period_minutes = self.company.grace_period_minutes
            self.working_hours_per_day = self.company.working_hours_per_day
            self.overtime_threshold = self.company.overtime_threshold_hours
            
            # Load custom work hours from company settings
            settings = self.company.settings or {}
            self.work_start_time = self._parse_time(
                settings.get('work_start_time', '09:00')
            )
            self.work_end_time = self._parse_time(
                settings.get('work_end_time', '17:00')
            )
        else:
            self.grace_period_minutes = self.DEFAULT_GRACE_PERIOD_MINUTES
            self.working_hours_per_day = self.DEFAULT_WORKING_HOURS_PER_DAY
            self.overtime_threshold = self.DEFAULT_OVERTIME_THRESHOLD
            self.work_start_time = self.DEFAULT_WORK_START_TIME
            self.work_end_time = self.DEFAULT_WORK_END_TIME
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except (ValueError, AttributeError):
            return self.DEFAULT_WORK_START_TIME
    
    def validate_check_in(
        self, 
        employee, 
        check_in_time: datetime,
        existing_attendance=None
    ) -> Tuple[bool, str, str]:
        """
        Validate check-in according to attendance policies.
        
        Args:
            employee: Employee instance
            check_in_time: Check-in datetime
            existing_attendance: Existing attendance record for today (if any)
        
        Returns:
            Tuple of (is_valid: bool, status: str, message: str)
        """
        # Check if already checked in today
        if existing_attendance and existing_attendance.check_in:
            return False, 'present', 'Already checked in today'
        
        # Determine attendance status based on time
        status = self._determine_check_in_status(check_in_time)
        
        # Generate appropriate message
        if status == 'late':
            message = f'Late check-in (grace period: {self.grace_period_minutes} minutes)'
        elif status == 'present':
            message = 'On-time check-in'
        else:
            message = 'Check-in recorded'
        
        return True, status, message
    
    def validate_check_out(
        self, 
        attendance_record,
        check_out_time: datetime
    ) -> Tuple[bool, str]:
        """
        Validate check-out according to attendance policies.
        
        Args:
            attendance_record: Existing attendance record
            check_out_time: Check-out datetime
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        # Check if already checked out
        if attendance_record.check_out:
            return False, 'Already checked out today'
        
        # Check if checked in
        if not attendance_record.check_in:
            return False, 'No check-in record found'
        
        # Validate check-out is after check-in
        if check_out_time <= attendance_record.check_in:
            return False, 'Check-out time must be after check-in time'
        
        return True, 'Check-out recorded'
    
    def calculate_working_hours(
        self, 
        check_in: datetime, 
        check_out: datetime
    ) -> Decimal:
        """
        Calculate working hours between check-in and check-out.
        
        Args:
            check_in: Check-in datetime
            check_out: Check-out datetime
        
        Returns:
            Working hours as Decimal
        """
        if not check_in or not check_out:
            return Decimal('0.0')
        
        time_diff = check_out - check_in
        hours = Decimal(str(time_diff.total_seconds() / 3600))
        
        # Round to 2 decimal places
        return round(hours, 2)
    
    def calculate_overtime(self, working_hours: Decimal) -> Decimal:
        """
        Calculate overtime hours.
        
        Args:
            working_hours: Total working hours
        
        Returns:
            Overtime hours as Decimal
        """
        if working_hours > self.overtime_threshold:
            return working_hours - self.overtime_threshold
        return Decimal('0.0')
    
    def _determine_check_in_status(self, check_in_time: datetime) -> str:
        """
        Determine attendance status based on check-in time.
        
        Args:
            check_in_time: Check-in datetime
        
        Returns:
            Status string: 'present', 'late', or 'half_day'
        """
        check_in_time_only = check_in_time.time()
        
        # Calculate grace period end time
        grace_end = (
            datetime.combine(datetime.today(), self.work_start_time) +
            timedelta(minutes=self.grace_period_minutes)
        ).time()
        
        # Check if within grace period
        if check_in_time_only <= grace_end:
            return 'present'
        
        # Check if significantly late (more than 2 hours)
        late_threshold = (
            datetime.combine(datetime.today(), self.work_start_time) +
            timedelta(hours=2)
        ).time()
        
        if check_in_time_only > late_threshold:
            return 'half_day'
        
        return 'late'
    
    def handle_multiple_check_ins(
        self, 
        existing_attendance,
        new_check_in_time: datetime
    ) -> Dict:
        """
        Handle scenario where employee tries to check in multiple times.
        
        Args:
            existing_attendance: Existing attendance record
            new_check_in_time: New check-in attempt time
        
        Returns:
            Dictionary with action and message
        """
        if not existing_attendance.check_out:
            # Already checked in, not checked out yet
            return {
                'action': 'reject',
                'message': 'Already checked in. Please check out first.',
                'existing_check_in': existing_attendance.check_in.isoformat()
            }
        else:
            # Already completed a full cycle
            return {
                'action': 'reject',
                'message': 'Attendance already recorded for today.',
                'check_in': existing_attendance.check_in.isoformat(),
                'check_out': existing_attendance.check_out.isoformat()
            }
    
    def get_attendance_summary(self, attendance_record) -> Dict:
        """
        Get summary of attendance record with policy-based calculations.
        
        Args:
            attendance_record: AttendanceRecord instance
        
        Returns:
            Dictionary with attendance summary
        """
        summary = {
            'date': attendance_record.date.isoformat(),
            'status': attendance_record.status,
            'check_in': attendance_record.check_in.isoformat() if attendance_record.check_in else None,
            'check_out': attendance_record.check_out.isoformat() if attendance_record.check_out else None,
            'working_hours': float(attendance_record.working_hours) if attendance_record.working_hours else 0,
            'biometric_verified': attendance_record.biometric_verified,
        }
        
        # Calculate overtime if applicable
        if attendance_record.working_hours:
            overtime = self.calculate_overtime(attendance_record.working_hours)
            summary['overtime_hours'] = float(overtime)
        
        # Add policy information
        summary['policy'] = {
            'expected_hours': float(self.working_hours_per_day),
            'grace_period_minutes': self.grace_period_minutes,
            'work_start_time': self.work_start_time.strftime('%H:%M'),
            'work_end_time': self.work_end_time.strftime('%H:%M'),
        }
        
        return summary


def get_attendance_policy(company=None) -> AttendancePolicy:
    """
    Get AttendancePolicy instance for a company.
    
    Args:
        company: Company instance
    
    Returns:
        AttendancePolicy instance
    """
    return AttendancePolicy(company)
