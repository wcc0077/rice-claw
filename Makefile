# Makefile for Shrimp Market Docker deployment

.PHONY: help build up down logs restart clean backup restore

help: ## Show this help message
	@echo "Shrimp Market Docker Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## View logs (all services)
	docker compose logs -f

logs-backend: ## View backend logs
	docker compose logs -f backend

logs-frontend: ## View frontend logs
	docker compose logs -f frontend

restart: ## Restart all services
	docker compose restart

restart-backend: ## Restart backend only
	docker compose restart backend

ps: ## Show container status
	docker compose ps

health: ## Check service health
	@echo "Backend health:"
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "Backend not responding"
	@echo ""
	@echo "Frontend health:"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/health

clean: ## Remove containers, volumes, and images
	docker compose down -v
	docker compose rm -f
	docker rmi shrimp-market-backend shrimp-market-frontend 2>/dev/null || true

backup: ## Backup database to ./backup/
	@mkdir -p backup
	docker compose cp backend:/app/data/shrimp_market.db ./backup/shrimp_market_$$(date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to ./backup/"

restore: ## Restore database from backup (usage: make restore FILE=backup.db)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=backup_file.db"; \
		exit 1; \
	fi
	docker compose cp ./backup/$(FILE) backend:/app/data/shrimp_market.db
	docker compose restart backend
	@echo "Database restored from $(FILE)"

prod-build: ## Build for production
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

prod-up: ## Start production deployment
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Stop production deployment
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

shell-backend: ## Open shell in backend container
	docker compose exec backend bash

shell-frontend: ## Open shell in frontend container
	docker compose exec frontend sh

db-cli: ## Open SQLite CLI in backend
	docker compose exec backend sqlite3 /app/data/shrimp_market.db