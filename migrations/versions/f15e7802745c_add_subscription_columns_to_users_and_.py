"""add subscription columns to users and organizations

Revision ID: f15e7802745c
Revises: 1cb340fbc71b
Create Date: 2026-04-26 19:43:43.620614

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f15e7802745c"
down_revision: Union[str, Sequence[str], None] = "1cb340fbc71b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ── users ──────────────────────────────────────────────────────────────
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sub_status",
                sa.Text(),
                nullable=False,
                server_default="free",
            )
        )
        batch_op.add_column(
            sa.Column("sub_stripe_customer_id", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("sub_stripe_subscription_id", sa.Text(), nullable=True)
        )
        batch_op.add_column(sa.Column("sub_price_id", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("sub_current_period_end", sa.Integer(), nullable=True)
        )

    # ── organizations ──────────────────────────────────────────────────────
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sub_status",
                sa.Text(),
                nullable=False,
                server_default="free",
            )
        )
        batch_op.add_column(
            sa.Column("sub_stripe_customer_id", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("sub_stripe_subscription_id", sa.Text(), nullable=True)
        )
        batch_op.add_column(sa.Column("sub_price_id", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("sub_current_period_end", sa.Integer(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("sub_status")
        batch_op.drop_column("sub_stripe_customer_id")
        batch_op.drop_column("sub_stripe_subscription_id")
        batch_op.drop_column("sub_price_id")
        batch_op.drop_column("sub_current_period_end")

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_column("sub_status")
        batch_op.drop_column("sub_stripe_customer_id")
        batch_op.drop_column("sub_stripe_subscription_id")
        batch_op.drop_column("sub_price_id")
        batch_op.drop_column("sub_current_period_end")
