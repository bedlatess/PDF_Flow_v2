"""Add public visibility to feature flags."""

from alembic import op
import sqlalchemy as sa


revision = "ff_public_visibility"
down_revision = "add_payment_provider_configs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "feature_flags",
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("idx_feature_flag_public", "feature_flags", ["is_public"])
    op.alter_column("feature_flags", "is_public", server_default=None)


def downgrade():
    op.drop_index("idx_feature_flag_public", table_name="feature_flags")
    op.drop_column("feature_flags", "is_public")
