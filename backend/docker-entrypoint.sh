#!/bin/sh
# Entrypoint script for Shrimp Market backend
# Handles database migrations and initialization

set -e

DB_PATH="${DATABASE_PATH:-/app/data/shrimp_market.db}"

# Ensure data directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Run database migrations
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Database migrations complete."
else
    echo "Warning: Alembic migration failed, falling back to init_database..."
    python -c "from src.db.database import init_database; init_database()"
fi

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port 8000