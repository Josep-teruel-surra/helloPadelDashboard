"""students and certifications

Revision ID: 28bf5095bd2a
Revises: 307cee55b2db
Create Date: 2026-10-29 13:29:52.723774

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "28bf5095bd2a"
down_revision: str | None = "307cee55b2db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "certifications",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("has_test", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("has_video", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("has_test OR has_video", name=op.f("ck_certifications_has_some_part")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_certifications")),
        sa.UniqueConstraint("name", name=op.f("uq_certifications_name")),
    )
    op.create_table(
        "students",
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("campus_id", sa.Uuid(), nullable=True),
        sa.Column("notes_md", sa.Text(), server_default="", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campus_id"],
            ["campuses.id"],
            name=op.f("fk_students_campus_id_campuses"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_students")),
        sa.UniqueConstraint("email", name=op.f("uq_students_email")),
    )
    op.create_index("ix_students_full_name", "students", ["full_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_students_full_name", table_name="students")
    op.drop_table("students")
    op.drop_table("certifications")
