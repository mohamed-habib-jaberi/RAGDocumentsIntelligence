"""Enable the pgvector PostgreSQL extension.

Revision ID: 13c000000003
Revises: 13c000000002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "13c000000003"
down_revision: str | None = "13c000000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Vector collections may still depend on the extension. They are managed
    # at runtime like Qdrant collections, so do not drop it automatically.
    pass
