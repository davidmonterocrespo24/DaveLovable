#!/bin/bash

################################################################################
# DaveLovable Uninstallation Script
# This script removes DaveLovable from Ubuntu server
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get project directory
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

echo ""
echo "================================================================"
echo "  DaveLovable Uninstallation Script"
echo "================================================================"
echo ""
log_warn "This will completely remove DaveLovable from your system!"
log_warn "Project directory: $PROJECT_DIR"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "Uninstallation cancelled"
    exit 0
fi

# Ask about domain for SSL removal
read -p "Enter domain name for SSL certificate removal (or press Enter to skip): " DOMAIN

################################################################################
# 1. Stop and disable backend service
################################################################################
log_info "Stopping backend service..."
if sudo systemctl is-active --quiet davelovable-backend; then
    sudo systemctl stop davelovable-backend
fi

if sudo systemctl is-enabled --quiet davelovable-backend 2>/dev/null; then
    sudo systemctl disable davelovable-backend
fi

################################################################################
# 2. Remove systemd service file
################################################################################
log_info "Removing systemd service..."
if [ -f /etc/systemd/system/davelovable-backend.service ]; then
    sudo rm /etc/systemd/system/davelovable-backend.service
    sudo systemctl daemon-reload
fi

################################################################################
# 3. Remove Nginx configuration
################################################################################
log_info "Removing Nginx configuration..."
if [ -L /etc/nginx/sites-enabled/davelovable ]; then
    sudo rm /etc/nginx/sites-enabled/davelovable
fi

if [ -f /etc/nginx/sites-available/davelovable ]; then
    sudo rm /etc/nginx/sites-available/davelovable
fi

sudo systemctl reload nginx || true

################################################################################
# 4. Remove SSL certificate
################################################################################
if [ ! -z "$DOMAIN" ]; then
    log_info "Removing SSL certificate for $DOMAIN..."
    sudo certbot delete --cert-name "$DOMAIN" --non-interactive || log_warn "SSL certificate not found or already removed"
fi

################################################################################
# 5. Remove log files
################################################################################
log_info "Removing log files..."
sudo rm -f /var/log/davelovable-backend.log
sudo rm -f /var/log/davelovable-backend-error.log
sudo rm -f /var/log/davelovable-backup.log

################################################################################
# 6. Remove cron job
################################################################################
log_info "Removing backup cron job..."
(crontab -l 2>/dev/null | grep -v "$PROJECT_DIR/backup.sh") | crontab - || true

################################################################################
# 7. Backup before deletion
################################################################################
log_warn "Creating final backup before deletion..."
BACKUP_FINAL="$HOME/davelovable-final-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_FINAL"

if [ -f "$PROJECT_DIR/backend/davelovable.db" ]; then
    cp "$PROJECT_DIR/backend/davelovable.db" "$BACKUP_FINAL/"
fi

if [ -d "$PROJECT_DIR/backend/projects" ]; then
    tar -czf "$BACKUP_FINAL/projects.tar.gz" -C "$PROJECT_DIR/backend" projects
fi

if [ -f "$PROJECT_DIR/backend/.env" ]; then
    cp "$PROJECT_DIR/backend/.env" "$BACKUP_FINAL/env.backup"
fi

log_info "Final backup created at: $BACKUP_FINAL"

################################################################################
# 8. Remove project directory
################################################################################
read -p "Remove project directory ($PROJECT_DIR)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Removing project directory..."
    cd "$HOME"
    rm -rf "$PROJECT_DIR"
    log_info "Project directory removed"
else
    log_warn "Project directory kept at: $PROJECT_DIR"
fi

################################################################################
# Uninstallation Complete
################################################################################
echo ""
echo "================================================================"
log_info "Uninstallation completed!"
echo "================================================================"
echo ""
log_info "Final backup saved at: $BACKUP_FINAL"
echo ""
log_warn "Note: System packages (Python, Node.js, Nginx) were NOT removed."
log_warn "To remove them manually, run:"
echo "  sudo apt remove --purge python3-venv nginx certbot python3-certbot-nginx"
echo ""
