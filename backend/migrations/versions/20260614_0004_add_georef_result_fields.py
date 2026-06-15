"""add georef result fields

Revision ID: 20260614_0004
Revises: 20260614_0003
Create Date: 2026-06-15 11:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260614_0004"
down_revision = "20260614_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project", sa.Column("transform_type", sa.String(length=32), nullable=True))
    op.add_column("project", sa.Column("target_crs", sa.String(length=32), nullable=True))
    op.add_column("project", sa.Column("rms_meters", sa.Float(), nullable=True))
    op.add_column("project", sa.Column("georef_result_path", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("project", "georef_result_path")
    op.drop_column("project", "rms_meters")
    op.drop_column("project", "target_crs")
    op.drop_column("project", "transform_type")
