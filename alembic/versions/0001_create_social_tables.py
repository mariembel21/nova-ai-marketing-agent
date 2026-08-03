"""create social tables

Revision ID: 0001_create_social_tables
Revises:
Create Date: 2026-07-26 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_social_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_uuid", sa.String(length=36), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_uuid"),
        sa.UniqueConstraint("platform", "external_id", name="uq_social_accounts_platform_external_id"),
    )
    op.create_index(op.f("ix_social_accounts_account_uuid"), "social_accounts", ["account_uuid"], unique=True)
    op.create_index(op.f("ix_social_accounts_platform"), "social_accounts", ["platform"], unique=False)

    op.create_table(
        "social_publish_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_uuid", sa.String(length=36), nullable=False),
        sa.Column("social_account_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.Text(), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("linkedin_post_urn", sa.String(length=255), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["social_account_id"], ["social_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_uuid"),
    )
    op.create_index(op.f("ix_social_publish_records_record_uuid"), "social_publish_records", ["record_uuid"], unique=True)
    op.create_index(op.f("ix_social_publish_records_social_account_id"), "social_publish_records", ["social_account_id"], unique=False)
    op.create_index(op.f("ix_social_publish_records_platform"), "social_publish_records", ["platform"], unique=False)
    op.create_index(op.f("ix_social_publish_records_status"), "social_publish_records", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_social_publish_records_status"), table_name="social_publish_records")
    op.drop_index(op.f("ix_social_publish_records_platform"), table_name="social_publish_records")
    op.drop_index(op.f("ix_social_publish_records_social_account_id"), table_name="social_publish_records")
    op.drop_index(op.f("ix_social_publish_records_record_uuid"), table_name="social_publish_records")
    op.drop_table("social_publish_records")

    op.drop_index(op.f("ix_social_accounts_platform"), table_name="social_accounts")
    op.drop_index(op.f("ix_social_accounts_account_uuid"), table_name="social_accounts")
    op.drop_table("social_accounts")
