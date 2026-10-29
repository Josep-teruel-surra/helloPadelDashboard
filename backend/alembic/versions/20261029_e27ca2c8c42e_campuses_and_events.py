"""campuses and events

Revision ID: e27ca2c8c42e
Revises: 911540e2608b
Create Date: 2026-10-29 12:06:46.152190

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e27ca2c8c42e"
down_revision: str | None = "911540e2608b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campuses",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("partner", sa.String(length=160), nullable=True),
        sa.Column("coordinator_name", sa.String(length=120), nullable=True),
        sa.Column("coordinator_email", sa.String(length=255), nullable=True),
        sa.Column("coordinator_phone", sa.String(length=40), nullable=True),
        sa.Column("notes_md", sa.Text(), server_default="", nullable=False),
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
        sa.Column("ship_recipient", sa.String(length=160), nullable=True),
        sa.Column("ship_line1", sa.String(length=200), nullable=True),
        sa.Column("ship_line2", sa.String(length=200), nullable=True),
        sa.Column("ship_postal_code", sa.String(length=20), nullable=True),
        sa.Column("ship_city", sa.String(length=120), nullable=True),
        sa.Column("ship_region", sa.String(length=120), nullable=True),
        sa.Column("ship_country_code", sa.String(length=2), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campuses")),
        sa.UniqueConstraint("name", name=op.f("uq_campuses_name")),
    )
    op.create_index("ix_campuses_country_code", "campuses", ["country_code"], unique=False)
    op.create_table(
        "events",
        sa.Column("campus_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("campus", "coach_training", "exam", "other", name="event_kind"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("planned", "confirmed", "done", "cancelled", name="event_status"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("responsible_id", sa.Uuid(), nullable=True),
        sa.Column("expected_participants", sa.Integer(), nullable=True),
        sa.Column("notes_md", sa.Text(), server_default="", nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("material_todo_id", sa.Uuid(), nullable=True),
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
        sa.CheckConstraint("end_date >= start_date", name=op.f("ck_events_dates_in_order")),
        sa.CheckConstraint(
            "expected_participants >= 0", name=op.f("ck_events_participants_not_negative")
        ),
        sa.ForeignKeyConstraint(
            ["campus_id"], ["campuses.id"], name=op.f("fk_events_campus_id_campuses")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_events_created_by_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["responsible_id"],
            ["users.id"],
            name=op.f("fk_events_responsible_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(
        "ix_events_campus_id_start_date", "events", ["campus_id", "start_date"], unique=False
    )
    op.create_index("ix_events_start_date", "events", ["start_date"], unique=False)
    # Explícita: Alembic omite dentro de create_table las FK marcadas con use_alter.
    op.create_foreign_key(
        op.f("fk_events_material_todo_id_todos"),
        "events",
        "todos",
        ["material_todo_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("notes", sa.Column("event_id", sa.Uuid(), nullable=True))
    op.create_index("ix_notes_event_id", "notes", ["event_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_notes_event_id_events"),
        "notes",
        "events",
        ["event_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("todos", sa.Column("event_id", sa.Uuid(), nullable=True))
    op.create_index("ix_todos_event_id", "todos", ["event_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_todos_event_id_events"),
        "todos",
        "events",
        ["event_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_todos_event_id_events"), "todos", type_="foreignkey")
    op.drop_index("ix_todos_event_id", table_name="todos")
    op.drop_column("todos", "event_id")
    op.drop_constraint(op.f("fk_notes_event_id_events"), "notes", type_="foreignkey")
    op.drop_index("ix_notes_event_id", table_name="notes")
    op.drop_column("notes", "event_id")
    op.drop_constraint(op.f("fk_events_material_todo_id_todos"), "events", type_="foreignkey")
    op.drop_index("ix_events_start_date", table_name="events")
    op.drop_index("ix_events_campus_id_start_date", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_campuses_country_code", table_name="campuses")
    op.drop_table("campuses")
    sa.Enum(name="event_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="event_kind").drop(op.get_bind(), checkfirst=True)
