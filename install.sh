#!/bin/bash

################################################################################
# DaveLovable Installation Script
# This script installs and configures the DaveLovable application on Ubuntu
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root - allow but warn
if [[ $EUID -eq 0 ]]; then
   log_warn "Running as root user. This is allowed but not recommended for production environments."
fi

# Get domain from user
echo ""
echo "================================================================"
echo "  DaveLovable Installation Script"
echo "================================================================"
echo ""
read -p "Enter your domain name (e.g., davelovable.com): " DOMAIN
read -p "Enter your email for SSL certificates (for Let's Encrypt): " EMAIL
read -p "Enter OpenAI API Key: " OPENAI_API_KEY

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ] || [ -z "$OPENAI_API_KEY" ]; then
    log_error "Domain, email, and OpenAI API key are required!"
    exit 1
fi

# Get current directory
PROJECT_DIR=$(pwd)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/front"
VENV_DIR="$BACKEND_DIR/venv"

log_info "Installation settings:"
log_info "  Domain: $DOMAIN"
log_info "  Email: $EMAIL"
log_info "  Project directory: $PROJECT_DIR"
log_info "  Backend directory: $BACKEND_DIR"
log_info "  Frontend directory: $FRONTEND_DIR"
echo ""
read -p "Continue with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Installation cancelled"
    exit 0
fi

################################################################################
# 1. Update system packages
################################################################################
log_info "Updating system packages..."
sudo apt update
sudo apt upgrade -y

################################################################################
# 2. Install required dependencies
################################################################################
log_info "Installing system dependencies (without Node.js/npm first)..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    build-essential

# Remove any existing Node.js/npm installations to avoid conflicts
log_info "Removing any existing Node.js/npm installations..."
sudo apt remove --purge -y nodejs npm node 2>/dev/null || true
sudo apt autoremove -y

# Install Node.js 20.x (LTS) from NodeSource (includes npm)
log_info "Installing Node.js 20.x LTS from NodeSource..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
log_info "Verifying installations..."
python3 --version
node --version
npm --version
nginx -v

################################################################################
# 3. Setup Python Virtual Environment
################################################################################
log_info "Creating Python virtual environment..."
cd "$BACKEND_DIR"
python3 -m venv venv

log_info "Activating virtual environment and installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

################################################################################
# 4. Setup Backend Environment Variables
################################################################################
log_info "Configuring backend environment variables..."
cd "$BACKEND_DIR"

if [ ! -f .env ]; then
    cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_MODEL=gpt-4
OPENAI_API_BASE_URL=https://api.openai.com/v1

# Database
DATABASE_URL=sqlite:///./davelovable.db

# Security
SECRET_KEY=$(openssl rand -hex 32)

# Server
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Projects
PROJECTS_BASE_DIR=$BACKEND_DIR/projects

# AutoGen
AUTOGEN_MAX_ROUND=10
EOF
    log_info "Backend .env file created"
else
    log_warn "Backend .env file already exists, skipping..."
fi

################################################################################
# 5. Initialize Database
################################################################################
log_info "Initializing database..."
cd "$BACKEND_DIR"
source venv/bin/activate
python init_db.py
deactivate

################################################################################
# 6. Setup Frontend
################################################################################
log_info "Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm install

log_info "Building frontend..."
VITE_API_URL=https://$DOMAIN/api npm run build

################################################################################
# 7. Create systemd service for backend
################################################################################
log_info "Creating systemd service for backend..."

sudo tee /etc/systemd/system/davelovable-backend.service > /dev/null << EOF
[Unit]
Description=DaveLovable Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/davelovable-backend.log
StandardError=append:/var/log/davelovable-backend-error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Create log files
sudo touch /var/log/davelovable-backend.log
sudo touch /var/log/davelovable-backend-error.log
sudo chown $USER:$USER /var/log/davelovable-backend.log
sudo chown $USER:$USER /var/log/davelovable-backend-error.log

# Enable and start service
log_info "Enabling and starting backend service..."
sudo systemctl daemon-reload
sudo systemctl enable davelovable-backend
sudo systemctl start davelovable-backend

# Check service status
sleep 2
if sudo systemctl is-active --quiet davelovable-backend; then
    log_info "Backend service started successfully!"
else
    log_error "Backend service failed to start. Check logs with: sudo journalctl -u davelovable-backend -f"
fi

################################################################################
# 8. Configure Nginx
################################################################################
log_info "Configuring Nginx..."

sudo tee /etc/nginx/sites-available/davelovable > /dev/null << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER;

    # Frontend - Serve static files
    location / {
        root FRONTEND_DIST_PLACEHOLDER;
        try_files $uri $uri/ /index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # COOP and COEP headers for WebContainers
        add_header Cross-Origin-Opener-Policy "same-origin" always;
        add_header Cross-Origin-Embedder-Policy "require-corp" always;
    }

    # Backend API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Increase timeouts for long-running requests (AI processing)
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # WebSocket support for SSE
    location /api/v1/chat {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # SSE specific headers
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for SSE
        proxy_buffering off;
        proxy_cache off;

        # Keep connection alive
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Client body size (for file uploads)
    client_max_body_size 50M;
}
EOF

# Replace placeholders
sudo sed -i "s|DOMAIN_PLACEHOLDER|$DOMAIN|g" /etc/nginx/sites-available/davelovable
sudo sed -i "s|FRONTEND_DIST_PLACEHOLDER|$FRONTEND_DIR/dist|g" /etc/nginx/sites-available/davelovable

# Enable site
sudo ln -sf /etc/nginx/sites-available/davelovable /etc/nginx/sites-enabled/davelovable

# Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
log_info "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
log_info "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

################################################################################
# 9. Setup SSL with Let's Encrypt
################################################################################
log_info "Setting up SSL with Let's Encrypt..."
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

# Auto-renewal test
log_info "Testing SSL certificate auto-renewal..."
sudo certbot renew --dry-run

################################################################################
# 10. Setup Firewall
################################################################################
log_info "Configuring UFW firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

################################################################################
# 11. Create update script
################################################################################
log_info "Creating update script..."
cat > "$PROJECT_DIR/update.sh" << 'UPDATEEOF'
#!/bin/bash
set -e

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/front"

echo "Updating DaveLovable..."

# Pull latest changes
git pull

# Update backend
echo "Updating backend dependencies..."
cd "$BACKEND_DIR"
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Update frontend
echo "Updating frontend dependencies..."
cd "$FRONTEND_DIR"
npm install
npm run build

# Restart backend service
echo "Restarting backend service..."
sudo systemctl restart davelovable-backend

# Reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx

echo "Update complete!"
UPDATEEOF

chmod +x "$PROJECT_DIR/update.sh"

################################################################################
# 12. Create backup script
################################################################################
log_info "Creating backup script..."
cat > "$PROJECT_DIR/backup.sh" << 'BACKUPEOF'
#!/bin/bash
set -e

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Creating backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
cp "$PROJECT_DIR/backend/davelovable.db" "$BACKUP_DIR/davelovable_${TIMESTAMP}.db"

# Backup projects
tar -czf "$BACKUP_DIR/projects_${TIMESTAMP}.tar.gz" -C "$PROJECT_DIR/backend" projects

# Backup .env
cp "$PROJECT_DIR/backend/.env" "$BACKUP_DIR/env_${TIMESTAMP}.backup"

# Keep only last 7 backups
find "$BACKUP_DIR" -name "*.db" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.backup" -mtime +7 -delete

echo "Backup complete: $BACKUP_DIR"
BACKUPEOF

chmod +x "$PROJECT_DIR/backup.sh"

# Setup daily backup cron job
(crontab -l 2>/dev/null | grep -v "$PROJECT_DIR/backup.sh"; echo "0 2 * * * $PROJECT_DIR/backup.sh >> /var/log/davelovable-backup.log 2>&1") | crontab -

################################################################################
# Installation Complete
################################################################################
echo ""
echo "================================================================"
log_info "Installation completed successfully!"
echo "================================================================"
echo ""
log_info "Your application is now running at: https://$DOMAIN"
echo ""
log_info "Useful commands:"
echo "  - Check backend status:    sudo systemctl status davelovable-backend"
echo "  - View backend logs:       sudo journalctl -u davelovable-backend -f"
echo "  - Restart backend:         sudo systemctl restart davelovable-backend"
echo "  - Check Nginx status:      sudo systemctl status nginx"
echo "  - Update application:      ./update.sh"
echo "  - Create backup:           ./backup.sh"
echo ""
log_info "Log files:"
echo "  - Backend logs:            /var/log/davelovable-backend.log"
echo "  - Backend errors:          /var/log/davelovable-backend-error.log"
echo "  - Nginx access logs:       /var/log/nginx/access.log"
echo "  - Nginx error logs:        /var/log/nginx/error.log"
echo ""
log_warn "IMPORTANT: Keep your .env file secure and backed up!"
echo ""
