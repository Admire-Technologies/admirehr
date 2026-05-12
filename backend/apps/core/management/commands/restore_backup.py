"""
Management command to restore from encrypted database backups.

Usage:
    python manage.py restore_backup --file=<backup_file_path>
    python manage.py restore_backup --backup-id=<backup_uuid>
"""

import os
import json
import gzip
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db import transaction
from apps.core.models import DataBackup
from apps.core.encryption import get_data_encryption


class Command(BaseCommand):
    help = 'Restore database from encrypted backup'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to backup file'
        )
        parser.add_argument(
            '--backup-id',
            type=str,
            help='Backup record ID to restore from'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate backup without restoring'
        )
    
    def handle(self, *args, **options):
        file_path = options.get('file')
        backup_id = options.get('backup_id')
        dry_run = options.get('dry_run')
        
        # Validate arguments
        if not file_path and not backup_id:
            raise CommandError('Either --file or --backup-id must be specified')
        
        # Get file path
        if backup_id:
            try:
                backup = DataBackup.objects.get(id=backup_id)
                file_path = backup.file_path
            except DataBackup.DoesNotExist:
                raise CommandError(f'Backup with ID "{backup_id}" not found')
        
        if not os.path.exists(file_path):
            raise CommandError(f'Backup file not found: {file_path}')
        
        self.stdout.write(f'Restoring from: {file_path}')
        
        try:
            # Read and decrypt backup
            backup_data = self.read_backup_file(file_path)
            
            self.stdout.write(
                f'Backup info:'
                f'\n  - Company: {backup_data["company"]}'
                f'\n  - Type: {backup_data["backup_type"]}'
                f'\n  - Timestamp: {backup_data["timestamp"]}'
                f'\n  - Tables: {len(backup_data["data"])}'
            )
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS('Dry run completed successfully'))
                return
            
            # Confirm restore
            confirm = input('Are you sure you want to restore? This will overwrite existing data. (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Restore cancelled')
                return
            
            # Restore data
            self.restore_data(backup_data)
            
            self.stdout.write(self.style.SUCCESS('Restore completed successfully'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Restore failed: {str(e)}'))
            raise
    
    def read_backup_file(self, file_path):
        """Read and decrypt backup file."""
        self.stdout.write('Reading backup file...')
        
        # Read compressed file
        with open(file_path, 'rb') as f:
            compressed_data = f.read()
        
        # Decompress
        encrypted_data = gzip.decompress(compressed_data).decode('utf-8')
        
        # Decrypt
        encryption = get_data_encryption()
        json_data = encryption.decrypt(encrypted_data)
        
        # Parse JSON
        if isinstance(json_data, str):
            backup_data = json.loads(json_data)
        else:
            backup_data = json_data
        
        return backup_data
    
    @transaction.atomic
    def restore_data(self, backup_data):
        """Restore data from backup."""
        self.stdout.write('Restoring data...')
        
        total_restored = 0
        
        for model_name, objects_data in backup_data['data'].items():
            self.stdout.write(f'  - Restoring {model_name}...')
            
            try:
                # Deserialize and save objects
                for obj in serializers.deserialize('json', json.dumps(objects_data)):
                    obj.save()
                    total_restored += 1
                
                self.stdout.write(f'    Restored {len(objects_data)} records')
            
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'    Failed to restore {model_name}: {str(e)}')
                )
        
        self.stdout.write(f'Total records restored: {total_restored}')
