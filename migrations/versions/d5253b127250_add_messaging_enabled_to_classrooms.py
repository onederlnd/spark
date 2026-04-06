"""add messaging_enabled to classrooms

Revision ID: d5253b127250
Revises: 8f5f585c46f9
Create Date: 2026-04-05 15:27:08.090967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5253b127250'
down_revision: Union[str, Sequence[str], None] = '8f5f585c46f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "classrooms",
        sa.Column(
            "messaging_enabled",
            sa.Integer(),
            nullable=False,
            server_default="0",
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("classrooms", "messaging_enabled")
