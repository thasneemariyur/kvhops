# KVH Operations — Deployment Guide

## Environment Setup

### Environment Variables
Create `/home/frappe/kvh-bench/sites/kvh.yourdomain.com/site_config.json`:
```json
{
  "db_name": "kvh_erpnext",
  "db_password": "<DB_PASSWORD>",
  "db_host": "127.0.0.1",
  "db_port": "3306",
  "redis_cache": "redis://127.0.0.1:6379/0",
  "redis_queue": "redis://127.0.0.1:6379/1",
  "redis_socketio": "redis://127.0.0.1:6379/2",
  "socketio_port": 9000,
  "background_workers": 4,
  "frappe_user": "frappe",
  "auto_update": false,
  "encryption_key": "<GENERATE_WITH: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'>",
  "mail_server": "smtp.gmail.com",
  "mail_port": 587,
  "mail_login": "kvh.notifications@yourdomain.com",
  "mail_password": "<MAIL_APP_PASSWORD>",
  "mail_use_tls": 1,
  "auto_email_id": "kvh.notifications@yourdomain.com",
  "email_footer_address": "KVH Industries, [Your Address]"
}
```

---

## Production Deployment

### Nginx Configuration
After `bench setup nginx`, verify `/etc/nginx/nginx.conf` includes:
```nginx
upstream kvh_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 443 ssl http2;
    server_name kvh.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/kvh.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kvh.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://kvh_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
    }

    location /assets {
        alias /home/frappe/kvh-bench/sites/assets;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 50m;
    gzip on;
    gzip_types text/css application/javascript application/json;
}

server {
    listen 80;
    server_name kvh.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

### Supervisor Configuration
After `bench setup supervisor`, verify workers are running:
```bash
sudo supervisorctl status
# Should show:
# kvh-bench-web:kvh-bench-web-0    RUNNING
# kvh-bench-worker:kvh-bench-worker-default-0  RUNNING
# kvh-bench-worker:kvh-bench-worker-long-0     RUNNING
# kvh-bench-worker:kvh-bench-worker-short-0    RUNNING
# kvh-bench-schedule:kvh-bench-schedule-0      RUNNING
# kvh-bench-socketio:kvh-bench-socketio-0      RUNNING
```

### MariaDB Configuration
Edit `/etc/mysql/mariadb.conf.d/50-server.cnf`:
```ini
[mysqld]
# Performance for ERPNext
innodb_buffer_pool_size = 4G  # set to 70% of available RAM
innodb_log_file_size = 512M
innodb_flush_method = O_DIRECT
max_connections = 300
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Increase for large imports
max_allowed_packet = 128M
wait_timeout = 28800
interactive_timeout = 28800
```

---

## File Storage (S3 for Production)

For production, configure S3-compatible storage for file attachments:

```json
{
  "s3": {
    "bucket": "kvh-erpnext-files",
    "region": "ap-south-1",
    "access_key_id": "<AWS_ACCESS_KEY>",
    "secret_access_key": "<AWS_SECRET_KEY>"
  }
}
```

Install and configure:
```bash
bench --site kvh.yourdomain.com install-app s3_attachment
bench --site kvh.yourdomain.com execute frappe.integrations.s3_backup.backup
```

---

## Automated Backups

### Database Backups
Configure automatic backups in ERPNext:
1. Go to **Setup → System Settings**
2. Set **Backup Limit** = 7 (keep 7 daily backups)
3. Enable **Allow Scheduled Backup**

### S3 Backup Schedule
```bash
# Edit cron to back up daily at 2 AM
crontab -e
# Add:
0 2 * * * cd /home/frappe/kvh-bench && bench --site kvh.yourdomain.com backup --with-files >> /var/log/kvh-backup.log 2>&1
```

---

## Scaling

### Horizontal Scaling (Multiple Workers)
For high load, add more background workers in `Procfile`:
```
web: gunicorn -b 127.0.0.1:8000 --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 4 --max-requests 1000 frappe.app:application
worker_default: bench worker --queue default
worker_long: bench worker --queue long
worker_short: bench worker --queue short
```

### Redis Cluster
For production Redis, use Redis Sentinel or Redis Cluster to prevent single point of failure.

---

## Monitoring

### Frappe Error Log
```bash
# View application errors
bench --site kvh.yourdomain.com console
frappe.get_all("Error Log", order_by="creation desc", limit=20, fields=["method","error"])
```

### System Health Check
```bash
# Check all services
bench --site kvh.yourdomain.com doctor

# Check scheduler
bench --site kvh.yourdomain.com show-pending-jobs

# Check queue
bench --site kvh.yourdomain.com execute frappe.utils.background_jobs.get_stats
```

### Uptime Monitoring
Set up monitoring for:
- URL: `https://kvh.yourdomain.com/api/method/ping`
- Expected response: `{"message": "pong"}`
- Check interval: 1 minute
- Alert on: 2 consecutive failures

---

## Security Hardening

### Rate Limiting
Configure in `site_config.json`:
```json
{
  "deny_multiple_logins": true,
  "max_login_attempts": 5,
  "login_attempt_timeout_minutes": 15,
  "session_expiry": "06:00:00"
}
```

### Two-Factor Authentication
Enable 2FA for Admin roles:
1. **Setup → System Settings → Security**
2. Enable **Two Factor Authentication**
3. Select **OTP App** as method
4. Apply to: Admin, KVH Admin roles

### SSL/TLS Renewal (Let's Encrypt)
```bash
# Auto-renewal via certbot (installed during setup)
certbot renew --dry-run

# Add to cron for auto-renewal
0 0 * * 1 certbot renew --quiet && service nginx reload
```

---

## CI/CD Pipeline (Optional)

### GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to ERPNext

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: frappe
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/frappe/kvh-bench
            bench update --pull
            bench --site kvh.yourdomain.com migrate
            bench build --app kvh_ops
            sudo supervisorctl restart all
```

---

## Disaster Recovery

### Full Recovery Steps
1. Provision new Ubuntu 22.04 server
2. Follow INSTALLATION.md steps 1-4
3. Restore database:
   ```bash
   bench --site kvh.yourdomain.com restore /path/to/backup.sql.gz --with-private-files /path/to/files.tar
   ```
4. Re-run migrations:
   ```bash
   bench --site kvh.yourdomain.com migrate
   bench build
   ```
5. Verify site health:
   ```bash
   bench --site kvh.yourdomain.com doctor
   ```

### RTO (Recovery Time Objective): 2 hours
### RPO (Recovery Point Objective): 24 hours (daily backups)
