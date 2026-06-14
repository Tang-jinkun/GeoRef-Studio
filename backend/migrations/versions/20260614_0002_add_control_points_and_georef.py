"""add control points and georef fields

Revision ID: 20260614_0002
Revises: 20260614_0001
Create Date: 2026-06-14 18:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260614_0002"
down_revision = "20260614_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project", sa.Column("transform_matrix", sa.JSON(), nullable=True))
    op.add_column("project", sa.Column("rms_error", sa.Float(), nullable=True))
    op.add_column("project", sa.Column("georef_time", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "control_point",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pixel_x", sa.Float(), nullable=False),
        sa.Column("pixel_y", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("residual", sa.Float(), nullable=True),
        sa.Column("delta_x", sa.Float(), nullable=True),
        sa.Column("delta_y", sa.Float(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("create_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_control_point_project_id", "control_point", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_control_point_project_id", table_name="control_point")
    op.drop_table("control_point")
    op.drop_column("project", "georef_time")
    op.drop_column("project", "rms_error")
    op.drop_column("project", "transform_matrix")
