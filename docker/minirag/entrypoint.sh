#!/bin/bash
set -e

# PGVector needs the PostgreSQL `vector` extension. The same VECTOR_DB_BACKEND
# flag that selects the adapter also triggers its Alembic setup automatically.
if { [ "${PERSISTENCE_BACKEND:-mongodb}" = "postgresql" ] || [ "${VECTOR_DB_BACKEND:-QDRANT}" = "PGVECTOR" ]; } \
  && [ "${RUN_DB_MIGRATIONS:-false}" = "true" ]; then
  cd /app/models/db_schemes/minirag
  cp -f alembic.ini.example alembic.ini
  alembic upgrade head
  cd /app
fi

exec "$@"
