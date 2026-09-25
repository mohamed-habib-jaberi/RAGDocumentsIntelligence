# PostgreSQL schema and Alembic migrations

This directory is used when `PERSISTENCE_BACKEND="postgresql"` or when
`VECTOR_DB_BACKEND="PGVECTOR"`. MongoDB itself does not use Alembic, but the
PGVector adapter requires the PostgreSQL `vector` extension installed by the
migrations in this directory.

The Alembic environment reads `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`,
`POSTGRES_HOST`, `POSTGRES_PORT`, and `POSTGRES_MAIN_DATABASE` directly from
`src/.env` or the process environment. Credentials are not stored in
`alembic.ini`.

Apply all migrations from this directory:

```bash
conda activate rag
alembic -c alembic.ini.example upgrade head
```

Inspect the active revision:

```bash
alembic -c alembic.ini.example current
```

After changing a SQLAlchemy schema, generate and review a migration before
applying it:

```bash
alembic -c alembic.ini.example revision --autogenerate -m "describe change"
alembic -c alembic.ini.example upgrade head
```

In Docker, only the FastAPI container runs migrations. They run when
`RUN_DB_MIGRATIONS="true"` and either PostgreSQL persistence or the PGVector
vector backend is selected.
