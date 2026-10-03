"""drop legacy task argument unique index

Revision ID: 6e1d4f8a2c90
Revises: 243ca8b683b0
"""

from typing import Sequence, Union

from alembic import op


revision: str = "6e1d4f8a2c90"
down_revision: Union[str, None] = "243ca8b683b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow the same operation arguments to be submitted under a new task ID."""
    op.drop_index("ixz_task_name_args_hash", table_name="celery_task_executions")


def downgrade() -> None:
    """Restore the legacy uniqueness constraint on task name and arguments."""
    op.create_index(
        "ixz_task_name_args_hash",
        "celery_task_executions",
        ["task_name", "task_args_hash"],
        unique=True,
    )
