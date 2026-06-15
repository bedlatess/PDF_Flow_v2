"""Add tool usage quotas and usage logs."""

from alembic import op
import sqlalchemy as sa


revision = "tool_usage_limits"
down_revision = "nullable_processing_job_user"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("feature_flags", sa.Column("free_daily_limit", sa.Integer(), nullable=True))
    op.add_column("feature_flags", sa.Column("free_max_file_size_mb", sa.Integer(), nullable=True))
    op.add_column("feature_flags", sa.Column("free_batch_file_limit", sa.Integer(), nullable=True))
    op.add_column("feature_flags", sa.Column("pro_daily_limit", sa.Integer(), nullable=True))
    op.add_column("feature_flags", sa.Column("pro_max_file_size_mb", sa.Integer(), nullable=True))
    op.add_column("feature_flags", sa.Column("pro_batch_file_limit", sa.Integer(), nullable=True))
    op.add_column(
        "feature_flags",
        sa.Column("pro_unlimited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("feature_flags", "pro_unlimited", server_default=None)

    op.create_table(
        "tool_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("anonymous_key", sa.String(), nullable=True),
        sa.Column("tool_type", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tool_usage_user_tool_created", "tool_usage_logs", ["user_id", "tool_type", "created_at"])
    op.create_index("idx_tool_usage_anon_tool_created", "tool_usage_logs", ["anonymous_key", "tool_type", "created_at"])
    op.create_index("idx_tool_usage_job", "tool_usage_logs", ["job_id"])
    op.create_index(op.f("ix_tool_usage_logs_id"), "tool_usage_logs", ["id"])
    op.create_index(op.f("ix_tool_usage_logs_created_at"), "tool_usage_logs", ["created_at"])

    op.execute(
        """
        UPDATE feature_flags
        SET
            free_daily_limit = COALESCE(free_daily_limit, 10),
            free_max_file_size_mb = COALESCE(free_max_file_size_mb, 25),
            free_batch_file_limit = COALESCE(free_batch_file_limit, 5),
            pro_daily_limit = COALESCE(pro_daily_limit, 200),
            pro_max_file_size_mb = COALESCE(pro_max_file_size_mb, 200),
            pro_batch_file_limit = COALESCE(pro_batch_file_limit, 25),
            pro_unlimited = COALESCE(pro_unlimited, false)
        """
    )


def downgrade():
    op.drop_index(op.f("ix_tool_usage_logs_created_at"), table_name="tool_usage_logs")
    op.drop_index(op.f("ix_tool_usage_logs_id"), table_name="tool_usage_logs")
    op.drop_index("idx_tool_usage_job", table_name="tool_usage_logs")
    op.drop_index("idx_tool_usage_anon_tool_created", table_name="tool_usage_logs")
    op.drop_index("idx_tool_usage_user_tool_created", table_name="tool_usage_logs")
    op.drop_table("tool_usage_logs")

    op.drop_column("feature_flags", "pro_unlimited")
    op.drop_column("feature_flags", "pro_batch_file_limit")
    op.drop_column("feature_flags", "pro_max_file_size_mb")
    op.drop_column("feature_flags", "pro_daily_limit")
    op.drop_column("feature_flags", "free_batch_file_limit")
    op.drop_column("feature_flags", "free_max_file_size_mb")
    op.drop_column("feature_flags", "free_daily_limit")
