"""Add one-time password reset tokens."""

from alembic import op
import sqlalchemy as sa


revision = "add_password_reset_tokens"
down_revision = "add_payment_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="user_request"),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_reset_tokens_id", "password_reset_tokens", ["id"])
    op.create_index(
        "ix_password_reset_tokens_expires_at",
        "password_reset_tokens",
        ["expires_at"],
    )
    op.create_index(
        "idx_password_reset_token_hash",
        "password_reset_tokens",
        ["token_hash"],
    )
    op.create_index(
        "idx_password_reset_token_user",
        "password_reset_tokens",
        ["user_id"],
    )
    op.create_index(
        "idx_password_reset_token_expires",
        "password_reset_tokens",
        ["expires_at"],
    )


def downgrade():
    op.drop_index("idx_password_reset_token_expires", table_name="password_reset_tokens")
    op.drop_index("idx_password_reset_token_user", table_name="password_reset_tokens")
    op.drop_index("idx_password_reset_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_expires_at", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
