"""rename linkedin_post_urn to platform_post_id

Revision ID: 0002
Revises: 0001_create_social_tables
Create Date: 2026-08-04 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001_create_social_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "social_publish_records",
        "linkedin_post_urn",
        new_column_name="platform_post_id",
    )


def downgrade() -> None:
    op.alter_column(
        "social_publish_records",
        "platform_post_id",
        new_column_name="linkedin_post_urn",
    )