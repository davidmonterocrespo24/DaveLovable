# Quick Deployment Guide

## One-Command Installation

```bash
chmod +x install.sh && ./install.sh
```

That's it! The script will guide you through the installation.

## What You Need

1. **Ubuntu Server 20.04 or 22.04**
2. **Domain name** pointed to your server
3. **OpenAI API Key**
4. **Email address** for SSL certificates

## Installation Time

Approximately **10-15 minutes** depending on your server speed.

## What Gets Installed

- ✅ Python 3 virtual environment
- ✅ Node.js 20.x LTS
- ✅ Nginx web server
- ✅ SSL certificates (Let's Encrypt)
- ✅ Systemd service (auto-starts on reboot)
- ✅ Firewall configuration (UFW)
- ✅ Automatic daily backups

## After Installation

Your app will be running at: `https://your-domain.com`

### Useful Commands

```bash
# Check status
sudo systemctl status davelovable-backend

# View logs
sudo journalctl -u davelovable-backend -f

# Update app
./update.sh

# Create backup
./backup.sh

# Uninstall
./uninstall.sh
```

## Server Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 20GB minimum
- **OS**: Ubuntu 20.04 or 22.04

## Architecture

```
Internet
    ↓
Nginx (Port 80/443)
    ↓
    ├─→ Frontend (Static files)
    └─→ Backend API (Port 8000)
            ↓
        SQLite Database
```

## Security Features

- ✅ HTTPS with auto-renewal SSL
- ✅ Firewall enabled (UFW)
- ✅ Security headers (COOP, COEP)
- ✅ Service runs as non-root user
- ✅ API rate limiting via Nginx
- ✅ Secure environment variables

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u davelovable-backend -n 50

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Test manually
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Can't access website

```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check firewall
sudo ufw status

# Check DNS
nslookup your-domain.com
```

### SSL certificate issues

```bash
# Check certificates
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal
```

## Update Process

```bash
# Pull latest code
git pull

# Run update script
./update.sh
```

The update script will:
1. Update backend dependencies
2. Rebuild frontend
3. Restart services

## Backup & Restore

### Automatic Backups

Daily at 2 AM (via cron)

### Manual Backup

```bash
./backup.sh
```

### Restore

```bash
# Stop service
sudo systemctl stop davelovable-backend

# Restore database
cp backups/davelovable_TIMESTAMP.db backend/davelovable.db

# Restore projects
tar -xzf backups/projects_TIMESTAMP.tar.gz -C backend/

# Start service
sudo systemctl start davelovable-backend
```

## Monitoring

### Backend Logs

```bash
# Live logs
sudo journalctl -u davelovable-backend -f

# Last 100 lines
sudo journalctl -u davelovable-backend -n 100

# Logs from today
sudo journalctl -u davelovable-backend --since today
```

### Nginx Logs

```bash
# Access logs
tail -f /var/log/nginx/access.log

# Error logs
tail -f /var/log/nginx/error.log
```

### System Resources

```bash
# Check CPU and memory
htop

# Check disk usage
df -h

# Check service status
sudo systemctl status davelovable-backend nginx
```

## Performance Tuning

### Increase Workers

Edit `/etc/systemd/system/davelovable-backend.service`:

```ini
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart davelovable-backend
```

### Enable Nginx Caching

Add to `/etc/nginx/sites-available/davelovable`:

```nginx
# Static file caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Database Optimization

For production with many users, migrate to PostgreSQL:

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb davelovable

# Update backend/.env
DATABASE_URL=postgresql://user:password@localhost/davelovable

# Restart backend
sudo systemctl restart davelovable-backend
```

## Scaling

### Horizontal Scaling

Use a load balancer (Nginx, HAProxy) with multiple backend instances:

```nginx
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

location /api {
    proxy_pass http://backend;
}
```

### Database Scaling

- Use PostgreSQL with connection pooling
- Enable database replication
- Use Redis for caching

## Support

For detailed troubleshooting, see [INSTALLATION.md](INSTALLATION.md)

## License

See LICENSE file for details.
