"""add users and job ownership

Revision ID: 8c1f2e7a4b91
Revises: 2ffa4a8d0023
"""
from typing import Sequence, Union
import os

from alembic import context, op
from pwdlib import PasswordHash
import sqlalchemy as sa


revision: str = "8c1f2e7a4b91"
down_revision: Union[str, Sequence[str], None] = "2ffa4a8d0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.add_column("jobs", sa.Column("owner_id", sa.Integer(), nullable=True))

    if context.is_offline_mode():
        op.execute(
            sa.text(
                """
                DO $$
                DECLARE owner_id_value INTEGER;
                BEGIN
                    IF EXISTS (SELECT 1 FROM jobs) THEN
                        SELECT id INTO owner_id_value
                        FROM users ORDER BY id LIMIT 1;
                        IF owner_id_value IS NULL THEN
                            RAISE EXCEPTION
                                'Existing jobs require MIGRATION_OWNER_EMAIL '
                                'and MIGRATION_OWNER_PASSWORD during online migration';
                        END IF;
                        UPDATE jobs SET owner_id = owner_id_value;
                    END IF;
                END $$;
                """
            )
        )
    else:
        connection = op.get_bind()
        existing_jobs = connection.execute(
            sa.text("SELECT COUNT(*) FROM jobs")
        ).scalar_one()
        if existing_jobs:
            owner_id = connection.execute(
                sa.text("SELECT id FROM users ORDER BY id LIMIT 1")
            ).scalar_one_or_none()
            if owner_id is None:
                email = os.getenv("MIGRATION_OWNER_EMAIL")
                password = os.getenv("MIGRATION_OWNER_PASSWORD")
                if not email or not password:
                    raise RuntimeError(
                        "Existing jobs need an owner. Set MIGRATION_OWNER_EMAIL "
                        "and MIGRATION_OWNER_PASSWORD, then rerun alembic upgrade head."
                    )
                result = connection.execute(
                    sa.text(
                        """
                        INSERT INTO users (email, hashed_password, is_active)
                        VALUES (:email, :hashed_password, true)
                        RETURNING id
                        """
                    ),
                    {
                        "email": email,
                        "hashed_password": PasswordHash.recommended().hash(password),
                    },
                )
                owner_id = result.scalar_one()
            connection.execute(
                sa.text("UPDATE jobs SET owner_id = :owner_id"),
                {"owner_id": owner_id},
            )

    op.alter_column("jobs", "owner_id", nullable=False)
    op.create_index("ix_jobs_owner_id", "jobs", ["owner_id"], unique=False)
    op.create_foreign_key(
        "fk_jobs_owner_id_users",
        "jobs",
        "users",
        ["owner_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_jobs_owner_id_users", "jobs", type_="foreignkey")
    op.drop_index("ix_jobs_owner_id", table_name="jobs")
    op.drop_column("jobs", "owner_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
