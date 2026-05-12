#!/bin/bash
# Automated backup script for Admire HRMS

set -e

echo "=== Admire HRMS Backup Script ==="

# Configuration
BACKUP_DIR="/opt/admire-hrms/backups"
DEPLOY_DIR="/opt/admire-hrms"
RETENTION_DAYS=30
LOG_FILE="/opt/admire-hrms/logs/backup.log"

# Remote backup configuration (optional)
REMOTE_BACKUP_ENABLED=${REMOTE_BACKUP_ENABLED:-false}
REMOTE_BACKUP_HOST=${REMOTE_BACKUP_HOST:-""}
REMOTE_BACKUP_USER=${REMOTE_BACKUP_USER:-""}
REMOTE_BACKUP_PATH=${REMOTE_BACKUP_PATH:-""}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Change to deployment directory
cd "$DEPLOY_DIR" || exit 1

# Create timestamp
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')

# Step 1: Create database backup
log "Creating database backup..."
docker-compose exec -T backend python manage.py create_backup --all --type=full --output-dir=/backups || {
    error "Database backup failed"
    exit 1
}

# Step 2: Backup PostgreSQL directly (additional safety)
log "Creating PostgreSQL dump..."
docker-compose exec -T db pg_dumpall -U postgres | gzip > "$BACKUP_DIR/postgres_dump_${TIMESTAMP}.sql.gz" || {
    error "PostgreSQL dump failed"
    exit 1
}

# Step 3: Backup media files
log "Backing up media files..."
if [ -d "backend/media" ]; then
    tar -czf "$BACKUP_DIR/media_${TIMESTAMP}.tar.gz" backend/media/ || {
        error "Media backup failed"
        exit 1
    }
fi

# Step 4: Backup configuration files
log "Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_${TIMESTAMP}.tar.gz" \
    .env \
    docker-compose.yml \
    nginx/nginx.conf \
    backend/admire_hrms/settings.py 2>/dev/null || {
    error "Configuration backup failed"
    exit 1
}

# Step 5: Create backup manifest
log "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_${TIMESTAMP}.txt" << EOF
Backup Date: $(date)
Backup Type: Full System Backup
Database Backups: $(ls -lh "$BACKUP_DIR"/*_${TIMESTAMP}.backup.gz 2>/dev/null | wc -l)
PostgreSQL Dump: postgres_dump_${TIMESTAMP}.sql.gz
Media Backup: media_${TIMESTAMP}.tar.gz
Config Backup: config_${TIMESTAMP}.tar.gz
Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF

# Step 6: Verify backups
log "Verifying backups..."
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*${TIMESTAMP}* 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -lt 3 ]; then
    error "Backup verification failed. Expected at least 3 files, found $BACKUP_COUNT"
    exit 1
fi

log "Backup verification passed ($BACKUP_COUNT files created)"

# Step 7: Copy to remote location (if enabled)
if [ "$REMOTE_BACKUP_ENABLED" = "true" ] && [ -n "$REMOTE_BACKUP_HOST" ]; then
    log "Copying backups to remote location..."
    rsync -avz --progress "$BACKUP_DIR/"*${TIMESTAMP}* \
        "${REMOTE_BACKUP_USER}@${REMOTE_BACKUP_HOST}:${REMOTE_BACKUP_PATH}/" || {
        error "Remote backup copy failed"
    }
    log "Remote backup completed"
fi

# Step 8: Cleanup old backups
log "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.backup.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "manifest_*.txt" -mtime +$RETENTION_DAYS -delete

# Step 9: Report backup status
log ""
log "=== Backup completed successfully ==="
log "Backup location: $BACKUP_DIR"
log "Backup files:"
ls -lh "$BACKUP_DIR"/*${TIMESTAMP}* | tee -a "$LOG_FILE"
log ""
log "Total backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
log "Available disk space: $(df -h "$BACKUP_DIR" | tail -1 | awk '{print $4}')"

exit 0
