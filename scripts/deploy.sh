#!/bin/bash
# Production deployment script for Admire HRMS

set -e  # Exit on error

echo "=== Admire HRMS Deployment Script ==="
echo ""

# Configuration
BACKUP_DIR="/opt/admire-hrms/backups"
DEPLOY_DIR="/opt/admire-hrms"
LOG_FILE="/opt/admire-hrms/logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root or with sudo"
    exit 1
fi

# Change to deployment directory
cd "$DEPLOY_DIR" || exit 1

# Step 1: Pre-deployment checks
log "Step 1: Running pre-deployment checks..."

# Check if .env file exists
if [ ! -f .env ]; then
    error ".env file not found. Please create it from .env.example"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    error "docker-compose is not installed"
    exit 1
fi

# Check disk space (require at least 5GB free)
FREE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$FREE_SPACE" -lt 5 ]; then
    error "Insufficient disk space. At least 5GB required, only ${FREE_SPACE}GB available"
    exit 1
fi

log "Pre-deployment checks passed"

# Step 2: Create backup
log "Step 2: Creating database backup..."

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Create backup using Django management command
docker-compose exec -T backend python manage.py create_backup --all --type=full --output-dir=/backups || {
    error "Backup creation failed"
    exit 1
}

BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.backup.gz 2>/dev/null | head -1)
if [ -n "$BACKUP_FILE" ]; then
    log "Backup created: $BACKUP_FILE"
else
    warning "No backup file found, but continuing deployment"
fi

# Step 3: Pull latest images
log "Step 3: Pulling latest Docker images..."
docker-compose pull || {
    error "Failed to pull Docker images"
    exit 1
}

# Step 4: Stop services gracefully
log "Step 4: Stopping services gracefully..."

# Give Celery workers time to finish current tasks
docker-compose exec -T celery_worker celery -A admire_hrms control shutdown || true
sleep 10

# Stop all services
docker-compose down || {
    error "Failed to stop services"
    exit 1
}

# Step 5: Start services
log "Step 5: Starting services..."
docker-compose up -d || {
    error "Failed to start services"
    exit 1
}

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 30

# Step 6: Run database migrations
log "Step 6: Running database migrations..."
docker-compose exec -T backend python manage.py migrate --noinput || {
    error "Database migration failed"
    log "Attempting to restore from backup..."
    
    if [ -n "$BACKUP_FILE" ]; then
        docker-compose exec -T backend python manage.py restore_backup --file="$BACKUP_FILE" --force
        error "Deployment failed. System restored from backup."
    else
        error "Deployment failed and no backup available for restore"
    fi
    exit 1
}

# Step 7: Collect static files
log "Step 7: Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput || {
    warning "Static file collection failed, but continuing"
}

# Step 8: Create default permissions
log "Step 8: Creating default permissions..."
docker-compose exec -T backend python manage.py create_default_permissions || {
    warning "Permission creation failed, but continuing"
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

# Check Nginx health
NGINX_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")
if [ "$NGINX_HEALTH" != "200" ]; then
    error "Nginx health check failed (HTTP $NGINX_HEALTH)"
    exit 1
fi
log "Nginx health check passed"

# Step 10: Cleanup old images
log "Step 10: Cleaning up old Docker images..."
docker image prune -f || true

# Step 11: Cleanup old backups (keep last 30 days)
log "Step 11: Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.backup.gz" -mtime +30 -delete || true

log ""
log "=== Deployment completed successfully ==="
log "Deployment time: $(date)"
log ""

# Display service status
log "Service status:"
docker-compose ps

exit 0
