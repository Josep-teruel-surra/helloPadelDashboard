"""inventory

Revision ID: e610c55b0892
Revises: e27ca2c8c42e
Create Date: 2026-10-29 12:36:30.266375

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e610c55b0892"
down_revision: str | None = "e27ca2c8c42e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column(
            "category",
            sa.Enum("clothing", "book", "other", name="product_category"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        sa.UniqueConstraint("name", name=op.f("uq_products_name")),
    )
    op.create_table(
        "product_variants",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=60), nullable=False),
        sa.Column("sku", sa.String(length=60), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "low_stock_threshold >= 0", name=op.f("ck_product_variants_threshold_not_negative")
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_variants_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_variants")),
        sa.UniqueConstraint("product_id", "label", name="uq_product_variants_product_id_label"),
        sa.UniqueConstraint("sku", name=op.f("uq_product_variants_sku")),
    )
    op.create_table(
        "stock_movements",
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("restock", "shipment", "adjustment", "return", name="stock_movement_kind"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "(kind IN ('restock', 'return') AND quantity > 0) OR (kind = 'shipment' AND quantity < 0) OR kind = 'adjustment'",
            name=op.f("ck_stock_movements_quantity_sign_matches_kind"),
        ),
        sa.CheckConstraint("quantity <> 0", name=op.f("ck_stock_movements_quantity_not_zero")),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_stock_movements_created_by_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            name=op.f("fk_stock_movements_variant_id_product_variants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_movements")),
    )
    op.create_index(
        "ix_stock_movements_variant_id_created_at",
        "stock_movements",
        ["variant_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_variant_id_created_at", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_table("product_variants")
    op.drop_table("products")
    sa.Enum(name="stock_movement_kind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="product_category").drop(op.get_bind(), checkfirst=True)
