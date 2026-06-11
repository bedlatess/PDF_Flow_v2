"""Add API error logs

Revision ID: add_api_error_logs
Revises: add_feedback_reports
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa


revision = "add_api_error_logs"
down_revision = "add_feedback_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_error_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("query_string", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("traceback_summary", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_error_logs_id", "api_error_logs", ["id"])
    op.create_index("ix_api_error_logs_created_at", "api_error_logs", ["created_at"])
    op.create_index("idx_api_error_status", "api_error_logs", ["status_code"])
    op.create_index("idx_api_error_created", "api_error_logs", ["created_at"])
    op.create_index("idx_api_error_path", "api_error_logs", ["path"])


def downgrade():
    op.drop_index("idx_api_error_path", table_name="api_error_logs")
    op.drop_index("idx_api_error_created", table_name="api_error_logs")
    op.drop_index("idx_api_error_status", table_name="api_error_logs")
    op.drop_index("ix_api_error_logs_created_at", table_name="api_error_logs")
    op.drop_index("ix_api_error_logs_id", table_name="api_error_logs")
    op.drop_table("api_error_logs")
