"""Add admin-managed payment provider configs."""

from alembic import op
import sqlalchemy as sa


revision = "add_payment_provider_configs"
down_revision = "add_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_provider_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_key", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("public_config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("encrypted_secret_json", sa.Text(), nullable=True),
        sa.Column("secret_fingerprint_json", sa.Text(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_key"),
    )
    op.create_index("ix_payment_provider_configs_id", "payment_provider_configs", ["id"])
    op.create_index(
        "idx_payment_provider_config_key",
        "payment_provider_configs",
        ["provider_key"],
    )
    op.create_index(
        "idx_payment_provider_config_enabled",
        "payment_provider_configs",
        ["enabled"],
    )


def downgrade():
    op.drop_index("idx_payment_provider_config_enabled", table_name="payment_provider_configs")
    op.drop_index("idx_payment_provider_config_key", table_name="payment_provider_configs")
    op.drop_index("ix_payment_provider_configs_id", table_name="payment_provider_configs")
    op.drop_table("payment_provider_configs")
