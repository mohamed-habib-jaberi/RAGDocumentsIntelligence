# PostgreSQL schema and Alembic migrations

This directory is used only when `PERSISTENCE_BACKEND="postgresql"`.
MongoDB does not use Alembic.

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

In Docker, only the FastAPI container runs migrations, and only when both
`PERSISTENCE_BACKEND="postgresql"` and `RUN_DB_MIGRATIONS="true"` are set.
