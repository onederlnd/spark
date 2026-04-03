"""add invited_at to waitlist

Revision ID: 9a4aeee0e129
Revises: 52cd938e378c
Create Date: 2026-04-03 09:54:54.204257

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a4aeee0e129"
down_revision: Union[str, Sequence[str], None] = "52cd938e378c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("waitlist", sa.Column("invited_at", sa.Text(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("waitlist", "invited_at")
