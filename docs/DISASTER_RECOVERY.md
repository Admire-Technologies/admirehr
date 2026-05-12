# Disaster Recovery Procedures

## Overview

This document outlines the disaster recovery procedures for Admire HRMS. Follow these procedures in case of system failure, data loss, or security incidents.

## Table of Contents

1. [Emergency Contacts](#emergency-contacts)
2. [Backup Strategy](#backup-strategy)
3. [Recovery Procedures](#recovery-procedures)
4. [Incident Response](#incident-response)
5. [Testing and Validation](#testing-and-validation)

## Emergency Contacts

### Primary Contacts
- **System Administrator**: admin@admire-hrms.com
- **Database Administrator**: dba@admire-hrms.com
- **Security Team**: security@admire-hrms.com
- **On-Call Engineer**: +1-XXX-XXX-XXXX

### Escalation Path
1. On-Call Engineer (Response time: 15 minutes)
2. System Administrator (Response time: 30 minutes)
3. CTO/Technical Lead (Response time: 1 hour)

## Backup Strategy

### Automated Backups

#### Daily Backups
- **Schedule**: Every day at 2:00 AM UTC
- **Type**: Full database backup + incremental file backup
- **Retention**: 30 days
- **Location**: `/opt/admire-hrms/backups` + Remote storage

#### Weekly Backups
- **Schedule**: Every Sunday at 1:00 AM UTC
- **Type**: Complete system backup (database + media + configuration)
- **Retention**: 90 days
- **Location**: Remote storage only

#### Monthly Backups
- **Schedule**: First day of each month at 12:00 AM UTC
- **Type**: Complete system backup with verification
- **Retention**: 1 year
- **Location**: Remote storage + offline storage

### Backup Components

1. **Database Backup**
   - PostgreSQL full dump
   - Encrypted Django application backup
   - Transaction logs

2. **File Backup**
   - Media files (employee photos, documents)
   - Static files
   - Configuration files

3. **Configuration Backup**
   - Environment variables (.env)
   - Docker configurations
   - Nginx configurations
   - Application settings

### Backup Verification

All backups are automatically verified:
- File integrity checks (checksums)
- Encryption validation
- Restore test (monthly)

## Recovery Procedures

### Scenario 1: Complete System Failure

**Symptoms**: Entire system is down, no services responding

**Recovery Steps**:

1. **Assess the Situation** (5 minutes)
   ```bash
   # Check system status
   docker-compose ps
   
   # Check logs
   docker-compose logs --tail=100
   
   # Check disk space
   df -h
   
   # Check system resources
   top
   ```

2. **Attempt Service Restart** (10 minutes)
   ```bash
   cd /opt/admire-hrms
   
   # Stop all services
   docker-compose down
   
   # Start services
   docker-compose up -d
   
   # Monitor startup
   docker-compose logs -f
   ```

3. **If Restart Fails, Restore from Backup** (30-60 minutes)
   ```bash
   # List available backups
   ls -lht /opt/admire-hrms/backups/*.backup.gz | head -5
   
   # Restore from latest backup
   sudo ./scripts/restore.sh --file=/opt/admire-hrms/backups/[BACKUP_FILE] --force
   ```

4. **Verify System Health** (10 minutes)
   ```bash
   # Run deployment tests
   cd tests/deployment
   pytest test_deployment.py -v
   
   # Check health endpoints
   curl http://localhost/health
   curl http://localhost/api/v1/health/detailed/
   ```

5. **Notify Stakeholders**
   - Send status update to management
   - Notify affected users
   - Document incident

### Scenario 2: Database Corruption

**Symptoms**: Database errors, data inconsistencies, failed queries

**Recovery Steps**:

1. **Stop Application Services** (2 minutes)
   ```bash
   docker-compose stop backend celery_worker celery_beat
   ```

2. **Backup Current State** (5 minutes)
   ```bash
   # Even if corrupted, backup current state
   docker-compose exec db pg_dumpall -U postgres > /tmp/corrupted_backup.sql
   ```

3. **Restore Database from Backup** (15-30 minutes)
   ```bash
   # Find latest good backup
   ls -lht /opt/admire-hrms/backups/*.backup.gz | head -5
   
   # Restore database
   docker-compose exec -T backend python manage.py restore_backup \
     --file=/backups/[BACKUP_FILE] --force
   ```

4. **Run Migrations** (5 minutes)
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Verify Data Integrity** (10 minutes)
   ```bash
   # Check database
   docker-compose exec db psql -U postgres -d admire_hrms -c "SELECT COUNT(*) FROM authentication_user;"
   
   # Run Django checks
   docker-compose exec backend python manage.py check
   ```

6. **Restart Services** (5 minutes)
   ```bash
   docker-compose start backend celery_worker celery_beat
   ```

### Scenario 3: Data Loss (Accidental Deletion)

**Symptoms**: Missing data, user reports deleted records

**Recovery Steps**:

1. **Identify Scope** (10 minutes)
   - Determine what data was deleted
   - Identify when deletion occurred
   - Check audit logs

2. **Find Appropriate Backup** (5 minutes)
   ```bash
   # List backups around the time before deletion
   ls -lht /opt/admire-hrms/backups/ | grep [DATE]
   ```

3. **Selective Data Restore** (20-40 minutes)
   ```bash
   # Extract specific data from backup
   # This requires custom script or manual SQL extraction
   
   # Option 1: Restore to temporary database
   docker-compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/temp_restore \
     backend python manage.py restore_backup --file=/backups/[BACKUP_FILE]
   
   # Option 2: Extract and import specific records
   # Use Django shell or SQL to copy specific records
   ```

4. **Verify Restored Data** (10 minutes)
   - Check record counts
   - Verify data integrity
   - Confirm with affected users

### Scenario 4: Security Breach

**Symptoms**: Unauthorized access, suspicious activity, data breach

**Recovery Steps**:

1. **Immediate Actions** (5 minutes)
   ```bash
   # Isolate the system
   docker-compose down
   
   # Block external access (if needed)
   sudo iptables -A INPUT -p tcp --dport 80 -j DROP
   sudo iptables -A INPUT -p tcp --dport 443 -j DROP
   ```

2. **Assess Damage** (30 minutes)
   - Review security logs
   - Check audit trails
   - Identify compromised accounts
   - Determine data exposure

3. **Secure the System** (60 minutes)
   ```bash
   # Change all passwords
   docker-compose exec backend python manage.py changepassword [username]
   
   # Rotate secret keys
   # Update .env file with new SECRET_KEY
   
   # Invalidate all sessions
   docker-compose exec backend python manage.py clearsessions
   
   # Revoke all JWT tokens
   docker-compose exec backend python manage.py shell
   >>> from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
   >>> OutstandingToken.objects.all().delete()
   ```

4. **Restore from Clean Backup** (60 minutes)
   ```bash
   # Restore from backup before breach
   sudo ./scripts/restore.sh --file=/opt/admire-hrms/backups/[CLEAN_BACKUP] --force
   ```

5. **Implement Additional Security** (30 minutes)
   - Enable additional logging
   - Implement IP restrictions
   - Add 2FA requirements
   - Update security policies

6. **Notify Authorities and Users**
   - Report to relevant authorities (if required)
   - Notify affected users
   - Document incident for compliance

### Scenario 5: Hardware Failure

**Symptoms**: Server unresponsive, disk failure, network issues

**Recovery Steps**:

1. **Migrate to Backup Server** (60-120 minutes)
   ```bash
   # On backup server
   cd /opt/admire-hrms
   
   # Pull latest images
   docker-compose pull
   
   # Restore from remote backup
   rsync -avz backup-server:/backups/latest/ /opt/admire-hrms/backups/
   
   # Restore system
   sudo ./scripts/restore.sh --file=/opt/admire-hrms/backups/[LATEST_BACKUP] --force
   ```

2. **Update DNS** (15 minutes)
   - Point domain to new server IP
   - Wait for DNS propagation

3. **Verify System** (15 minutes)
   ```bash
   # Run deployment tests
   pytest tests/deployment/test_deployment.py -v
   ```

## Incident Response

### Incident Classification

#### Severity 1 (Critical)
- Complete system outage
- Data breach
- Data loss affecting multiple users
- **Response Time**: 15 minutes
- **Resolution Target**: 4 hours

#### Severity 2 (High)
- Partial system outage
- Performance degradation affecting all users
- Security vulnerability discovered
- **Response Time**: 30 minutes
- **Resolution Target**: 8 hours

#### Severity 3 (Medium)
- Single service failure
- Performance issues affecting some users
- Non-critical data inconsistency
- **Response Time**: 2 hours
- **Resolution Target**: 24 hours

#### Severity 4 (Low)
- Minor bugs
- Cosmetic issues
- Feature requests
- **Response Time**: 24 hours
- **Resolution Target**: 1 week

### Incident Response Process

1. **Detection and Reporting**
   - Automated monitoring alerts
   - User reports
   - Security scans

2. **Initial Response**
   - Acknowledge incident
   - Assess severity
   - Notify stakeholders
   - Begin investigation

3. **Containment**
   - Isolate affected systems
   - Prevent further damage
   - Preserve evidence

4. **Recovery**
   - Follow appropriate recovery procedure
   - Restore services
   - Verify functionality

5. **Post-Incident**
   - Document incident
   - Conduct root cause analysis
   - Implement preventive measures
   - Update procedures

## Testing and Validation

### Monthly Disaster Recovery Drill

Perform a complete disaster recovery drill monthly:

1. **Backup Verification** (30 minutes)
   ```bash
   # Verify latest backup
   sudo ./scripts/backup.sh
   
   # Test restore to staging environment
   sudo ./scripts/restore.sh --file=[LATEST_BACKUP]
   ```

2. **Failover Test** (60 minutes)
   - Simulate primary server failure
   - Activate backup server
   - Verify all services
   - Test user access

3. **Documentation Review** (30 minutes)
   - Review and update procedures
   - Verify contact information
   - Update runbooks

### Quarterly Full Recovery Test

Perform a complete system recovery quarterly:

1. **Complete System Restore** (2-4 hours)
   - Restore from backup to clean environment
   - Verify all data
   - Test all functionality
   - Performance testing

2. **Security Audit** (2 hours)
   - Review access logs
   - Check security configurations
   - Verify encryption
   - Test authentication

3. **Capacity Planning** (1 hour)
   - Review resource usage
   - Plan for growth
   - Update infrastructure

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

### RTO (Maximum Acceptable Downtime)
- **Critical Systems**: 4 hours
- **Non-Critical Systems**: 24 hours

### RPO (Maximum Acceptable Data Loss)
- **Transactional Data**: 1 hour (continuous backup)
- **User Data**: 24 hours (daily backup)
- **Configuration**: 7 days (weekly backup)

## Appendix

### Useful Commands

```bash
# Check system status
docker-compose ps
docker-compose logs --tail=100

# Create manual backup
sudo ./scripts/backup.sh

# Restore from backup
sudo ./scripts/restore.sh --file=[BACKUP_FILE]

# Run deployment tests
pytest tests/deployment/test_deployment.py -v

# Check health
curl http://localhost/api/v1/health/detailed/

# View metrics
curl -H "Authorization: Bearer [TOKEN]" http://localhost/api/v1/monitoring/metrics/
```

### Backup Locations

- **Local**: `/opt/admire-hrms/backups`
- **Remote**: `backup-server:/backups/admire-hrms/`
- **Offline**: Physical storage at secure location

### Important Files

- Deployment script: `/opt/admire-hrms/scripts/deploy.sh`
- Backup script: `/opt/admire-hrms/scripts/backup.sh`
- Restore script: `/opt/admire-hrms/scripts/restore.sh`
- Environment config: `/opt/admire-hrms/.env`
- Docker compose: `/opt/admire-hrms/docker-compose.yml`

---

**Last Updated**: [Date]  
**Document Owner**: System Administrator  
**Review Frequency**: Quarterly
