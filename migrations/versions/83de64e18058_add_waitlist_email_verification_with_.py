"""add waitlist email verification with token

Revision ID: 83de64e18058
Revises: 052377127bb5
Create Date: 2026-04-15 10:20:36.298958

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "83de64e18058"
down_revision: Union[str, Sequence[str], None] = "052377127bb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("waitlist") as batch_op:
        batch_op.add_column(
            sa.Column(
                "verified",
                sa.Integer(),
                nullable=False,
                server_default="0",  # existing rows default to unverified
            )
        )
        batch_op.add_column(
            sa.Column(
                "verify_token",
                sa.String(64),
                nullable=True,  # NULL once token is consumed
            )
        )
        batch_op.create_index(
            "ix_waitlist_verify_token",
            ["verify_token"],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table("waitlist") as batch_op:
        batch_op.drop_index("ix_waitlist_verify_token")
        batch_op.drop_column("verify_token")
        batch_op.drop_column("verified")
