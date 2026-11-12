"""harden reminder processing and notification center

Revision ID: 20261112_reminder_hardening
Revises: 20261112_phase2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261112_reminder_hardening"
down_revision: Union[str, Sequence[str], None] = "20261112_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("interview_id", sa.Integer(), nullable=True))
    op.add_column("reminders", sa.Column("status", sa.String(20), nullable=True))
    op.add_column("reminders", sa.Column("attempt_count", sa.Integer(), nullable=True))
    op.add_column("reminders", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reminders", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("reminders", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE reminders SET status = CASE WHEN completed THEN 'completed' ELSE 'pending' END")
    op.execute("UPDATE reminders SET attempt_count = 0 WHERE attempt_count IS NULL")
    op.alter_column("reminders", "status", nullable=False, server_default="pending")
    op.alter_column("reminders", "attempt_count", nullable=False, server_default="0")
    op.drop_column("reminders", "completed")
    op.create_foreign_key(
        "fk_reminders_interview_id",
        "reminders",
        "interviews",
        ["interview_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_reminders_interview_id", "reminders", ["interview_id"])
    op.create_index("ix_reminders_status", "reminders", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reminders_status", table_name="reminders")
    op.drop_index("ix_reminders_interview_id", table_name="reminders")
    op.drop_constraint("fk_reminders_interview_id", "reminders", type_="foreignkey")
    op.add_column("reminders", sa.Column("completed", sa.Boolean(), nullable=True))
    op.execute("UPDATE reminders SET completed = CASE WHEN status = 'completed' THEN true ELSE false END")
    op.alter_column("reminders", "completed", nullable=False, server_default=sa.false())
    op.drop_column("reminders", "processed_at")
    op.drop_column("reminders", "last_error")
    op.drop_column("reminders", "processing_started_at")
    op.drop_column("reminders", "attempt_count")
    op.drop_column("reminders", "status")
    op.drop_column("reminders", "interview_id")
