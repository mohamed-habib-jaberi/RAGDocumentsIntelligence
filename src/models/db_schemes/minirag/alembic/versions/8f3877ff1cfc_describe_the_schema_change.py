"""Compatibility checkpoint retained from the local migration history.

Revision ID: 8f3877ff1cfc
Revises: fee4cd54bd38
"""

from typing import Sequence, Union


revision: str = "8f3877ff1cfc"
down_revision: Union[str, None] = "fee4cd54bd38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the schema changes defined by this database revision."""
    pass


def downgrade() -> None:
    """Revert the schema changes introduced by this database revision."""
    pass
