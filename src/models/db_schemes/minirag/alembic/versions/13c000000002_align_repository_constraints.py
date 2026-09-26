"""Align PostgreSQL constraints with the MongoDB repository contract.

Revision ID: 13c000000002
Revises: 13c000000001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "13c000000002"
down_revision: str | None = "13c000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the schema changes defined by this database revision."""
    op.create_index(
        "ux_asset_project_id_name",
        "assets",
        ["asset_project_id", "asset_name"],
        unique=True,
    )


def downgrade() -> None:
    """Revert the schema changes introduced by this database revision."""
    op.drop_index("ux_asset_project_id_name", table_name="assets")
