"""scope companies to their owning user

Revision ID: 20261111
Revises: 20261107
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261111"
down_revision: Union[str, Sequence[str], None] = "20261107"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("owner_id", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "ALTER TABLE companies "
            "DROP CONSTRAINT IF EXISTS companies_name_key"
        )
    )

    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                company_record RECORD;
                owner_record RECORD;
                primary_owner INTEGER;
                new_company_id INTEGER;
            BEGIN
                FOR company_record IN
                    SELECT id, name FROM companies ORDER BY id
                LOOP
                    SELECT MIN(owner_id)
                    INTO primary_owner
                    FROM jobs
                    WHERE company_id = company_record.id;

                    IF primary_owner IS NULL THEN
                        SELECT id
                        INTO primary_owner
                        FROM users
                        ORDER BY id
                        LIMIT 1;
                        IF primary_owner IS NULL THEN
                            RAISE EXCEPTION
                                'Cannot scope existing companies without an existing user';
                        END IF;
                    END IF;

                    UPDATE companies
                    SET owner_id = primary_owner
                    WHERE id = company_record.id;

                    FOR owner_record IN
                        SELECT DISTINCT owner_id
                        FROM jobs
                        WHERE company_id = company_record.id
                          AND owner_id <> primary_owner
                        ORDER BY owner_id
                    LOOP
                        INSERT INTO companies (name, owner_id)
                        VALUES (company_record.name, owner_record.owner_id)
                        RETURNING id INTO new_company_id;

                        UPDATE jobs
                        SET company_id = new_company_id
                        WHERE company_id = company_record.id
                          AND owner_id = owner_record.owner_id;
                    END LOOP;
                END LOOP;
            END $$;
            """
        )
    )

    op.alter_column("companies", "owner_id", nullable=False)
    op.create_index(
        "ix_companies_owner_id",
        "companies",
        ["owner_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_companies_owner_id_users",
        "companies",
        "users",
        ["owner_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_companies_owner_name",
        "companies",
        ["owner_id", "name"],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                company_record RECORD;
            BEGIN
                FOR company_record IN
                    SELECT duplicate.id, MIN(canonical.id) AS canonical_id
                    FROM companies AS duplicate
                    JOIN companies AS canonical
                      ON canonical.name = duplicate.name
                     AND canonical.id < duplicate.id
                    GROUP BY duplicate.id
                LOOP
                    UPDATE jobs
                    SET company_id = company_record.canonical_id
                    WHERE company_id = company_record.id;

                    DELETE FROM companies
                    WHERE id = company_record.id;
                END LOOP;
            END $$;
            """
        )
    )

    op.drop_constraint("uq_companies_owner_name", "companies", type_="unique")
    op.drop_constraint(
        "fk_companies_owner_id_users",
        "companies",
        type_="foreignkey",
    )
    op.drop_index("ix_companies_owner_id", table_name="companies")
    op.drop_column("companies", "owner_id")
    op.create_unique_constraint(
        "companies_name_key",
        "companies",
        ["name"],
    )
