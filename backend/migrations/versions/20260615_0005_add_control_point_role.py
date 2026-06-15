"""add control point role

Revision ID: 20260615_0005
Revises: 20260614_0004
Create Date: 2026-06-15 16:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260615_0005"
down_revision = "20260614_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "control_point",
        sa.Column("role", sa.String(length=16), nullable=False, server_default="fit"),
    )
    op.alter_column("control_point", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("control_point", "role")
