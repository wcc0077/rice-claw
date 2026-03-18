#!/bin/sh
# Entrypoint script for Shrimp Market backend
# Handles database migrations and initialization

set -e

DB_PATH="${DATABASE_PATH:-/app/data/shrimp_market.db}"

# Ensure data directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Database migrations complete."

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port 8000