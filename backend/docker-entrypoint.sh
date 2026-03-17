#!/bin/sh
# Entrypoint script for Shrimp Market backend
# Handles database initialization/reset

set -e

DB_PATH="${DATABASE_PATH:-/app/data/shrimp_market.db}"
DB_TEMPLATE="/app/init-data/shrimp_market.db"

# Reset database if requested (set RESET_DATA=true in docker-compose for new deployments)
if [ "${RESET_DATA}" = "true" ] && [ -f "$DB_TEMPLATE" ]; then
    echo "Resetting database from template..."
    cp "$DB_TEMPLATE" "$DB_PATH"
    echo "Database reset complete."
fi

# Run init_database() to ensure tables exist (idempotent)
# This won't overwrite existing data if tables already exist
python -c "from src.db.database import init_database; init_database()"

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port 8000