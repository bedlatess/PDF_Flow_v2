"""Hidden admin console endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.domains.admin.content import (
    get_admin_overview_summary,
    get_public_config as get_public_config_payload,
    list_content_blocks as list_content_blocks_service,
    list_feature_flags as list_feature_flags_service,
    list_settings as list_settings_service,
    update_content_block as update_content_block_service,
    update_feature_flag as update_feature_flag_service,
    update_setting as update_setting_service,
)
from app.domains.admin.feedback import (
    cleanup_live_acceptance_feedback as cleanup_live_acceptance_feedback_service,
    list_audit_logs as list_audit_logs_service,
    list_feedback as list_feedback_service,
    update_feedback as update_feedback_service,
)
from app.domains.admin.payment_ops import get_payment_operations_summary
from app.domains.admin.audit import write_admin_audit
from app.domains.pricing import (
    list_pricing_plans as list_pricing_plans_service,
    update_pricing_plan as update_pricing_plan_service,
)
from app.domains.admin.operations import (
    cleanup_expired_files as cleanup_expired_files_service,
    get_diagnostics as get_diagnostics_service,
    get_health_report as get_health_report_service,
    get_maintenance_summary as get_maintenance_summary_service,
    get_operations_overview as get_operations_overview_service,
    list_api_errors as list_api_errors_service,
    list_jobs as list_jobs_service,
)
from app.domains.admin.users import (
    cleanup_test_users as cleanup_test_users_service,
    create_user_password_reset_link as create_user_password_reset_link_service,
    delete_user as delete_user_service,
    list_users as list_users_service,
    role_value,
    update_user as update_user_service,
)
from app.schemas.admin import (
    AdminAuditLogResponse,
    AdminApiErrorResponse,
    AdminCleanupTestUsersResponse,
    AdminDiagnosticsResponse,
    AdminFeedbackCleanupResponse,
    AdminFileRetentionResponse,
    AdminHealthReportResponse,
    AdminJobResponse,
    AdminMaintenanceResponse,
    AdminOperationsResponse,
    AdminPaymentSummaryResponse,
    AdminPaymentProviderConfigResponse,
    AdminPaymentProviderConfigUpdate,
    AdminPaymentProviderConfigValidation,
    AdminOverviewResponse,
    AdminPasswordResetLinkResponse,
    AdminServiceProviderConfigResponse,
    AdminServiceProviderConfigUpdate,
    AdminServiceProviderConfigValidation,
    AdminUserResponse,
    AdminUserUpdate,
    ContentBlockResponse,
    ContentBlockUpdate,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    PricingPlanResponse,
    PricingPlanUpdate,
    SiteSettingResponse,
    SiteSettingUpdate,
)
from app.domains.payment.config_store import (
    build_safe_provider_config,
    list_safe_provider_configs,
    update_provider_config as update_payment_provider_config_service,
    validate_provider_config_payload,
)
from app.domains.service_provider.config_store import (
    build_safe_service_provider_config,
    list_safe_service_provider_configs,
    update_service_provider_config as update_service_provider_config_service,
    validate_service_provider_config_payload,
)
from app.schemas.feedback import AdminFeedbackResponse, AdminFeedbackUpdate

router = APIRouter()


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require an authenticated admin user."""
    if role_value(current_user) != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_admin_overview(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return admin console summary and seed defaults on first use."""
    return get_admin_overview_summary(db)


@router.get("/operations", response_model=AdminOperationsResponse)
async def get_operations_overview(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return one-shot operational dashboard data for the hidden control room."""
    return get_operations_overview_service(db)


@router.get("/health-report", response_model=AdminHealthReportResponse)
async def get_health_report(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return a safe copyable live health summary for admin troubleshooting."""
    return get_health_report_service(db)


@router.get("/payments", response_model=AdminPaymentSummaryResponse)
async def get_payment_operations(
    provider: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return read-only payment operations data for reconciliation."""
    return get_payment_operations_summary(
        db,
        provider=provider,
        status_filter=status_filter,
        limit=limit,
    )


@router.get("/pricing-plans", response_model=list[PricingPlanResponse])
async def list_pricing_plans(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return admin-managed pricing plans."""
    return list_pricing_plans_service(db)


@router.put("/pricing-plans/{plan_key}", response_model=PricingPlanResponse)
async def update_pricing_plan(
    plan_key: str,
    payload: PricingPlanUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update one pricing plan and provider mapping."""
    return update_pricing_plan_service(
        db,
        plan_key=plan_key,
        payload=payload,
        request=request,
        admin=admin,
    )


@router.get("/payment-configs", response_model=list[AdminPaymentProviderConfigResponse])
async def list_payment_provider_configs(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return safe admin-managed provider config state."""
    return list_safe_provider_configs(db)


@router.get("/payment-configs/{provider_key}", response_model=AdminPaymentProviderConfigResponse)
async def get_payment_provider_config(
    provider_key: str,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return one provider config without secret plaintext."""
    return build_safe_provider_config(db, provider_key)


@router.put("/payment-configs/{provider_key}", response_model=AdminPaymentProviderConfigResponse)
async def update_payment_provider_config(
    provider_key: str,
    payload: AdminPaymentProviderConfigUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Save admin-managed provider config. Secret fields are write-only."""
    result, changed_fields = update_payment_provider_config_service(
        db,
        provider_key=provider_key,
        enabled=payload.enabled,
        public_config=payload.public_config,
        secret_values=payload.secrets,
        admin_user_id=admin.id,
    )
    write_admin_audit(
        db,
        request,
        admin,
        action="payment_config.update",
        target_type="payment_provider_config",
        target_key=provider_key,
        detail=(
            f"provider={provider_key}; enabled={payload.enabled}; "
            f"changed_fields={','.join(changed_fields) or 'none'}"
        ),
    )
    db.commit()
    return result


@router.post("/payment-configs/{provider_key}/validate", response_model=AdminPaymentProviderConfigValidation)
async def validate_payment_provider_config(
    provider_key: str,
    payload: AdminPaymentProviderConfigUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Validate config locally without creating a real payment."""
    result = validate_provider_config_payload(
        provider_key=provider_key,
        public_config=payload.public_config,
        secret_values=payload.secrets,
        existing_safe_config=build_safe_provider_config(db, provider_key),
    )
    return {"provider_key": provider_key, **result}


@router.get("/service-provider-configs/{service_key}", response_model=list[AdminServiceProviderConfigResponse])
async def list_service_provider_configs(
    service_key: str,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return safe admin-managed OCR/Office provider config state."""
    return list_safe_service_provider_configs(db, service_key)


@router.get("/service-provider-configs/{service_key}/{provider_key}", response_model=AdminServiceProviderConfigResponse)
async def get_service_provider_config(
    service_key: str,
    provider_key: str,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return one service provider config without secret plaintext."""
    return build_safe_service_provider_config(db, service_key, provider_key)


@router.put("/service-provider-configs/{service_key}/{provider_key}", response_model=AdminServiceProviderConfigResponse)
async def update_service_provider_config(
    service_key: str,
    provider_key: str,
    payload: AdminServiceProviderConfigUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Save admin-managed OCR/Office provider config. Secret fields are write-only."""
    result, changed_fields = update_service_provider_config_service(
        db,
        service_key=service_key,
        provider_key=provider_key,
        enabled=payload.enabled,
        priority=payload.priority,
        public_config=payload.public_config,
        secret_values=payload.secrets,
        admin_user_id=admin.id,
    )
    write_admin_audit(
        db,
        request,
        admin,
        action="service_provider_config.update",
        target_type="service_provider_config",
        target_key=f"{service_key}:{provider_key}",
        detail=(
            f"service={service_key}; provider={provider_key}; enabled={payload.enabled}; "
            f"changed_fields={','.join(changed_fields) or 'none'}"
        ),
    )
    db.commit()
    return result


@router.post(
    "/service-provider-configs/{service_key}/{provider_key}/validate",
    response_model=AdminServiceProviderConfigValidation,
)
async def validate_service_provider_config(
    service_key: str,
    provider_key: str,
    payload: AdminServiceProviderConfigUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Validate OCR/Office provider config locally without creating a job."""
    result = validate_service_provider_config_payload(
        service_key=service_key,
        provider_key=provider_key,
        public_config=payload.public_config,
        secret_values=payload.secrets,
        existing_safe_config=build_safe_service_provider_config(db, service_key, provider_key),
    )
    return {"service_key": service_key, "provider_key": provider_key, **result}


@router.get("/public-config")
async def get_public_config(db: Session = Depends(get_db)):
    """Public read-only site configuration used by the frontend."""
    return get_public_config_payload(db)


@router.get("/settings", response_model=list[SiteSettingResponse])
async def list_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_settings_service(db)


@router.put("/settings/{key}", response_model=SiteSettingResponse)
async def update_setting(
    key: str,
    payload: SiteSettingUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_setting_service(
        db,
        key=key,
        payload=payload,
        request=request,
        admin=admin,
    )


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_feature_flags_service(db)


@router.put("/feature-flags/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    key: str,
    payload: FeatureFlagUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_feature_flag_service(
        db,
        key=key,
        payload=payload,
        request=request,
        admin=admin,
    )


@router.get("/content-blocks", response_model=list[ContentBlockResponse])
async def list_content_blocks(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_content_blocks_service(db)


@router.put("/content-blocks/{key}/{locale}", response_model=ContentBlockResponse)
async def update_content_block(
    key: str,
    locale: str,
    payload: ContentBlockUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_content_block_service(
        db,
        key=key,
        locale=locale,
        payload=payload,
        request=request,
        admin=admin,
    )


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    search: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent users for hidden admin operations."""
    return list_users_service(db, search=search, limit=limit)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update a user's operational status or role."""
    return update_user_service(
        db,
        user_id=user_id,
        payload=payload,
        request=request,
        admin=admin,
    )


@router.post("/users/{user_id}/password-reset-link", response_model=AdminPasswordResetLinkResponse)
async def create_user_password_reset_link(
    user_id: int,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a copyable password reset link for a user without sending email."""
    return create_user_password_reset_link_service(
        db,
        user_id=user_id,
        request=request,
        admin=admin,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a non-current user account and related owned records."""
    delete_user_service(db, user_id=user_id, request=request, admin=admin)
    return None


@router.post("/users/cleanup-test-users", response_model=AdminCleanupTestUsersResponse)
async def cleanup_test_users(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete synthetic test accounts while preserving admin and real user accounts."""
    return cleanup_test_users_service(db, request=request, admin=admin)


@router.get("/jobs", response_model=list[AdminJobResponse])
async def list_jobs(
    status_filter: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent processing jobs with user context."""
    return list_jobs_service(db, limit=limit, status_filter=status_filter)


@router.get("/feedback", response_model=list[AdminFeedbackResponse])
async def list_feedback(
    status_filter: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent user-submitted feedback reports."""
    return list_feedback_service(db, status_filter=status_filter, limit=limit)


@router.get("/errors", response_model=list[AdminApiErrorResponse])
async def list_api_errors(
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent API 500-level error summaries."""
    return list_api_errors_service(db, limit=limit)


@router.get("/diagnostics", response_model=AdminDiagnosticsResponse)
async def get_diagnostics(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return combined live-testing signals for quick production triage."""
    return get_diagnostics_service(db)


@router.get("/maintenance", response_model=AdminMaintenanceResponse)
async def get_maintenance_summary(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return safe cleanup counts for hidden admin maintenance actions."""
    return get_maintenance_summary_service(db, admin=admin)


@router.post("/files/cleanup-expired", response_model=AdminFileRetentionResponse)
async def cleanup_expired_files(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete expired temporary upload/result/download directories under UPLOAD_DIR."""
    return cleanup_expired_files_service(db, request=request, admin=admin)


@router.patch("/feedback/{feedback_id}", response_model=AdminFeedbackResponse)
async def update_feedback(
    feedback_id: int,
    payload: AdminFeedbackUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update feedback triage status or internal admin note."""
    return update_feedback_service(
        db,
        feedback_id=feedback_id,
        payload=payload,
        request=request,
        admin=admin,
    )


@router.post("/feedback/cleanup-live-acceptance", response_model=AdminFeedbackCleanupResponse)
async def cleanup_live_acceptance_feedback(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Close synthetic live-acceptance feedback probes without touching real user reports."""
    return cleanup_live_acceptance_feedback_service(db, request=request, admin=admin)


@router.get("/audit-logs", response_model=list[AdminAuditLogResponse])
async def list_audit_logs(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_audit_logs_service(db)
