"""Allow anonymous processing jobs."""

from alembic import op
import sqlalchemy as sa


revision = "nullable_processing_job_user"
down_revision = "add_service_provider_configs"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "processing_jobs",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "processing_jobs",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
