"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-02 11:48:10.255862
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "banks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("discount_value", sa.Double(), nullable=True),
        sa.Column("discount_type", sa.String(length=16), nullable=True),
        sa.Column("card_types", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("bank_category", sa.String(length=128), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bank_id"],
            ["banks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id", "external_id"),
    )
    op.create_index(op.f("ix_promotions_bank_id"), "promotions", ["bank_id"], unique=False)
    op.create_index(op.f("ix_promotions_category"), "promotions", ["category"], unique=False)
    op.create_index(op.f("ix_promotions_is_active"), "promotions", ["is_active"], unique=False)
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("offers_found", sa.Integer(), nullable=False),
        sa.Column("offers_new", sa.Integer(), nullable=False),
        sa.Column("offers_closed", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("raw_path", sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(
            ["bank_id"],
            ["banks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scrape_runs_bank_id"), "scrape_runs", ["bank_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scrape_runs_bank_id"), table_name="scrape_runs")
    op.drop_table("scrape_runs")
    op.drop_index(op.f("ix_promotions_is_active"), table_name="promotions")
    op.drop_index(op.f("ix_promotions_category"), table_name="promotions")
    op.drop_index(op.f("ix_promotions_bank_id"), table_name="promotions")
    op.drop_table("promotions")
    op.drop_table("banks")
