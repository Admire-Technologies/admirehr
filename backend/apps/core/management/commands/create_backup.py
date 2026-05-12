"""
Management command to create encrypted database backups.

Usage:
    python manage.py create_backup --company=<company_code> --type=full
    python manage.py create_backup --all --type=incremental
"""

import os
import json
import gzip
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.apps import apps
from django.utils import timezone
from apps.core.models import Company, DataBackup
from apps.core.encryption import get_data_encryption


class Command(BaseCommand):
    help = 'Create encrypted database backup for company data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Company code to backup'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Backup all companies'
        )
        parser.add_argument(
            '--type',
            type=str,
            default='full',
            choices=['full', 'incremental', 'differential'],
            help='Backup type'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Output directory for backups'
        )
    
    def handle(self, *args, **options):
        company_code = options.get('company')
        backup_all = options.get('all')
        backup_type = options.get('type')
        output_dir = options.get('output_dir')
        
        # Validate arguments
        if not company_code and not backup_all:
            raise CommandError('Either --company or --all must be specified')
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get companies to backup
        if backup_all:
            companies = Company.objects.filter(is_active=True)
        else:
            try:
                companies = [Company.objects.get(code=company_code)]
            except Company.DoesNotExist:
                raise CommandError(f'Company with code "{company_code}" not found')
        
        # Backup each company
        for company in companies:
            self.stdout.write(f'Starting {backup_type} backup for {company.name}...')
            try:
                self.create_company_backup(company, backup_type, output_dir)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully backed up {company.name}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to backup {company.name}: {str(e)}')
                )
    
    def create_company_backup(self, company, backup_type, output_dir):
        """Create backup for a single company."""
        # Create backup record
        backup = DataBackup.objects.create(
            company=company,
            backup_type=backup_type,
            status='in_progress',
            started_at=timezone.now()
        )
        
        try:
            # Get all models to backup
            models_to_backup = self.get_models_to_backup()
            
            # Collect data
            backup_data = {
                'company': company.code,
                'backup_type': backup_type,
                'timestamp': timezone.now().isoformat(),
                'data': {}
            }
            
            tables_backed_up = []
            record_counts = {}
            
            for model in models_to_backup:
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                
                # Filter by company if model has company field
                if hasattr(model, 'company'):
                    queryset = model.objects.filter(company=company)
                else:
                    # For models without company field, backup all
                    queryset = model.objects.all()
                
                # Serialize data
                data = serializers.serialize('json', queryset)
                backup_data['data'][model_name] = json.loads(data)
                
                tables_backed_up.append(model_name)
                record_counts[model_name] = queryset.count()
            
            # Convert to JSON
            json_data = json.dumps(backup_data, indent=2)
            
            # Encrypt data
            encryption = get_data_encryption()
            encrypted_data = encryption.encrypt(json_data)
            
            # Compress
            compressed_data = gzip.compress(encrypted_data.encode('utf-8'))
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{company.code}_{backup_type}_{timestamp}.backup.gz"
            file_path = os.path.join(output_dir, filename)
            
            # Write to file
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
            
            # Update backup record
            backup.status = 'completed'
            backup.completed_at = timezone.now()
            backup.file_path = file_path
            backup.file_size_bytes = os.path.getsize(file_path)
            backup.tables_backed_up = tables_backed_up
            backup.record_counts = record_counts
            backup.expires_at = timezone.now() + timedelta(days=90)
            backup.save()
            
            self.stdout.write(
                f'  - Backed up {len(tables_backed_up)} tables '
                f'({sum(record_counts.values())} records)'
            )
            self.stdout.write(f'  - File: {file_path} ({backup.file_size_mb} MB)')
        
        except Exception as e:
            backup.status = 'failed'
            backup.error_message = str(e)
            backup.completed_at = timezone.now()
            backup.save()
            raise
    
    def get_models_to_backup(self):
        """Get list of models to include in backup."""
        # Include all models from our apps
        app_labels = [
            'authentication',
            'employees',
            'attendance',
            'leave_management',
            'payroll',
            'dashboard',
            'core',
        ]
        
        models = []
        for app_label in app_labels:
            try:
                app_config = apps.get_app_config(app_label)
                models.extend(app_config.get_models())
            except LookupError:
                pass
        
        return models
