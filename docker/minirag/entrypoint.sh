#!/bin/bash
set -e

if { [ "${PERSISTENCE_BACKEND:-mongodb}" = "postgresql" ] || [ "${VECTOR_DB_BACKEND:-QDRANT}" = "PGVECTOR" ]; } \
  && [ "${RUN_DB_MIGRATIONS:-false}" = "true" ]; then
  cd /app/models/db_schemes/minirag
  cp -f alembic.ini.example alembic.ini
  alembic upgrade head
  cd /app
fi

exec "$@"
