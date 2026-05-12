#!/bin/bash
# Disaster recovery script for Admire HRMS

set -e

echo "=== Admire HRMS Restore Script ==="
echo ""
echo "WARNING: This will restore the system from a backup."
echo "All current data will be replaced with backup data."
echo ""

# Configuration
BACKUP_DIR="/opt/admire-hrms/backups"
DEPLOY_DIR="/opt/admire-hrms"
LOG_FILE="/opt/admire-hrms/logs/restore.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root or with sudo"
    exit 1
fi

# Parse arguments
BACKUP_FILE=""
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Usage: $0 --file <backup_file> [--force]"
            exit 1
            ;;
    esac
done

# If no backup file specified, list available backups
if [ -z "$BACKUP_FILE" ]; then
    echo "Available backups:"
    ls -lht "$BACKUP_DIR"/*.backup.gz 2>/dev/null | head -10
    echo ""
    echo "Usage: $0 --file <backup_file> [--force]"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Confirm restore
if [ "$FORCE" != true ]; then
    echo -e "${YELLOW}Are you sure you want to restore from: $BACKUP_FILE?${NC}"
    echo "This will replace all current data. Type 'yes' to continue:"
    read -r CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Restore cancelled"
        exit 0
    fi
fi

cd "$DEPLOY_DIR" || exit 1

# Step 1: Create safety backup of current state
log "Step 1: Creating safety backup of current state..."
./scripts/backup.sh || warning "Safety backup failed, but continuing"

# Step 2: Stop services
log "Step 2: Stopping services..."
docker-compose down || {
    error "Failed to stop services"
    exit 1
}

# Step 3: Restore database
log "Step 3: Restoring database from backup..."

# Start only database service
docker-compose up -d db redis
sleep 10

# Restore using Django management command
docker-compose run --rm backend python manage.py restore_backup --file="$BACKUP_FILE" --force || {
    error "Database restore failed"
    exit 1
}

# Step 4: Restore media files (if available)
log "Step 4: Restoring media files..."
BACKUP_TIMESTAMP=$(basename "$BACKUP_FILE" | grep -oP '\d{8}_\d{6}')
MEDIA_BACKUP="$BACKUP_DIR/media_${BACKUP_TIMESTAMP}.tar.gz"

if [ -f "$MEDIA_BACKUP" ]; then
    tar -xzf "$MEDIA_BACKUP" -C . || {
        warning "Media restore failed, but continuing"
    }
    log "Media files restored"
else
    warning "No media backup found for this timestamp"
fi

# Step 5: Restore configuration (if available)
log "Step 5: Checking configuration backup..."
CONFIG_BACKUP="$BACKUP_DIR/config_${BACKUP_TIMESTAMP}.tar.gz"

if [ -f "$CONFIG_BACKUP" ]; then
    warning "Configuration backup found: $CONFIG_BACKUP"
    warning "Review and manually restore if needed"
fi

# Step 6: Start all services
log "Step 6: Starting all services..."
docker-compose up -d || {
    error "Failed to start services"
    exit 1
}

# Wait for services
log "Waiting for services to be ready..."
sleep 30

# Step 7: Run migrations (in case of version differences)
log "Step 7: Running database migrations..."
docker-compose exec -T backend python manage.py migrate --noinput || {
    warning "Migration failed, but continuing"
}

# Step 8: Collect static files
log "Step 8: Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput || {
    warning "Static file collection failed, but continuing"
}

# Step 9: Health checks
log "Step 9: Running health checks..."

# Check backend health
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/health/ || echo "000")
if [ "$BACKEND_HEALTH" != "200" ]; then
    error "Backend health check failed (HTTP $BACKEND_HEALTH)"
    exit 1
fi
log "Backend health check passed"

# Check frontend health
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health || echo "000")
if [ "$FRONTEND_HEALTH" != "200" ]; then
    warning "Frontend health check failed (HTTP $FRONTEND_HEALTH)"
else
    log "Frontend health check passed"
fi

log ""
log "=== Restore completed successfully ==="
log "Restored from: $BACKUP_FILE"
log "Restore time: $(date)"
log ""

# Display service status
log "Service status:"
docker-compose ps

exit 0
