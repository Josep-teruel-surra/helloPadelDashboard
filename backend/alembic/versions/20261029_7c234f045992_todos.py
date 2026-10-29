"""todos

Revision ID: 7c234f045992
Revises: 6ff0bd85d3b8
Create Date: 2026-10-29 10:19:00.267635

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7c234f045992"
down_revision: str | None = "6ff0bd85d3b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "todos",
        sa.Column("scope", sa.Enum("personal", "company", name="scope"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
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
        sa.CheckConstraint(
            "scope = 'company' OR assignee_id IS NULL",
            name=op.f("ck_todos_personal_without_assignee"),
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name=op.f("fk_todos_assignee_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_todos_created_by_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_todos")),
    )
    op.create_index("ix_todos_assignee_id", "todos", ["assignee_id"], unique=False)
    op.create_index(
        "ix_todos_created_by_id_scope", "todos", ["created_by_id", "scope"], unique=False
    )
    op.create_index("ix_todos_scope_is_done", "todos", ["scope", "is_done"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_todos_scope_is_done", table_name="todos")
    op.drop_index("ix_todos_created_by_id_scope", table_name="todos")
    op.drop_index("ix_todos_assignee_id", table_name="todos")
    op.drop_table("todos")
    sa.Enum(name="scope").drop(op.get_bind(), checkfirst=True)
