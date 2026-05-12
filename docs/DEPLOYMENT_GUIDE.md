# Admire HRMS Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying Admire HRMS to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Production Deployment](#production-deployment)
4. [Post-Deployment](#post-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 100 GB SSD
- OS: Ubuntu 20.04 LTS or later

**Recommended Requirements**:
- CPU: 8 cores
- RAM: 16 GB
- Disk: 250 GB SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Git
- SSL Certificate (for HTTPS)

### Network Requirements

- Open ports: 80 (HTTP), 443 (HTTPS)
- Outbound internet access for Docker images
- SMTP server for email notifications

## Initial Setup

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Clone Repository

```bash
# Create deployment directory
sudo mkdir -p /opt/admire-hrms
cd /opt/admire-hrms

# Clone repository
git clone https://github.com/your-org/admire-hrms.git .

# Or download release
wget https://github.com/your-org/admire-hrms/archive/v1.0.0.tar.gz
tar -xzf v1.0.0.tar.gz
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables**:

```bash
# Django Settings
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
POSTGRES_DB=admire_hrms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-database-password

# Redis
REDIS_URL=redis://redis:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Frontend
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws

# Backup
BACKUP_ENCRYPTION_KEY=your-backup-encryption-key
BACKUP_RETENTION_DAYS=30
```

### 4. Generate Secret Keys

```bash
# Generate Django secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate backup encryption key
openssl rand -base64 32
```

### 5. Set Up SSL Certificate

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

**Option B: Custom Certificate**

Place your SSL certificate files:
- Certificate: `/opt/admire-hrms/ssl/cert.pem`
- Private Key: `/opt/admire-hrms/ssl/key.pem`

### 6. Update Nginx Configuration

Edit `nginx/nginx.conf` to add SSL:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... rest of configuration
}
```

## Production Deployment

### 1. Build and Start Services

```bash
cd /opt/admire-hrms

# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Initialize Database

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Create default permissions
docker-compose exec backend python manage.py create_default_permissions

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

### 3. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs --tail=50

# Test health endpoints
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/health/detailed/

# Run deployment tests
cd tests/deployment
pip install -r requirements.txt
pytest test_deployment.py -v
```

### 4. Set Up Automated Backups

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Test backup script
sudo ./scripts/backup.sh

# Add to crontab for daily backups at 2 AM
sudo crontab -e

# Add this line:
0 2 * * * /opt/admire-hrms/scripts/backup.sh >> /opt/admire-hrms/logs/backup.log 2>&1
```

### 5. Configure Remote Backup (Optional)

```bash
# Set up SSH key for remote backup
ssh-keygen -t rsa -b 4096 -f ~/.ssh/backup_key

# Copy public key to backup server
ssh-copy-id -i ~/.ssh/backup_key.pub user@backup-server

# Update .env with remote backup settings
REMOTE_BACKUP_ENABLED=true
REMOTE_BACKUP_HOST=backup-server
REMOTE_BACKUP_USER=backup-user
REMOTE_BACKUP_PATH=/backups/admire-hrms
```

## Post-Deployment

### 1. Security Hardening

```bash
# Set up firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Set up fail2ban
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Configure Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/admire-hrms

# Add:
/opt/admire-hrms/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose -f /opt/admire-hrms/docker-compose.yml restart backend
    endscript
}

/opt/admire-hrms/nginx/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose -f /opt/admire-hrms/docker-compose.yml restart nginx
    endscript
}
```

### 3. Set Up Monitoring Alerts

```bash
# Update alertmanager configuration
nano monitoring/alertmanager/alertmanager.yml

# Add your email and Slack webhook
ALERT_EMAIL_CRITICAL=critical@yourdomain.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 4. Performance Tuning

**PostgreSQL Tuning**:

```bash
# Edit PostgreSQL configuration
docker-compose exec db bash
nano /var/lib/postgresql/data/postgresql.conf

# Recommended settings for 16GB RAM:
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

**Nginx Tuning**:

```nginx
# Edit nginx.conf
worker_processes auto;
worker_connections 2048;
keepalive_timeout 65;
client_max_body_size 50M;
```

## Monitoring Setup

### 1. Deploy Monitoring Stack

```bash
# Start monitoring services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access Grafana
# URL: http://yourdomain.com:3001
# Default credentials: admin/admin (change immediately)

# Access Prometheus
# URL: http://yourdomain.com:9090
```

### 2. Configure Grafana Dashboards

1. Log in to Grafana
2. Add Prometheus data source
3. Import pre-built dashboards:
   - Node Exporter Dashboard (ID: 1860)
   - Docker Dashboard (ID: 893)
   - PostgreSQL Dashboard (ID: 9628)

### 3. Set Up Alerts

Configure alerts in `monitoring/prometheus/alerts.yml` and restart Prometheus:

```bash
docker-compose restart prometheus
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs db
docker-compose logs redis

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec backend python manage.py dbshell

# Reset database (CAUTION: This will delete all data)
docker-compose down -v
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check slow queries
docker-compose exec db psql -U postgres -d admire_hrms -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Clear cache
docker-compose exec backend python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Test certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Restart Nginx
docker-compose restart nginx
```

## Updating the Application

### Rolling Update (Zero Downtime)

```bash
cd /opt/admire-hrms

# Pull latest code
git pull origin main

# Build new images
docker-compose build

# Update services one by one
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
docker-compose up -d --no-deps --build nginx

# Run migrations
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

### Using Deployment Script

```bash
# Use the automated deployment script
sudo ./scripts/deploy.sh
```

## Scaling

### Horizontal Scaling

To scale services:

```bash
# Scale backend workers
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery_worker=4
```

### Load Balancer Configuration

For multiple backend instances, update `nginx/nginx.conf`:

```nginx
upstream backend {
    least_conn;
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

## Support

For issues or questions:
- Documentation: https://docs.admire-hrms.com
- Support Email: support@admire-hrms.com
- GitHub Issues: https://github.com/your-org/admire-hrms/issues

---

**Last Updated**: [Date]  
**Version**: 1.0.0
