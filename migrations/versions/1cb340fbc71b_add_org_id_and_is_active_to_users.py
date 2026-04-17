"""add_org_id_and_is_active_to_users

Revision ID: 1cb340fbc71b
Revises: 83de64e18058
Create Date: 2026-04-17 10:50:35.907192

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1cb340fbc71b"
down_revision: Union[str, Sequence[str], None] = "83de64e18058"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    )
    op.add_column("organizations", sa.Column("name", sa.Text(), nullable=False))
    op.add_column("organizations", sa.Column("billing_email", sa.Text()))
    op.add_column("organizations", sa.Column("created_by", sa.Integer()))
    op.add_column(
        "organizations",
        sa.Column("created_at", sa.TIMESTAMP(), server_default="CURRENT_TIMESTAMP"),
    )

    # SQLite can't do this in one shot with FK, so just add the columns
    op.add_column("users", sa.Column("org_id", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade():
    op.drop_column("users", "is_active")
    op.drop_column("users", "org_id")
