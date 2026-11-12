"""add application activity history

Revision ID: 20261111_activities
Revises: 20261111
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261111_activities"
down_revision: Union[str, Sequence[str], None] = "20261111"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name="fk_application_activities_job_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_application_activities_job_id",
        "application_activities",
        ["job_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_activities_job_id",
        table_name="application_activities",
    )
    op.drop_table("application_activities")
