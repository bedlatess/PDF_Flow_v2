"""Schemas for hidden admin console APIs."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class SiteSettingBase(BaseModel):
    value: str = ""
    value_type: str = Field(default="text", max_length=40)
    group: str = Field(default="general", max_length=80)
    label: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    is_public: bool = True


class SiteSettingUpdate(SiteSettingBase):
    pass


class SiteSettingResponse(SiteSettingBase):
    id: int
    key: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    enabled: bool = True
    is_public: bool = True
    requires_login: bool = False
    requires_pro: bool = False
    maintenance_message: Optional[str] = None


class FeatureFlagUpdate(FeatureFlagBase):
    pass


class FeatureFlagResponse(FeatureFlagBase):
    id: int
    key: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentBlockBase(BaseModel):
    locale: str = Field(default="zh", max_length=12)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = ""
    description: Optional[str] = None
    is_public: bool = True


class ContentBlockUpdate(ContentBlockBase):
    pass


class ContentBlockResponse(ContentBlockBase):
    id: int
    key: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


PlanKey = Literal["free", "pro_monthly", "pro_yearly", "enterprise"]
BillingInterval = Literal["none", "month", "year", "custom"]


class StripePlanMapping(BaseModel):
    price_id: str = ""


class PayPalPlanMapping(BaseModel):
    plan_id: str = ""
    product_id: str = ""


class GMPayPlanMapping(BaseModel):
    amount_cents: int = Field(default=0, ge=0)
    currency: str = "CNY"
    token: str = "usdt"
    network: str = "tron"


class PricingProviderMappings(BaseModel):
    stripe: StripePlanMapping = Field(default_factory=StripePlanMapping)
    paypal: PayPalPlanMapping = Field(default_factory=PayPalPlanMapping)
    gmpay: GMPayPlanMapping = Field(default_factory=GMPayPlanMapping)


class PricingPlanBase(BaseModel):
    plan_key: PlanKey
    display_name: str = Field(..., min_length=1, max_length=120)
    is_public: bool = True
    price_amount_cents: int = Field(default=0, ge=0)
    display_price: str = Field(default="", max_length=80)
    currency: str = Field(default="USD", min_length=3, max_length=12)
    billing_interval: BillingInterval = "none"
    description: Optional[str] = None
    provider_mappings: PricingProviderMappings = Field(default_factory=PricingProviderMappings)
    sort_order: int = 0
    highlighted: bool = False


class PricingPlanUpdate(PricingPlanBase):
    pass


class PricingPlanResponse(PricingPlanBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogResponse(BaseModel):
    id: int
    admin_user_id: int
    action: str
    target_type: str
    target_key: str
    status: str
    detail: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    is_test_account: bool = False
    subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_end_date: Optional[datetime] = None
    created_at: datetime
    last_login_at: Optional[datetime]


class AdminUserUpdate(BaseModel):
    role: Optional[str] = Field(default=None, max_length=40)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    subscription_id: Optional[str] = Field(default=None, max_length=255)
    subscription_status: Optional[str] = Field(default=None, max_length=40)
    subscription_end_date: Optional[datetime] = None


class AdminPasswordResetLinkResponse(BaseModel):
    user_id: int
    email: str
    reset_url: str
    expires_at: datetime


class AdminJobResponse(BaseModel):
    id: Optional[int]
    job_id: str
    user_id: Optional[int]
    user_email: Optional[str]
    job_type: str
    status: str
    progress: int
    input_file_name: str
    input_file_size: int
    output_file_url: Optional[str] = None
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    source: str = "db"
    sources: list[str] = Field(default_factory=list)
    is_durable: bool = False


class AdminApiErrorResponse(BaseModel):
    id: int
    user_id: Optional[int]
    request_id: Optional[str]
    method: str
    path: str
    query_string: Optional[str]
    status_code: int
    error_type: Optional[str]
    error_message: Optional[str]
    traceback_summary: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminServiceStatus(BaseModel):
    status: str
    detail: Optional[str] = None


class AdminOperationsResponse(BaseModel):
    generated_at: datetime
    services: dict[str, AdminServiceStatus]
    total_users: int
    active_users: int
    banned_users: int
    test_users: int
    total_jobs: int
    visible_jobs: int
    failed_jobs: int
    running_jobs: int
    recent_users: list[AdminUserResponse]
    recent_failed_jobs: list[AdminJobResponse]
    recent_jobs: list[AdminJobResponse]


class AdminOverviewResponse(BaseModel):
    settings_count: int
    feature_flags_count: int
    content_blocks_count: int
    users_count: int
    active_users_count: int
    admin_users_count: int
    jobs_count: int
    failed_jobs_count: int
    feedback_count: int = 0
    open_feedback_count: int = 0
    api_error_count: int = 0
    recent_audit_logs: list[AdminAuditLogResponse]


class AdminDiagnosticsResponse(BaseModel):
    generated_at: datetime
    recent_errors: list[AdminApiErrorResponse]
    recent_failed_jobs: list[AdminJobResponse]
    recent_feedback: list[dict]
    diagnostic_summary: str
    open_feedback_count: int
    failed_jobs_count: int
    api_error_count: int


class AdminFeedbackCleanupResponse(BaseModel):
    closed_count: int
    remaining_open_count: int


class AdminFileRetentionResponse(BaseModel):
    scanned_count: int
    removable_count: int
    removed_count: int = 0
    removed_bytes: int = 0
    skipped_count: int
    upload_dir: str


class AdminMaintenanceResponse(BaseModel):
    test_users_count: int
    live_acceptance_feedback_count: int
    open_feedback_count: int
    api_error_count: int
    failed_jobs_count: int
    running_jobs_count: int
    file_retention: AdminFileRetentionResponse


class AdminCleanupTestUsersResponse(BaseModel):
    deleted_count: int
    deleted_emails: list[str]
    remaining_test_users_count: int


class AdminHealthReportResponse(BaseModel):
    generated_at: datetime
    app_version: str
    environment: str
    migration_version: Optional[str]
    services: dict[str, AdminServiceStatus]
    users_count: int
    active_users_count: int
    open_feedback_count: int
    api_error_count: int
    failed_jobs_count: int
    running_jobs_count: int
    recent_error_path: Optional[str] = None
    recent_feedback_title: Optional[str] = None


class AdminPaymentOrderResponse(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str]
    provider: str
    provider_display_name: str
    merchant_order_id: str
    provider_order_id: Optional[str]
    plan: str
    amount_cents: int
    currency: str
    status: str
    checkout_url_present: bool = False
    qr_code_url_present: bool = False
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    paid_at: Optional[datetime]


class AdminPaymentProviderHealth(BaseModel):
    key: str
    display_name: str
    enabled: bool
    configured: bool
    acceptance_status: str
    acceptance_label: str
    acceptance_detail: str
    acceptance_blockers: list[str]
    latest_paid_event_at: Optional[datetime] = None
    settlement: str
    supports_subscription: bool
    supports_one_time: bool
    open_orders: int = 0
    paid_orders: int = 0
    failed_orders: int = 0
    latest_order_at: Optional[datetime] = None
    detail: str
    webhook_url: str
    success_return_url: str
    cancel_return_url: str
    merchant_console_hint: str
    required_config_keys: list[str]
    missing_config_keys: list[str]
    setup_notes: list[str]
    sandbox_runbook: list[str]
    go_live_checklist: list[str]
    expected_event_flow: list[str]
    troubleshooting_steps: list[str]
    evidence_fields: list[str]


class AdminPaymentEventResponse(BaseModel):
    id: int
    order_id: Optional[int]
    provider: str
    provider_event_id: str
    merchant_order_id: str
    provider_order_id: Optional[str]
    event_type: str
    processing_status: str
    amount_cents: Optional[int]
    currency: Optional[str]
    raw_summary: Optional[str]
    error_message: Optional[str]
    created_at: datetime


class AdminPaymentSummaryResponse(BaseModel):
    generated_at: datetime
    total_orders: int
    pending_orders: int
    paid_orders: int
    failed_orders: int
    amount_mismatch_orders: int
    currency_mismatch_orders: int
    expired_pending_orders: int
    paid_amount_cents: int
    currency_breakdown: dict[str, int]
    providers: list[AdminPaymentProviderHealth]
    recent_orders: list[AdminPaymentOrderResponse]
    recent_events: list[AdminPaymentEventResponse]
    reconciliation_summary: str
    integration_evidence_packet: str


class AdminPaymentSecretFieldStatus(BaseModel):
    configured: bool
    tail: str = ""


class AdminPaymentProviderFieldMetadata(BaseModel):
    key: str
    label: str
    input_type: str = "text"
    required: bool = False
    secret: bool = False
    placeholder: str = ""
    help_text: str = ""
    min_value: Optional[int] = None
    max_value: Optional[int] = None


class AdminPaymentProviderMetadataFields(BaseModel):
    public: list[AdminPaymentProviderFieldMetadata]
    secret: list[AdminPaymentProviderFieldMetadata]


class AdminPaymentProviderMetadata(BaseModel):
    provider_key: str
    display_name: str
    description: str
    settlement: str
    supports_subscription: bool
    supports_one_time: bool
    merchant_console_hint: str
    setup_notes: list[str]
    validation_checks: list[str]
    fields: AdminPaymentProviderMetadataFields


class AdminPaymentProviderReadiness(BaseModel):
    status: str
    label: str
    detail: str
    missing_config_keys: list[str]
    validation_checks: list[str]


class AdminPaymentProviderConfigResponse(BaseModel):
    provider_key: str
    display_name: str
    enabled: bool
    configured: bool
    public_config: dict
    secret_fields: dict[str, AdminPaymentSecretFieldStatus]
    required_public_fields: list[str]
    required_secret_fields: list[str]
    missing_config_keys: list[str]
    webhook_url: str
    updated_at: Optional[datetime] = None
    encryption_available: bool
    webhook_status: str
    metadata: AdminPaymentProviderMetadata
    readiness: AdminPaymentProviderReadiness


class AdminPaymentProviderConfigUpdate(BaseModel):
    enabled: bool = False
    public_config: dict = Field(default_factory=dict)
    secrets: dict[str, str] = Field(default_factory=dict)


class AdminPaymentProviderConfigValidation(BaseModel):
    provider_key: str
    valid: bool
    errors: list[str]
    checks: list[str]
    signature_preview_tail: Optional[str] = None


class AdminServiceProviderFieldMetadata(BaseModel):
    key: str
    label: str
    input_type: str = "text"
    required: bool = False
    secret: bool = False
    placeholder: str = ""
    help_text: str = ""
    min_value: Optional[int] = None
    max_value: Optional[int] = None


class AdminServiceProviderMetadataFields(BaseModel):
    public: list[AdminServiceProviderFieldMetadata]
    secret: list[AdminServiceProviderFieldMetadata]


class AdminServiceProviderMetadata(BaseModel):
    service_key: str
    provider_key: str
    display_name: str
    description: str
    validation_checks: list[str]
    setup_notes: list[str]
    runtime_fallback: str
    fields: AdminServiceProviderMetadataFields


class AdminServiceProviderReadiness(BaseModel):
    status: str
    label: str
    detail: str
    missing_config_keys: list[str]
    validation_checks: list[str]


class AdminServiceProviderConfigResponse(BaseModel):
    service_key: str
    provider_key: str
    display_name: str
    enabled: bool
    priority: int
    configured: bool
    public_config: dict
    secret_fields: dict[str, AdminPaymentSecretFieldStatus]
    required_public_fields: list[str]
    required_secret_fields: list[str]
    missing_config_keys: list[str]
    updated_at: Optional[datetime] = None
    encryption_available: bool
    metadata: AdminServiceProviderMetadata
    readiness: AdminServiceProviderReadiness


class AdminServiceProviderConfigUpdate(BaseModel):
    enabled: bool = False
    priority: int = 100
    public_config: dict = Field(default_factory=dict)
    secrets: dict[str, str] = Field(default_factory=dict)


class AdminServiceProviderConfigValidation(BaseModel):
    service_key: str
    provider_key: str
    valid: bool
    errors: list[str]
    checks: list[str]
    signature_preview_tail: Optional[str] = None
