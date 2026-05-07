"""initial products and chunks tables

Revision ID: 0001
Revises:
Create Date: 2026-05-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("nafdac_number", sa.String(64)),
        sa.Column("product_name", sa.Text, nullable=False),
        sa.Column("applicant_name", sa.Text),
        sa.Column("manufacturer", sa.Text),
        sa.Column("category", sa.Text),
        sa.Column("issue_date", sa.Date),
        sa.Column("expiry_date", sa.Date),
        sa.Column("raw", JSONB, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_products_source", "products", ["source"])
    op.create_index("ix_products_nafdac_number", "products", ["nafdac_number"])
    op.create_index("ix_products_content_hash", "products", ["content_hash"])
    op.create_index("ix_products_source_nafdac", "products", ["source", "nafdac_number"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column(
            "product_id",
            sa.String(128),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedded_at", sa.DateTime(timezone=True)),
        sa.Column("qdrant_point_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chunks_product_id", "chunks", ["product_id"])
    op.create_index("ix_chunks_content_hash", "chunks", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_chunks_content_hash", table_name="chunks")
    op.drop_index("ix_chunks_product_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("ix_products_source_nafdac", table_name="products")
    op.drop_index("ix_products_content_hash", table_name="products")
    op.drop_index("ix_products_nafdac_number", table_name="products")
    op.drop_index("ix_products_source", table_name="products")
    op.drop_table("products")
