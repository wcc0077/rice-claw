#!/bin/bash
# Server Setup Script for Shrimp Market CI/CD (Local Build)
# Run this script on your server once to set up the deployment environment
#
# Usage: sudo bash setup-server.sh

set -e

echo "=========================================="
echo "Shrimp Market Server Setup (Local Build)"
echo "=========================================="

# Configuration
PROJECT_DIR="/opt/shrimp-market"
REPO_URL="https://github.com/wcc0077/rice-claw.git"
NGINX_CONF="/etc/nginx/conf.d/shrimp-market.conf"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Install git if not installed
echo "[1/6] Checking git..."
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    yum install -y git
fi

# Install Docker if not installed
echo "[2/6] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    yum install -y docker
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not installed
echo "[3/6] Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "Docker Compose not found, checking for standalone..."
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi
fi

# Clone or update repository
echo "[4/6] Setting up project directory..."
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "Repository exists, updating..."
    cd $PROJECT_DIR
    git pull origin main
else
    echo "Cloning repository..."
    rm -rf $PROJECT_DIR
    git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Setup Nginx
echo "[5/6] Setting up Nginx..."
if ! command -v nginx &> /dev/null; then
    echo "Nginx not found, installing..."
    yum install -y nginx
fi

# Create Nginx configuration
cp $PROJECT_DIR/deploy/nginx.conf $NGINX_CONF

# Enable and start Nginx
systemctl enable nginx
systemctl reload nginx

# Configure firewall
echo "[6/6] Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=3000/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=8080/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=8000/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo "Firewall ports opened"
fi

# Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Project directory: ${PROJECT_DIR}"
echo "Nginx config: ${NGINX_CONF}"
echo ""
echo "Files:"
ls -la $PROJECT_DIR/deploy/
echo ""
echo "Next steps:"
echo "  1. Configure DNS: test.xiayouqian.online -> server IP"
echo "  2. Configure DNS: xiayouqian.online -> server IP"
echo "  3. Add GitHub Secrets in repository settings"
echo "  4. Push to main or create Release to trigger deployment"
echo ""
echo "Test build manually:"
echo "  cd $PROJECT_DIR"
echo "  docker compose -f deploy/docker-compose.staging.yml up -d"
echo "=========================================="