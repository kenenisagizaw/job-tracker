"""add job deadlines and reminder tracking

Revision ID: 20261107
Revises: 8c1f2e7a4b91
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261107"
down_revision: Union[str, Sequence[str], None] = "8c1f2e7a4b91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("deadline", sa.Date(), nullable=True))
    op.add_column(
        "jobs",
        sa.Column("deadline_reminder_sent_for", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "deadline_reminder_sent_for")
    op.drop_column("jobs", "deadline")
