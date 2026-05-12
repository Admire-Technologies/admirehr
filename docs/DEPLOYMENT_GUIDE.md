# Admire HRMS Deployment Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [Database Configuration](#database-configuration)
5. [Application Deployment](#application-deployment)
6. [WebSocket Configuration](#websocket-configuration)
7. [Background Jobs Setup](#background-jobs-setup)
8. [Security Configuration](#security-configuration)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Backup and Recovery](#backup-and-recovery)
11. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

**Backend Server**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: 100 GB SSD
- OS: Ubuntu 20.04 LTS or later

**Database Server**:
- CPU: 4 cores
- RAM: 16 GB
- Storage: 200 GB SSD (with RAID for redundancy)

**Redis Server**:
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB SSD

### Recommended Requirements (Production)

**Backend Server**:
- CPU: 8 cores
- RAM: 16 GB
- Storage: 200 GB SSD

**Database Server**:
- CPU: 8 cores
- RAM: 32 GB
- Storage: 500 GB SSD with RAID 10

**Redis Server**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD

### Software Requirements

- Python 3.10 or later
- PostgreSQL 14 or later
- Redis 6.2 or later
- Node.js 18 or later (for frontend)
- Nginx 1.20 or later
- Docker and Docker Compose (optional but recommended)

## Pre-Deployment Checklist

- [ ] Domain name configured and DNS records set
- [ ] SSL/TLS certificates obtained
- [ ] Database server provisioned and secured
- [ ] Redis server provisioned
- [ ] Backup storage configured
- [ ] Email service configured (SMTP)
- [ ] Monitoring tools set up
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Documentation reviewed

## Environment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.10 python3.10-venv python3-pip \
    postgresql-client redis-tools nginx git curl

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Application User Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash admire
sudo usermod -aG sudo admire

# Switch to application user
sudo su - admire
```

### 3. Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/admire-hrms.git
cd admire-hrms

# Checkout production branch
git checkout production
```

## Database Configuration

### 1. PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE admire_hrms;
CREATE USER admire_user WITH PASSWORD 'secure_password_here';
ALTER ROLE admire_user SET client_encoding TO 'utf8';
ALTER ROLE admire_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE admire_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE admire_hrms TO admire_user;
\q
EOF
```

### 2. Database Optimization

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Memory Configuration
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB

# Connection Configuration
max_connections = 200

# Query Optimization
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200

# Write Ahead Log
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Logging
log_min_duration_statement = 1000  # Log slow queries (>1s)
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 3. Database Indexes

Run migrations to create optimized indexes:

```bash
python manage.py migrate
python manage.py create_indexes  # Custom management command
```

## Application Deployment

### Option 1: Docker Deployment (Recommended)

#### 1. Configure Environment Variables

Create `.env.production`:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://admire_user:password@db:5432/admire_hrms

# Redis
REDIS_URL=redis://redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 2. Build and Deploy

```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py collectstatic --noinput

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Manual Deployment

#### 1. Python Environment Setup

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

#### 2. Configure Environment

Create `.env` file with production settings (same as above).

#### 3. Run Migrations

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

#### 4. Gunicorn Configuration

Create `/etc/systemd/system/admire-hrms.service`:

```ini
[Unit]
Description=Admire HRMS Gunicorn Service
After=network.target

[Service]
User=admire
Group=www-data
WorkingDirectory=/home/admire/admire-hrms/backend
Environment="PATH=/home/admire/admire-hrms/venv/bin"
ExecStart=/home/admire/admire-hrms/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/admire-hrms.sock \
    --timeout 120 \
    --access-logfile /var/log/admire-hrms/access.log \
    --error-logfile /var/log/admire-hrms/error.log \
    admire_hrms.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl start admire-hrms
sudo systemctl enable admire-hrms
```

## WebSocket Configuration

### 1. Daphne Service (ASGI Server)

Create `/etc/systemd/system/admire-hrms-ws.service`:

```ini
[Unit]
Description=Admire HRMS WebSocket Service
After=network.target

[Service]
User=admire
Group=www-data
WorkingDirectory=/home/admire/admire-hrms/backend
Environment="PATH=/home/admire/admire-hrms/venv/bin"
ExecStart=/home/admire/admire-hrms/venv/bin/daphne \
    -b 0.0.0.0 \
    -p 8001 \
    admire_hrms.asgi:application

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl start admire-hrms-ws
sudo systemctl enable admire-hrms-ws
```

### 2. Nginx WebSocket Configuration

Add to Nginx configuration:

```nginx
upstream websocket {
    server 127.0.0.1:8001;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # WebSocket location
    location /ws/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## Background Jobs Setup

### 1. Celery Worker Service

Create `/etc/systemd/system/admire-hrms-celery.service`:

```ini
[Unit]
Description=Admire HRMS Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=admire
Group=www-data
WorkingDirectory=/home/admire/admire-hrms/backend
Environment="PATH=/home/admire/admire-hrms/venv/bin"
ExecStart=/home/admire/admire-hrms/venv/bin/celery -A admire_hrms worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/var/log/admire-hrms/celery-worker.log

[Install]
WantedBy=multi-user.target
```

### 2. Celery Beat Service (Scheduler)

Create `/etc/systemd/system/admire-hrms-celery-beat.service`:

```ini
[Unit]
Description=Admire HRMS Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=admire
Group=www-data
WorkingDirectory=/home/admire/admire-hrms/backend
Environment="PATH=/home/admire/admire-hrms/venv/bin"
ExecStart=/home/admire/admire-hrms/venv/bin/celery -A admire_hrms beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --logfile=/var/log/admire-hrms/celery-beat.log

[Install]
WantedBy=multi-user.target
```

Start services:

```bash
sudo systemctl start admire-hrms-celery
sudo systemctl enable admire-hrms-celery
sudo systemctl start admire-hrms-celery-beat
sudo systemctl enable admire-hrms-celery-beat
```

## Security Configuration

### 1. Firewall Setup

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (only from application server)
sudo ufw allow from <app-server-ip> to any port 5432

# Check status
sudo ufw status
```

### 2. SSL/TLS Configuration

Using Let's Encrypt:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 3. Nginx Security Headers

Add to Nginx configuration:

```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

## Monitoring and Logging

### 1. Application Logging

Configure log rotation in `/etc/logrotate.d/admire-hrms`:

```
/var/log/admire-hrms/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 admire www-data
    sharedscripts
    postrotate
        systemctl reload admire-hrms
    endscript
}
```

### 2. System Monitoring

Install monitoring tools:

```bash
# Install Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.5.0.linux-amd64.tar.gz
sudo mv node_exporter-1.5.0.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter
```

Create systemd service for Node Exporter.

### 3. Application Health Checks

Set up health check endpoint monitoring:

```bash
# Add to crontab
*/5 * * * * curl -f http://localhost:8000/api/v1/health/ || echo "Health check failed" | mail -s "HRMS Health Alert" admin@yourdomain.com
```

## Backup and Recovery

### 1. Database Backup

Create backup script `/home/admire/scripts/backup-db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="admire_hrms_$DATE.sql.gz"

# Create backup
pg_dump -h localhost -U admire_user admire_hrms | gzip > "$BACKUP_DIR/$FILENAME"

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp "$BACKUP_DIR/$FILENAME" s3://your-bucket/backups/
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /home/admire/scripts/backup-db.sh
```

### 2. Media Files Backup

```bash
#!/bin/bash

MEDIA_DIR="/home/admire/admire-hrms/backend/media"
BACKUP_DIR="/backups/media"
DATE=$(date +%Y%m%d)

# Create backup
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C "$MEDIA_DIR" .

# Keep only last 7 days
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete
```

### 3. Recovery Procedure

```bash
# Restore database
gunzip < backup_file.sql.gz | psql -h localhost -U admire_user admire_hrms

# Restore media files
tar -xzf media_backup.tar.gz -C /home/admire/admire-hrms/backend/media/

# Restart services
sudo systemctl restart admire-hrms
sudo systemctl restart admire-hrms-ws
sudo systemctl restart admire-hrms-celery
```

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check service status
sudo systemctl status admire-hrms

# Check logs
sudo journalctl -u admire-hrms -n 50

# Check application logs
tail -f /var/log/admire-hrms/error.log
```

**Database connection issues**:
```bash
# Test database connection
psql -h localhost -U admire_user -d admire_hrms

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

**WebSocket not connecting**:
```bash
# Check Daphne service
sudo systemctl status admire-hrms-ws

# Test WebSocket connection
wscat -c ws://localhost:8001/ws/
```

**High memory usage**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Restart services if needed
sudo systemctl restart admire-hrms
```

### Performance Tuning

**Database query optimization**:
```bash
# Enable query logging
# Edit postgresql.conf
log_min_duration_statement = 100

# Analyze slow queries
sudo tail -f /var/log/postgresql/postgresql-14-main.log | grep "duration:"
```

**Redis optimization**:
```bash
# Check Redis memory usage
redis-cli info memory

# Set max memory
redis-cli config set maxmemory 2gb
redis-cli config set maxmemory-policy allkeys-lru
```

## Maintenance

### Regular Tasks

**Weekly**:
- Review application logs
- Check disk space
- Monitor database size
- Review security logs

**Monthly**:
- Update system packages
- Review and optimize database
- Test backup restoration
- Security audit

**Quarterly**:
- Update application dependencies
- Performance testing
- Disaster recovery drill
- Documentation review

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Support**: devops@admire-hrms.com
