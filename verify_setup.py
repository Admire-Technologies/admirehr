#!/usr/bin/env python3
"""
Verification script for Admire HRMS project structure.
This script checks if all required files and directories are in place.
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print status."""
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} (MISSING)")
        return False

def check_directory_exists(dir_path, description):
    """Check if a directory exists and print status."""
    if os.path.isdir(dir_path):
        print(f"✓ {description}: {dir_path}")
        return True
    else:
        print(f"✗ {description}: {dir_path} (MISSING)")
        return False

def main():
    """Main verification function."""
    print("Admire HRMS Project Structure Verification")
    print("=" * 50)
    
    all_good = True
    
    # Check main project files
    files_to_check = [
        ("README.md", "Main README"),
        ("SETUP.md", "Setup Guide"),
        ("docker-compose.yml", "Docker Compose Configuration"),
        (".gitignore", "Git Ignore File"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False
    
    print("\nFrontend Structure:")
    print("-" * 20)
    
    # Check frontend structure
    frontend_files = [
        ("frontend/package.json", "Frontend Package Configuration"),
        ("frontend/next.config.js", "Next.js Configuration"),
        ("frontend/tsconfig.json", "TypeScript Configuration"),
        ("frontend/tailwind.config.js", "Tailwind Configuration"),
        ("frontend/src/app/layout.tsx", "Main Layout Component"),
        ("frontend/src/app/page.tsx", "Home Page Component"),
        ("frontend/src/types/index.ts", "Type Definitions"),
        ("frontend/src/lib/api.ts", "API Client"),
        ("frontend/src/services/auth.ts", "Authentication Service"),
    ]
    
    for file_path, description in frontend_files:
        if not check_file_exists(file_path, description):
            all_good = False
    
    print("\nBackend Structure:")
    print("-" * 20)
    
    # Check backend structure
    backend_files = [
        ("backend/requirements.txt", "Python Dependencies"),
        ("backend/manage.py", "Django Management Script"),
        ("backend/admire_hrms/settings.py", "Django Settings"),
        ("backend/admire_hrms/urls.py", "Main URL Configuration"),
        ("backend/admire_hrms/wsgi.py", "WSGI Configuration"),
        ("backend/admire_hrms/asgi.py", "ASGI Configuration"),
        ("backend/admire_hrms/celery.py", "Celery Configuration"),
    ]
    
    for file_path, description in backend_files:
        if not check_file_exists(file_path, description):
            all_good = False
    
    # Check Django apps
    apps = ['core', 'authentication', 'employees', 'attendance', 'leave_management', 'payroll']
    
    for app in apps:
        print(f"\n{app.title()} App:")
        print("-" * 15)
        
        app_files = [
            (f"backend/apps/{app}/__init__.py", f"{app} App Init"),
            (f"backend/apps/{app}/models.py", f"{app} Models"),
            (f"backend/apps/{app}/views.py", f"{app} Views"),
            (f"backend/apps/{app}/apps.py", f"{app} App Config"),
            (f"backend/apps/{app}/admin.py", f"{app} Admin"),
            (f"backend/apps/{app}/migrations/__init__.py", f"{app} Migrations Init"),
        ]
        
        # Add serializers and URLs for non-core apps
        if app != 'core':
            app_files.extend([
                (f"backend/apps/{app}/serializers.py", f"{app} Serializers"),
                (f"backend/apps/{app}/urls.py", f"{app} URLs"),
            ])
        
        for file_path, description in app_files:
            if not check_file_exists(file_path, description):
                all_good = False
    
    print("\nDevelopment Scripts:")
    print("-" * 20)
    
    script_files = [
        ("backend/scripts/setup_dev.py", "Development Setup Script"),
        ("backend/scripts/run_dev.sh", "Linux Development Runner"),
        ("backend/scripts/run_dev.bat", "Windows Development Runner"),
        ("frontend/scripts/setup.sh", "Linux Frontend Setup"),
        ("frontend/scripts/setup.bat", "Windows Frontend Setup"),
    ]
    
    for file_path, description in script_files:
        if not check_file_exists(file_path, description):
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("✓ All project files are in place!")
        print("\nNext steps:")
        print("1. Run 'docker-compose up -d' to start database services")
        print("2. Set up the backend following SETUP.md")
        print("3. Set up the frontend following SETUP.md")
        return 0
    else:
        print("✗ Some files are missing. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())