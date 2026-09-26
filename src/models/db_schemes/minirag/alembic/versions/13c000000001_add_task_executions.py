"""Add backend-neutral Celery task execution storage.

Revision ID: 13c000000001
Revises: 8f3877ff1cfc
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "13c000000001"
down_revision: str | None = "8f3877ff1cfc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the schema changes defined by this database revision."""
    op.create_table(
        "celery_task_executions",
        sa.Column("execution_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_name", sa.String(), nullable=False),
        sa.Column("task_args_hash", sa.String(length=64), nullable=False),
        sa.Column("task_args", postgresql.JSONB(), nullable=False),
        sa.Column("celery_task_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_celery_task_lookup",
        "celery_task_executions",
        ["celery_task_id", "task_name", "task_args_hash"],
        unique=True,
    )
    op.create_index(
        "ix_celery_task_created_at", "celery_task_executions", ["created_at"]
    )


def downgrade() -> None:
    """Revert the schema changes introduced by this database revision."""
    op.drop_index("ix_celery_task_created_at", table_name="celery_task_executions")
    op.drop_index("ix_celery_task_lookup", table_name="celery_task_executions")
    op.drop_table("celery_task_executions")
