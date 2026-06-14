"""Add admin-managed pricing plans."""

from alembic import op
import sqlalchemy as sa


revision = "add_pricing_plans"
down_revision = "ff_public_visibility"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pricing_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_key", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("price_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("display_price", sa.String(), nullable=False, server_default=""),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("billing_interval", sa.String(), nullable=False, server_default="none"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("provider_mappings_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("highlighted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_key"),
    )
    op.create_index("idx_pricing_plan_key", "pricing_plans", ["plan_key"])
    op.create_index("idx_pricing_plan_public", "pricing_plans", ["is_public"])
    op.create_index("idx_pricing_plan_sort", "pricing_plans", ["sort_order"])


def downgrade():
    op.drop_index("idx_pricing_plan_sort", table_name="pricing_plans")
    op.drop_index("idx_pricing_plan_public", table_name="pricing_plans")
    op.drop_index("idx_pricing_plan_key", table_name="pricing_plans")
    op.drop_table("pricing_plans")
