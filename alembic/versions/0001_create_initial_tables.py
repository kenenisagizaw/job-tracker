"""create initial job tables

Revision ID: 0001
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("company", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("salary", sa.Float(), nullable=True),
        sa.Column(
            "job_type",
            sa.String(length=50),
            nullable=False,
            server_default="Full-time",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="saved",
        ),
        sa.CheckConstraint(
            "salary IS NULL OR salary > 0",
            name="check_salary_positive",
        ),
        sa.CheckConstraint(
            "status IN ('saved', 'applied', 'interview', 'offer', 'rejected')",
            name="check_job_status",
        ),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_jobs_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("companies")
