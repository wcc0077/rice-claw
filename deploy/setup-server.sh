#!/bin/bash
# Server Setup Script for Shrimp Market CI/CD
# Run this script on your server once to set up the deployment environment
#
# Usage: sudo bash setup-server.sh

set -e

echo "=========================================="
echo "Shrimp Market Server Setup"
echo "=========================================="

# Configuration
PROJECT_DIR="/opt/shrimp-market"
NGINX_CONF="/etc/nginx/conf.d/shrimp-market.conf"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Create project directory
echo "[1/5] Creating project directory..."
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

# Create docker-compose files
echo "[2/5] Creating docker-compose files..."

cat > docker-compose.staging.yml << 'EOF'
# Docker Compose for Staging Environment
services:
  backend:
    image: ghcr.io/wcc0077/rice-claw-backend:staging
    container_name: shrimp-backend-staging
    restart: unless-stopped
    ports:
      - "8080:8000"
    volumes:
      - shrimp-staging-data:/app/data
    environment:
      - DATABASE_PATH=/app/data/shrimp_market.db
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - shrimp-staging-network

  frontend:
    image: ghcr.io/wcc0077/rice-claw-frontend:staging
    container_name: shrimp-frontend-staging
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - shrimp-staging-network

volumes:
  shrimp-staging-data:
    driver: local

networks:
  shrimp-staging-network:
    driver: bridge
EOF

cat > docker-compose.prod.yml << 'EOF'
# Docker Compose for Production Environment
services:
  backend:
    image: ghcr.io/wcc0077/rice-claw-backend:latest
    container_name: shrimp-backend-prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - shrimp-prod-data:/app/data
    environment:
      - DATABASE_PATH=/app/data/shrimp_market.db
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - shrimp-prod-network

  frontend:
    image: ghcr.io/wcc0077/rice-claw-frontend:latest
    container_name: shrimp-frontend-prod
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - shrimp-prod-network

volumes:
  shrimp-prod-data:
    driver: local

networks:
  shrimp-prod-network:
    driver: bridge
EOF

# Setup Nginx
echo "[3/5] Setting up Nginx..."

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Nginx not found, installing..."
    yum install -y nginx
fi

# Create Nginx configuration
cat > ${NGINX_CONF} << 'EOF'
# Staging Environment
server {
    listen 80;
    server_name test.xiayouqian.online;

    access_log /var/log/nginx/shrimp-staging.access.log;
    error_log /var/log/nginx/shrimp-staging.error.log;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /mcp {
        proxy_pass http://127.0.0.1:8080/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
    }

    location /health {
        proxy_pass http://127.0.0.1:8080/health;
    }
}

# Production Environment
server {
    listen 80;
    server_name xiayouqian.online www.xiayouqian.online;

    access_log /var/log/nginx/shrimp-prod.access.log;
    error_log /var/log/nginx/shrimp-prod.error.log;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /mcp {
        proxy_pass http://127.0.0.1:8000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
EOF

# Enable and start Nginx
systemctl enable nginx
systemctl restart nginx

echo "[4/5] Configuring firewall..."

# Open ports (firewalld)
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=3000/tcp
    firewall-cmd --permanent --add-port=8080/tcp
    firewall-cmd --reload
    echo "Firewall ports opened"
fi

echo "[5/5] Verifying setup..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "WARNING: Docker not installed. Please install Docker first."
fi

if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
    echo "WARNING: Docker Compose not installed. Please install Docker Compose first."
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
echo "Files created:"
echo "  - docker-compose.staging.yml (testing environment)"
echo "  - docker-compose.prod.yml (production environment)"
echo ""
echo "Next steps:"
echo "  1. Configure DNS: test.xiayouqian.online -> server IP"
echo "  2. Configure DNS: xiayouqian.online -> server IP"
echo "  3. Add GitHub Secrets in repository settings"
echo "  4. Push to main or create Release to trigger deployment"
echo ""
echo "For SSL/HTTPS, consider using certbot:"
echo "  certbot --nginx -d xiayouqian.online -d www.xiayouqian.online"
echo "  certbot --nginx -d test.xiayouqian.online"
echo "=========================================="