#!/bin/sh
# Entrypoint script for Shrimp Market backend
# Handles database migrations and initialization

set -e

echo "Starting Shrimp Market Backend..."
echo "Database type: ${DB_TYPE:-sqlite}"

# Wait for PostgreSQL to be ready (if using PostgreSQL)
if [ "${DB_TYPE}" = "postgresql" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    max_retries=30
    retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if python -c "
import psycopg2
conn = psycopg2.connect(
    host='${POSTGRES_HOST}',
    port=${POSTGRES_PORT:-5432},
    user='${POSTGRES_USER}',
    password='${POSTGRES_PASSWORD}',
    database='${POSTGRES_DB}'
)
conn.close()
" 2>/dev/null; then
            echo "PostgreSQL is ready!"
            break
        fi
        retry_count=$((retry_count + 1))
        echo "Waiting for PostgreSQL... (${retry_count}/${max_retries})"
        sleep 2
    done

    if [ $retry_count -eq $max_retries ]; then
        echo "Warning: PostgreSQL connection timeout, proceeding anyway..."
    fi
fi

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