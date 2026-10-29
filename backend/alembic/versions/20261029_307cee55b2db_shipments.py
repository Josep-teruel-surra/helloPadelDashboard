"""shipments

Revision ID: 307cee55b2db
Revises: e610c55b0892
Create Date: 2026-10-29 12:43:07.859023

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "307cee55b2db"
down_revision: str | None = "e610c55b0892"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shipments",
        sa.Column("number", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("campus_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "preparing", "shipped", "delivered", "incident", "cancelled", name="shipment_status"
            ),
            nullable=False,
        ),
        sa.Column("carrier", sa.String(length=80), nullable=True),
        sa.Column("tracking_number", sa.String(length=120), nullable=True),
        sa.Column("tracking_url", sa.String(length=500), nullable=True),
        sa.Column("needed_by", sa.Date(), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("cost_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("cost_currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("notes_md", sa.Text(), server_default="", nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
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
        sa.CheckConstraint("cost_amount >= 0", name=op.f("ck_shipments_cost_not_negative")),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name=op.f("fk_shipments_assignee_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["campus_id"], ["campuses.id"], name=op.f("fk_shipments_campus_id_campuses")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_shipments_created_by_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name=op.f("fk_shipments_event_id_events")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipments")),
        sa.UniqueConstraint("number", name=op.f("uq_shipments_number")),
    )
    op.create_index("ix_shipments_campus_id", "shipments", ["campus_id"], unique=False)
    op.create_index("ix_shipments_event_id", "shipments", ["event_id"], unique=False)
    op.create_index("ix_shipments_status", "shipments", ["status"], unique=False)
    op.create_table(
        "shipment_items",
        sa.Column("shipment_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_shipment_items_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["shipment_id"],
            ["shipments.id"],
            name=op.f("fk_shipment_items_shipment_id_shipments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            name=op.f("fk_shipment_items_variant_id_product_variants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipment_items")),
        sa.UniqueConstraint("shipment_id", "variant_id", name="uq_shipment_items_shipment_variant"),
    )
    op.create_index("ix_shipment_items_variant_id", "shipment_items", ["variant_id"], unique=False)
    op.add_column("stock_movements", sa.Column("shipment_id", sa.Uuid(), nullable=True))
    op.create_index(
        "ix_stock_movements_shipment_id", "stock_movements", ["shipment_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_stock_movements_shipment_id_shipments"),
        "stock_movements",
        "shipments",
        ["shipment_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_stock_movements_shipment_id_shipments"), "stock_movements", type_="foreignkey"
    )
    op.drop_index("ix_stock_movements_shipment_id", table_name="stock_movements")
    op.drop_column("stock_movements", "shipment_id")
    op.drop_index("ix_shipment_items_variant_id", table_name="shipment_items")
    op.drop_table("shipment_items")
    op.drop_index("ix_shipments_status", table_name="shipments")
    op.drop_index("ix_shipments_event_id", table_name="shipments")
    op.drop_index("ix_shipments_campus_id", table_name="shipments")
    op.drop_table("shipments")
    sa.Enum(name="shipment_status").drop(op.get_bind(), checkfirst=True)
