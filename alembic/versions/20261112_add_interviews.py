"""add interviews

Revision ID: 20261112_interviews
Revises: 20261111_activities
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261112_interviews"
down_revision: Union[str, Sequence[str], None] = "20261111_activities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("interview_type", sa.String(length=40), nullable=False),
        sa.Column("interview_stage", sa.String(length=40), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("meeting_link", sa.String(length=500), nullable=True),
        sa.Column("interviewer_name", sa.String(length=150), nullable=True),
        sa.Column("interviewer_email", sa.String(length=255), nullable=True),
        sa.Column("preparation_notes", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_interviews_user_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name="fk_interviews_job_id", ondelete="CASCADE"
        ),
    )
    op.create_index("ix_interviews_user_id", "interviews", ["user_id"])
    op.create_index("ix_interviews_job_id", "interviews", ["job_id"])
    op.create_index("ix_interviews_scheduled_at", "interviews", ["scheduled_at"])
    op.create_index("ix_interviews_outcome", "interviews", ["outcome"])


def downgrade() -> None:
    op.drop_index("ix_interviews_outcome", table_name="interviews")
    op.drop_index("ix_interviews_scheduled_at", table_name="interviews")
    op.drop_index("ix_interviews_job_id", table_name="interviews")
    op.drop_index("ix_interviews_user_id", table_name="interviews")
    op.drop_table("interviews")
