"""Add admin-managed service provider configs."""

from alembic import op
import sqlalchemy as sa


revision = "add_service_provider_configs"
down_revision = "add_pricing_plans"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_provider_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_key", sa.String(), nullable=False),
        sa.Column("provider_key", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("public_config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("encrypted_secret_json", sa.Text(), nullable=True),
        sa.Column("secret_fingerprint_json", sa.Text(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "service_key",
            "provider_key",
            name="uq_service_provider_config_service_provider",
        ),
    )
    op.create_index("ix_service_provider_configs_id", "service_provider_configs", ["id"])
    op.create_index(
        "idx_service_provider_config_service",
        "service_provider_configs",
        ["service_key"],
    )
    op.create_index(
        "idx_service_provider_config_provider",
        "service_provider_configs",
        ["provider_key"],
    )
    op.create_index(
        "idx_service_provider_config_enabled",
        "service_provider_configs",
        ["enabled"],
    )


def downgrade():
    op.drop_index("idx_service_provider_config_enabled", table_name="service_provider_configs")
    op.drop_index("idx_service_provider_config_provider", table_name="service_provider_configs")
    op.drop_index("idx_service_provider_config_service", table_name="service_provider_configs")
    op.drop_index("ix_service_provider_configs_id", table_name="service_provider_configs")
    op.drop_table("service_provider_configs")
