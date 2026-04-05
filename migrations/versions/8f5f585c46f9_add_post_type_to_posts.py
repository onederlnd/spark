"""add post_type to posts

Revision ID: 8f5f585c46f9
Revises: 9a4aeee0e129
Create Date: 2026-04-04 23:25:43.444538

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f5f585c46f9"
down_revision: Union[str, Sequence[str], None] = "9a4aeee0e129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("posts", sa.Column("post_type", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("posts", "post_type")
