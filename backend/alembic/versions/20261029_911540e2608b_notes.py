"""notes

Revision ID: 911540e2608b
Revises: 7c234f045992
Create Date: 2026-10-29 10:28:07.560558

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "911540e2608b"
down_revision: str | None = "7c234f045992"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notes",
        # El tipo 'scope' ya lo crea la migración de todos.
        sa.Column(
            "scope",
            postgresql.ENUM("personal", "company", name="scope", create_type=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content_md", sa.Text(), server_default="", nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name=op.f("fk_notes_author_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notes")),
    )
    op.create_index("ix_notes_author_id_scope", "notes", ["author_id", "scope"], unique=False)
    op.create_index("ix_notes_scope_updated_at", "notes", ["scope", "updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notes_scope_updated_at", table_name="notes")
    op.drop_index("ix_notes_author_id_scope", table_name="notes")
    op.drop_table("notes")
