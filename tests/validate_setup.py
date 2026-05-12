#!/usr/bin/env python3
"""
Test Infrastructure Validation Script

This script validates that all required components for the test suite are properly set up.
"""

import sys
import subprocess
import os
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")


def print_warning(text):
    print(f"{Colors.YELLOW}!{Colors.END} {text}")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (3.11+ required)")
        return False


def check_command(command, name):
    """Check if a command is available"""
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print_success(f"{name}: {version}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print_error(f"{name} not found")
    return False


def check_service(host, port, name):
    """Check if a service is running"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print_success(f"{name} is running on {host}:{port}")
            return True
        else:
            print_error(f"{name} is not running on {host}:{port}")
            return False
    except Exception as e:
        print_error(f"{name} check failed: {e}")
        return False


def check_file(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False


def check_directory(dirpath, description):
    """Check if a directory exists"""
    if Path(dirpath).is_dir():
        print_success(f"{description}: {dirpath}")
        return True
    else:
        print_error(f"{description} not found: {dirpath}")
        return False


def check_python_package(package, name=None):
    """Check if a Python package is installed"""
    if name is None:
        name = package
    try:
        __import__(package)
        print_success(f"{name} package installed")
        return True
    except ImportError:
        print_error(f"{name} package not installed")
        return False


def main():
    print_header("Test Infrastructure Validation")
    
    all_checks = []
    
    # Check Python version
    print_header("Python Environment")
    all_checks.append(check_python_version())
    
    # Check required commands
    print_header("Required Commands")
    all_checks.append(check_command('node', 'Node.js'))
    all_checks.append(check_command('npm', 'npm'))
    all_checks.append(check_command('pytest', 'pytest'))
    
    # Check optional commands
    print("\nOptional Commands:")
    check_command('docker', 'Docker')
    check_command('locust', 'Locust')
    
    # Check required services
    print_header("Required Services")
    all_checks.append(check_service('localhost', 5432, 'PostgreSQL'))
    all_checks.append(check_service('localhost', 6379, 'Redis'))
    
    # Check optional services
    print("\nOptional Services:")
    check_service('localhost', 8000, 'Backend Server')
    check_service('localhost', 3000, 'Frontend Server')
    
    # Check test files
    print_header("Test Files")
    all_checks.append(check_file('tests/e2e/test_user_workflows.py', 'E2E tests'))
    all_checks.append(check_file('tests/performance/test_performance.py', 'Performance tests'))
    all_checks.append(check_file('tests/security/test_security.py', 'Security tests'))
    all_checks.append(check_file('tests/load/test_load.py', 'Load tests'))
    all_checks.append(check_file('tests/integration/test_third_party_integrations.py', 'Integration tests'))
    
    # Check configuration files
    print_header("Configuration Files")
    all_checks.append(check_file('.github/workflows/test-pipeline.yml', 'CI/CD pipeline'))
    all_checks.append(check_file('tests/requirements.txt', 'Test requirements'))
    all_checks.append(check_file('frontend/playwright.config.ts', 'Playwright config'))
    all_checks.append(check_file('frontend/jest.config.js', 'Jest config'))
    
    # Check directories
    print_header("Directory Structure")
    all_checks.append(check_directory('tests/e2e', 'E2E tests directory'))
    all_checks.append(check_directory('tests/performance', 'Performance tests directory'))
    all_checks.append(check_directory('tests/security', 'Security tests directory'))
    all_checks.append(check_directory('tests/load', 'Load tests directory'))
    all_checks.append(check_directory('tests/integration', 'Integration tests directory'))
    all_checks.append(check_directory('backend', 'Backend directory'))
    all_checks.append(check_directory('frontend', 'Frontend directory'))
    
    # Check Python packages
    print_header("Python Packages")
    all_checks.append(check_python_package('pytest', 'pytest'))
    all_checks.append(check_python_package('requests', 'requests'))
    check_python_package('locust', 'locust')  # Optional
    check_python_package('redis', 'redis')
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\nChecks passed: {passed}/{total} ({percentage:.1f}%)\n")
    
    if passed == total:
        print_success("All required components are properly set up!")
        print("\nYou can now run the test suite:")
        print("  ./tests/run_all_tests.sh  (Unix/Linux/Mac)")
        print("  tests\\run_all_tests.bat  (Windows)")
        return 0
    else:
        print_error("Some required components are missing.")
        print("\nPlease install missing components and run this script again.")
        print("\nQuick setup:")
        print("  pip install -r tests/requirements.txt")
        print("  cd frontend && npm install")
        print("  createdb admire_hrms_test")
        print("  redis-server")
        return 1


if __name__ == '__main__':
    sys.exit(main())
