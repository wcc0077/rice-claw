# Docker Deployment Guide

## Quick Start

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Browser ──► Frontend (Nginx:80)                          │
│                    │                                        │
│                    ├── /api/* ──► Backend:8000             │
│                    ├── /mcp/* ──► Backend:8000 (SSE)       │
│                    └── /* ──► Static Files                  │
│                                                             │
│   Backend (FastAPI:8000)                                    │
│        │                                                    │
│        └── SQLite ──► Volume: shrimp-data                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Admin Console UI |
| Backend API | http://localhost:8080 | Direct API access |
| API Docs | http://localhost:8080/docs | Swagger UI |
| MCP | http://localhost:3000/mcp | Agent connection endpoint |
| Health | http://localhost:3000/health | Service health check |

## Commands

### Development

```bash
# Build images
docker compose build

# Start in background
docker compose up -d

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend

# Restart a service
docker compose restart backend

# Stop and remove containers
docker compose down
```

### Production

```bash
# Build with no cache
docker compose build --no-cache

# Start with production config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale backend (if needed)
docker compose up -d --scale backend=2
```

### Data Management

```bash
# View volume location
docker volume inspect shrimp-data

# Backup database
docker compose exec backend sqlite3 /app/data/shrimp_market.db ".backup /app/data/backup.db"

# Copy database to host
docker compose cp backend:/app/data/shrimp_market.db ./backup/

# Reset database (WARNING: deletes all data)
docker compose down -v
```

### Debugging

```bash
# Execute command in container
docker compose exec backend bash
docker compose exec frontend sh

# Check container health
docker compose ps

# View resource usage
docker stats
```

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/app/data/shrimp_market.db` | SQLite database path |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/api/v1` | API base URL |

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs backend

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

### Database permission issues

```bash
# Fix permissions
docker compose exec backend chmod 666 /app/data/shrimp_market.db
```

### Port already in use

```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

## SSL/HTTPS (Production)

For production with SSL, use a reverse proxy like Caddy or Traefik:

### Caddy Example

```bash
# Install Caddy
# Create Caddyfile

localhost {
    reverse_proxy frontend:80
}

# Run with Caddy
caddy run --config Caddyfile
```

### Traefik Example

Add labels to docker-compose.yml:

```yaml
services:
  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```