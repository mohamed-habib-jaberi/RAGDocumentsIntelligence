#!/bin/bash
set -e

echo "Running database migrations..."
cd /app/models/db_schemes/minirag/
alembic upgrade head
cd /app

# Start the command declared by the image (Uvicorn in the Dockerfile).
exec "$@"
