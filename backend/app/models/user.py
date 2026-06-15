"""
Database models for PDF-Flow
Following v4.0 specification: User authentication, API keys, usage tracking
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User roles"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


user_role_enum = Enum(
    UserRole,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    name="userrole",
)


class User(Base):
    """
    User model
    Implements S (Spoofing) defense: JWT authentication
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(user_role_enum, default=UserRole.FREE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # google, github
    oauth_id = Column(String, nullable=True)

    # Subscription
    stripe_customer_id = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_oauth', 'oauth_provider', 'oauth_id'),
        Index('idx_stripe_customer', 'stripe_customer_id'),
    )


class APIKey(Base):
    """
    API Key model for Enterprise users
    S (Spoofing): API Keys stored as SHA-256 hashes only
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # User-defined name for the key
    key_hash = Column(String, unique=True, nullable=False)  # SHA-256 hash
    key_prefix = Column(String, nullable=False)  # First 8 chars for identification (pdf_xxxxxxxx)

    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Rate limiting
    rate_limit = Column(Integer, default=-1, nullable=False)  # -1 = unlimited

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index('idx_key_hash', 'key_hash'),
        Index('idx_user_id', 'user_id'),
    )


class PasswordResetToken(Base):
    """One-time password reset token record.

    Plain reset tokens are only shown in links. The database stores a hash so a
    database leak cannot be used directly to reset accounts.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    source = Column(String, default="user_request", nullable=False)
    created_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    created_by_admin = relationship("User", foreign_keys=[created_by_admin_id])

    __table_args__ = (
        Index("idx_password_reset_token_hash", "token_hash"),
        Index("idx_password_reset_token_user", "user_id"),
        Index("idx_password_reset_token_expires", "expires_at"),
    )


class UsageLog(Base):
    """
    Usage tracking for rate limiting and billing
    R (Repudiation): Audit logs in read-only stream
    """
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Request info
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes

    # Processing info
    processing_time = Column(Integer, nullable=True)  # milliseconds
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(String, nullable=True)

    # Billing (for Enterprise)
    tokens_used = Column(Integer, default=0, nullable=False)
    cost = Column(Integer, default=0, nullable=False)  # cents

    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_endpoint', 'endpoint'),
    )


class ToolUsageLog(Base):
    """Conversion task creation usage used for product quotas."""
    __tablename__ = "tool_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    anonymous_key = Column(String, nullable=True)
    tool_type = Column(String, nullable=False)
    job_id = Column(String, nullable=True)
    file_size = Column(Integer, default=0, nullable=False)
    file_count = Column(Integer, default=1, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User")

    __table_args__ = (
        Index("idx_tool_usage_user_tool_created", "user_id", "tool_type", "created_at"),
        Index("idx_tool_usage_anon_tool_created", "anonymous_key", "tool_type", "created_at"),
        Index("idx_tool_usage_job", "job_id"),
    )


class ProcessingJob(Base):
    """
    Async processing job tracking
    For cloud-based OCR, Office conversion, etc.
    """
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)  # Celery task ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Job info
    job_type = Column(String, nullable=False)  # ocr, office_convert, compress, etc.
    status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed
    progress = Column(Integer, default=0, nullable=False)  # 0-100

    # File info
    input_file_name = Column(String, nullable=False)
    input_file_size = Column(Integer, nullable=False)
    output_file_url = Column(String, nullable=True)

    # Result
    result_data = Column(String, nullable=True)  # JSON string for OCR results, etc.
    error_message = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_job_id', 'job_id'),
        Index('idx_user_status', 'user_id', 'status'),
    )


class Webhook(Base):
    """
    Webhook configuration for Enterprise users
    Allows clients to receive real-time event notifications
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Webhook config
    url = Column(String, nullable=False)
    events = Column(String, nullable=False)  # JSON array of event types
    secret = Column(String, nullable=True)  # Optional secret for HMAC signature
    is_active = Column(Boolean, default=True, nullable=False)

    # Stats
    total_deliveries = Column(Integer, default=0, nullable=False)
    successful_deliveries = Column(Integer, default=0, nullable=False)
    failed_deliveries = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User")

    __table_args__ = (
        Index('idx_webhook_user', 'user_id'),
        Index('idx_webhook_active', 'is_active'),
    )


class PaymentProviderAccount(Base):
    """Provider-specific account reference for a user."""
    __tablename__ = "payment_provider_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)
    provider_customer_id = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_payment_provider_account_user_provider"),
        Index("idx_payment_provider_account_user", "user_id"),
        Index("idx_payment_provider_account_provider", "provider"),
    )


class PaymentProviderConfig(Base):
    """Admin-managed payment provider configuration.

    Secret values are encrypted with PAYMENT_CONFIG_ENCRYPTION_KEY and are never
    returned through API responses.
    """
    __tablename__ = "payment_provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider_key = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    public_config_json = Column(Text, nullable=False, default="{}")
    encrypted_secret_json = Column(Text, nullable=True)
    secret_fingerprint_json = Column(Text, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    updated_by = relationship("User")

    __table_args__ = (
        Index("idx_payment_provider_config_key", "provider_key"),
        Index("idx_payment_provider_config_enabled", "enabled"),
    )


class ServiceProviderConfig(Base):
    """Admin-managed OCR/Office/AI service provider configuration.

    Secret fields are optional for local providers, but the storage shape keeps
    the same write-only encrypted pattern used by payment provider configs.
    """
    __tablename__ = "service_provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    service_key = Column(String, nullable=False)
    provider_key = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    public_config_json = Column(Text, nullable=False, default="{}")
    encrypted_secret_json = Column(Text, nullable=True)
    secret_fingerprint_json = Column(Text, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    updated_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("service_key", "provider_key", name="uq_service_provider_config_service_provider"),
        Index("idx_service_provider_config_service", "service_key"),
        Index("idx_service_provider_config_provider", "provider_key"),
        Index("idx_service_provider_config_enabled", "enabled"),
    )


class PaymentOrder(Base):
    """Trusted payment order state across all payment providers."""
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)
    merchant_order_id = Column(String, unique=True, nullable=False)
    provider_order_id = Column(String, nullable=True)
    plan = Column(String, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(String, default="pending", nullable=False)
    checkout_url = Column(Text, nullable=True)
    qr_code_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payment_orders")
    events = relationship("PaymentEvent", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_payment_order_user", "user_id"),
        Index("idx_payment_order_provider_status", "provider", "status"),
        Index("idx_payment_order_provider_order", "provider", "provider_order_id"),
    )


class PaymentEvent(Base):
    """Immutable provider payment event ledger used for idempotency and audits."""
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)
    provider = Column(String, nullable=False)
    provider_event_id = Column(String, nullable=False)
    merchant_order_id = Column(String, nullable=False)
    provider_order_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    processing_status = Column(String, nullable=False, default="received")
    amount_cents = Column(Integer, nullable=True)
    currency = Column(String, nullable=True)
    raw_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    order = relationship("PaymentOrder", back_populates="events")

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_payment_event_provider_event"),
        Index("idx_payment_event_order", "order_id"),
        Index("idx_payment_event_provider_status", "provider", "processing_status"),
        Index("idx_payment_event_merchant_order", "merchant_order_id"),
    )


class SiteSetting(Base):
    """Admin-managed site setting."""
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False, default="")
    value_type = Column(String, default="text", nullable=False)
    group = Column("setting_group", String, default="general", nullable=False)
    label = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_site_setting_key", "key"),
        Index("idx_site_setting_group", "setting_group"),
    )


class FeatureFlag(Base):
    """Admin-managed feature access switch."""
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    requires_login = Column(Boolean, default=False, nullable=False)
    requires_pro = Column(Boolean, default=False, nullable=False)
    maintenance_message = Column(Text, nullable=True)
    free_daily_limit = Column(Integer, nullable=True)
    free_max_file_size_mb = Column(Integer, nullable=True)
    free_batch_file_limit = Column(Integer, nullable=True)
    pro_daily_limit = Column(Integer, nullable=True)
    pro_max_file_size_mb = Column(Integer, nullable=True)
    pro_batch_file_limit = Column(Integer, nullable=True)
    pro_unlimited = Column(Boolean, default=False, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_feature_flag_key", "key"),
        Index("idx_feature_flag_enabled", "enabled"),
    )


class ContentBlock(Base):
    """Admin-editable content block for public pages."""
    __tablename__ = "content_blocks"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    locale = Column(String, default="zh", nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False, default="")
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("key", "locale", name="uq_content_block_key_locale"),
        Index("idx_content_block_key", "key"),
        Index("idx_content_block_locale", "locale"),
    )


class PricingPlan(Base):
    """Admin-managed public plan catalog and provider price mapping."""
    __tablename__ = "pricing_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_key = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    price_amount_cents = Column(Integer, default=0, nullable=False)
    display_price = Column(String, nullable=False, default="")
    currency = Column(String, default="USD", nullable=False)
    billing_interval = Column(String, default="none", nullable=False)
    description = Column(Text, nullable=True)
    provider_mappings_json = Column(Text, nullable=False, default="{}")
    sort_order = Column(Integer, default=0, nullable=False)
    highlighted = Column(Boolean, default=False, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_pricing_plan_key", "plan_key"),
        Index("idx_pricing_plan_public", "is_public"),
        Index("idx_pricing_plan_sort", "sort_order"),
    )


class AdminAuditLog(Base):
    """Audit trail for hidden admin operations."""
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_key = Column(String, nullable=False)
    status = Column(String, default="success", nullable=False)
    detail = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_admin_audit_admin", "admin_user_id"),
        Index("idx_admin_audit_target", "target_type", "target_key"),
    )


class FeedbackReport(Base):
    """User-submitted issue report for live testing and support triage."""
    __tablename__ = "feedback_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String, nullable=True)
    category = Column(String, default="bug", nullable=False)
    severity = Column(String, default="normal", nullable=False)
    status = Column(String, default="new", nullable=False)
    page_url = Column(Text, nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    diagnostic_code = Column(String, nullable=True)
    diagnostics = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_feedback_status", "status"),
        Index("idx_feedback_created", "created_at"),
        Index("idx_feedback_user", "user_id"),
    )


class ApiErrorLog(Base):
    """Recent API error summary for hidden admin diagnostics."""
    __tablename__ = "api_error_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_id = Column(String, nullable=True)
    method = Column(String, nullable=False)
    path = Column(Text, nullable=False)
    query_string = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=False)
    error_type = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    traceback_summary = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_api_error_status", "status_code"),
        Index("idx_api_error_created", "created_at"),
        Index("idx_api_error_path", "path"),
    )
