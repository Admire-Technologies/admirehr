# Admire HRMS - Production Deployment

## Quick Start

### Prerequisites
- Docker 24.0+
- Docker Compose 2.20+
- 8GB RAM minimum (16GB recommended)
- 100GB disk space minimum

### Basic Deployment

1. **Clone and Configure**
   ```bash
   git clone https://github.com/your-org/admire-hrms.git
   cd admire-hrms
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Deploy**
   ```bash
   docker-compose up -d
   docker-compose exec backend python manage.py migrate
   docker-compose exec backend python manage.py createsuperuser
   docker-compose exec backend python manage.py collectstatic --noinput
   ```

3. **Verify**
   ```bash
   curl http://localhost/health
   curl http://localhost/api/v1/health/detailed/
   ```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (Port 80/443)                  │
│                    Load Balancer & Reverse Proxy             │
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────────┐
│   Django Backend       │      │   Next.js Frontend         │
│   (Port 8000)          │      │   (Port 3000)              │
│   - REST API           │      │   - React UI               │
│   - WebSocket          │      │   - SSR/SSG                │
│   - Admin Panel        │      │                            │
└────────┬───────────────┘      └────────────────────────────┘
         │
         ├─────────────┬─────────────┬─────────────┐
         ▼             ▼             ▼             ▼
┌────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ PostgreSQL │  │  Redis   │  │  Celery  │  │ Celery Beat  │
│  Database  │  │  Cache   │  │  Worker  │  │  Scheduler   │
└────────────┘  └──────────┘  └──────────┘  └──────────────┘
```

## Components

### Core Services

- **Nginx**: Load balancer and reverse proxy
- **Backend**: Django REST Framework API
- **Frontend**: Next.js React application
- **PostgreSQL**: Primary database
- **Redis**: Cache and message broker
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task management

### Monitoring Stack (Optional)

- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notifications
- **Loki**: Log aggregation
- **Promtail**: Log shipping

## Directory Structure

```
admire-hrms/
├── backend/                    # Django backend
│   ├── apps/                   # Django applications
│   ├── admire_hrms/           # Project settings
│   ├── Dockerfile             # Backend container
│   ├── Dockerfile.celery      # Celery worker container
│   └── Dockerfile.celery-beat # Celery beat container
├── frontend/                   # Next.js frontend
│   ├── src/                   # Source code
│   └── Dockerfile             # Frontend container
├── nginx/                      # Nginx configuration
│   ├── nginx.conf             # Main configuration
│   └── Dockerfile             # Nginx container
├── monitoring/                 # Monitoring configurations
│   ├── prometheus/            # Prometheus config
│   ├── grafana/               # Grafana dashboards
│   ├── alertmanager/          # Alert configuration
│   ├── loki/                  # Loki config
│   └── promtail/              # Promtail config
├── scripts/                    # Deployment scripts
│   ├── deploy.sh              # Deployment automation
│   ├── backup.sh              # Backup automation
│   └── restore.sh             # Restore automation
├── tests/                      # Test suites
│   └── deployment/            # Deployment tests
├── docs/                       # Documentation
│   ├── DEPLOYMENT_GUIDE.md    # Full deployment guide
│   └── DISASTER_RECOVERY.md   # DR procedures
├── .github/                    # CI/CD workflows
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions pipeline
├── docker-compose.yml          # Main compose file
├── docker-compose.monitoring.yml # Monitoring stack
└── .env.example               # Environment template
```

## Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Security
SECRET_KEY=                    # Django secret key
DEBUG=False                    # Never True in production

# Database
POSTGRES_DB=admire_hrms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=            # Strong password

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Backup
BACKUP_ENCRYPTION_KEY=        # Encryption key for backups
BACKUP_RETENTION_DAYS=30
```

### Ports

Default ports (configurable):
- **80**: HTTP (Nginx)
- **443**: HTTPS (Nginx)
- **5432**: PostgreSQL (internal)
- **6379**: Redis (internal)
- **8000**: Backend (internal)
- **3000**: Frontend (internal)

Monitoring ports (optional):
- **3001**: Grafana
- **9090**: Prometheus
- **9093**: AlertManager
- **3100**: Loki

## Deployment Options

### Option 1: Docker Compose (Recommended for Single Server)

```bash
# Basic deployment
docker-compose up -d

# With monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Option 2: Automated Script

```bash
# Full deployment with health checks
sudo ./scripts/deploy.sh
```

### Option 3: CI/CD Pipeline

Push to `main` branch triggers automatic deployment via GitHub Actions.

## Backup and Recovery

### Automated Backups

Backups run automatically:
- **Daily**: 2:00 AM UTC
- **Retention**: 30 days
- **Location**: `/opt/admire-hrms/backups`

### Manual Backup

```bash
sudo ./scripts/backup.sh
```

### Restore from Backup

```bash
# List available backups
ls -lht /opt/admire-hrms/backups/*.backup.gz

# Restore
sudo ./scripts/restore.sh --file=/path/to/backup.gz --force
```

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost/health

# Detailed health
curl http://localhost/api/v1/health/detailed/

# Readiness check
curl http://localhost/api/v1/health/ready/

# Liveness check
curl http://localhost/api/v1/health/live/
```

### Metrics

```bash
# System metrics (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost/api/v1/monitoring/metrics/

# System status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost/api/v1/monitoring/status/
```

### Logs

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# View specific service
docker-compose logs --tail=100 backend

# Export logs
docker-compose logs > logs.txt
```

## Scaling

### Vertical Scaling

Increase resources in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Horizontal Scaling

Scale services:

```bash
# Scale backend
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery_worker=4
```

## Security

### Security Features

- ✅ JWT authentication
- ✅ HTTPS/TLS encryption
- ✅ Database encryption at rest
- ✅ Encrypted backups
- ✅ Rate limiting
- ✅ CORS protection
- ✅ Security headers
- ✅ Audit logging

### Security Checklist

- [ ] Change default passwords
- [ ] Configure firewall
- [ ] Set up SSL certificates
- [ ] Enable fail2ban
- [ ] Configure backup encryption
- [ ] Set up monitoring alerts
- [ ] Review security logs regularly

## Troubleshooting

### Common Issues

**Services won't start**:
```bash
docker-compose logs
docker-compose ps
df -h  # Check disk space
```

**Database connection failed**:
```bash
docker-compose exec backend python manage.py dbshell
docker-compose logs db
```

**High memory usage**:
```bash
docker stats
docker-compose restart
```

**SSL certificate issues**:
```bash
sudo certbot renew
docker-compose restart nginx
```

## Maintenance

### Regular Tasks

**Daily**:
- Monitor system health
- Check backup completion
- Review error logs

**Weekly**:
- Review security logs
- Check disk space
- Update dependencies

**Monthly**:
- Test disaster recovery
- Review performance metrics
- Update documentation

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate
```

## Performance Optimization

### Database Optimization

```bash
# Analyze database
docker-compose exec db psql -U postgres -d admire_hrms -c "ANALYZE;"

# Vacuum database
docker-compose exec db psql -U postgres -d admire_hrms -c "VACUUM ANALYZE;"
```

### Cache Optimization

```bash
# Clear cache
docker-compose exec backend python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Log Rotation

Logs are automatically rotated:
- **Rotation**: Daily
- **Retention**: 30 days
- **Compression**: Enabled

## Support and Documentation

- **Full Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Disaster Recovery**: `docs/DISASTER_RECOVERY.md`
- **API Documentation**: http://localhost/api/v1/docs/
- **Support**: support@admire-hrms.com

## License

Proprietary - All rights reserved

---

**Version**: 1.0.0  
**Last Updated**: 2024
