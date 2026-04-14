"""add missing columns

Revision ID: 052377127bb5
Revises: d5253b127250
Create Date: 2026-04-13 23:12:00.445561

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "052377127bb5"
down_revision: Union[str, Sequence[str], None] = "d5253b127250"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.add_column(
            sa.Column(
                "attempts_allowed", sa.Integer(), nullable=False, server_default="1"
            )
        )
        batch_op.add_column(
            sa.Column("auto_grade", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("show_answers", sa.Integer(), nullable=False, server_default="0")
        )

    with op.batch_alter_table("lesson_blocks", recreate="always") as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Text(),
            type_=sa.Text(),
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
