"""Hidden admin console endpoints."""
from datetime import datetime
import json
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.user import (
    AdminAuditLog,
    ApiErrorLog,
    ContentBlock,
    FeatureFlag,
    FeedbackReport,
    ProcessingJob,
    SiteSetting,
    User,
    UserRole,
)
from app.services.feature_gate import DEFAULT_FEATURE_FLAGS
from app.services.file_service import file_processing_service
from app.schemas.admin import (
    AdminAuditLogResponse,
    AdminApiErrorResponse,
    AdminDiagnosticsResponse,
    AdminJobResponse,
    AdminOperationsResponse,
    AdminOverviewResponse,
    AdminUserResponse,
    AdminUserUpdate,
    ContentBlockResponse,
    ContentBlockUpdate,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    SiteSettingResponse,
    SiteSettingUpdate,
)
from app.schemas.feedback import AdminFeedbackResponse, AdminFeedbackUpdate

router = APIRouter()


DEFAULT_SETTINGS = [
    {
        "key": "site_name",
        "value": "PDF-Flow",
        "value_type": "text",
        "group": "brand",
        "label": "站点名称",
        "description": "显示在浏览器标题、页脚和品牌区域的名称。",
    },
    {
        "key": "support_contact",
        "value": "请通过页面截图、时间点和错误编号联系管理员。",
        "value_type": "textarea",
        "group": "support",
        "label": "支持说明",
        "description": "用于页脚或错误提示中的支持说明。",
    },
    {
        "key": "support_email",
        "value": "support@pdf-flow.com",
        "value_type": "text",
        "group": "support",
        "label": "支持邮箱",
        "description": "用于页脚、支付结果页和公开支持入口。",
    },
    {
        "key": "global_announcement",
        "value": "",
        "value_type": "textarea",
        "group": "notice",
        "label": "全站公告",
        "description": "留空表示不展示全站公告。",
    },
    {
        "key": "maintenance_mode",
        "value": "false",
        "value_type": "boolean",
        "group": "system",
        "label": "维护模式",
        "description": "开启后公开页面展示维护提示，处理类接口会暂停普通用户访问。",
    },
]

DEFAULT_CONTENT_BLOCKS = [
    (
        "privacy_policy",
        "zh",
        "我们如何保护你的文件与账户信息",
        "我们不会出售你的个人信息，也不会为了广告画像而读取你的文件内容。上传到云端处理的文件仅用于完成你主动发起的任务、排查故障和保障服务安全，并会尽量缩短保留时间。",
    ),
    (
        "privacy_policy",
        "en",
        "How we protect your files and account information",
        "We do not sell your personal information or read your documents for advertising profiles. Files uploaded for cloud processing are used to complete the task you requested, troubleshoot issues, and protect service security, with retention kept as short as practical.",
    ),
    (
        "terms_of_service",
        "zh",
        "使用 PDF-Flow 前请了解这些规则",
        "你可以使用 PDF-Flow 处理合法、合规、属于你或你有权处理的文件。请不要上传违法、侵权、恶意、滥用资源或可能伤害他人的内容。重要文件请自行保留备份并核对处理结果。",
    ),
    (
        "terms_of_service",
        "en",
        "Please understand these rules before using PDF-Flow",
        "You may use PDF-Flow to process legal documents that you own or are allowed to handle. Do not upload unlawful, infringing, malicious, abusive, or harmful content. Keep your own backups and verify important results.",
    ),
    (
        "home_hero",
        "zh",
        "PDF-Flow",
        "隐私优先的 PDF 工作台，合并、拆分、压缩、转换、OCR 与 AI 分析都在一个清晰流程里完成。",
    ),
    (
        "home_hero",
        "en",
        "PDF-Flow",
        "A privacy-first PDF workspace for merging, splitting, compressing, converting, OCR, and AI-assisted document review.",
    ),
    (
        "pricing_intro",
        "zh",
        "先从免费开始，需要云端能力时再升级",
        "基础 PDF 工具适合日常处理；当 OCR、Office 转换、AI 分析或团队流程成为稳定需求时，再开启更高套餐。",
    ),
    (
        "pricing_intro",
        "en",
        "Start free, upgrade when cloud work matters",
        "Core PDF tools cover everyday work. Upgrade when OCR, Office conversion, AI analysis, or team workflows become part of your regular process.",
    ),
]

LEGACY_CONTENT_PLACEHOLDERS = {
    "由后台接管后，可在这里维护隐私政策正文。",
    "由后台接管后，可在这里维护服务条款正文。",
    "用于后续从后台维护首页首屏文案。",
    "用于后续从后台维护定价页说明。",
}


def _role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _is_test_account(user: User) -> bool:
    email = (user.email or "").lower()
    return (
        email.startswith("smoke-")
        or email.startswith("ocr-")
        or email.startswith("office-")
        or email.endswith("@example.com")
    )


def _serialize_admin_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": _role_value(user),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_test_account": _is_test_account(user),
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


def _datetime_from_epoch(value) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(value))
    except (TypeError, ValueError, OSError):
        return None


def _infer_job_type(status_data: dict) -> str:
    message = str(status_data.get("message") or "").lower()
    result = status_data.get("result") or {}
    if "ocr" in message or "text" in result:
        return "ocr_pdf"
    if "office" in message:
        return "office_to_pdf"
    if "merge" in message:
        return "merge_pdf"
    if "split" in message:
        return "split_pdf"
    if "compression" in message or "compress" in message:
        return "compress_pdf"
    if "rotation" in message or "rotate" in message:
        return "rotate_pdf"
    if "image to pdf" in message:
        return "image_to_pdf"
    if "pdf to images" in message:
        return "pdf_to_image"
    return "processing_job"


def _list_redis_jobs(limit: int) -> list[dict]:
    jobs = []
    redis_client = file_processing_service.redis_client
    try:
        keys = list(redis_client.scan_iter("job:*", count=100))
    except AttributeError:
        keys = [key for key in getattr(redis_client, "store", {}).keys() if str(key).startswith("job:")]
    except Exception:
        return jobs

    for index, key in enumerate(keys):
        try:
            raw = redis_client.get(key)
            if not raw:
                continue
            import json

            status_data = json.loads(raw)
        except Exception:
            continue

        created_at = _datetime_from_epoch(status_data.get("created_at"))
        updated_at = _datetime_from_epoch(status_data.get("updated_at")) or created_at
        result = status_data.get("result") or {}
        error = status_data.get("error")
        output_path = result.get("output_path") or ""
        input_file_name = result.get("input_file_name") or output_path.rsplit("/", 1)[-1] or "Redis task"
        jobs.append({
            "id": None,
            "job_id": status_data.get("job_id") or str(key).replace("job:", ""),
            "user_id": None,
            "user_email": None,
            "job_type": _infer_job_type(status_data),
            "status": status_data.get("status", "unknown"),
            "progress": int(status_data.get("progress") or (100 if status_data.get("status") == "completed" else 0)),
            "input_file_name": input_file_name,
            "input_file_size": int(result.get("file_size") or 0),
            "error_message": str(error) if error else None,
            "created_at": created_at or datetime.fromtimestamp(0),
            "started_at": None,
            "completed_at": updated_at if status_data.get("status") in ("completed", "failed") else None,
            "_sort": created_at.timestamp() if created_at else time.time() - index,
        })

    jobs.sort(key=lambda item: item["_sort"], reverse=True)
    for item in jobs:
        item.pop("_sort", None)
    return jobs[:limit]


def _check_services(db: Session) -> dict:
    services = {}
    try:
        db.execute(text("SELECT 1"))
        services["database"] = {"status": "healthy", "detail": "Postgres reachable"}
    except Exception as exc:
        services["database"] = {"status": "unhealthy", "detail": str(exc)}

    try:
        file_processing_service.redis_client.ping()
        services["redis"] = {"status": "healthy", "detail": "Redis reachable"}
    except Exception as exc:
        services["redis"] = {"status": "unhealthy", "detail": str(exc)}

    redis_ok = services.get("redis", {}).get("status") == "healthy"
    services["celery_worker"] = {
        "status": "unknown" if redis_ok else "unhealthy",
        "detail": "Worker health is inferred from task movement; run smoke tests for confirmation."
        if redis_ok else "Redis broker is unavailable.",
    }
    return services


def _list_all_jobs_for_admin(db: Session, limit: int, status_filter: str | None = None) -> list[dict]:
    safe_limit = min(max(limit, 1), 100)
    redis_jobs = _list_redis_jobs(safe_limit)
    if status_filter:
        redis_jobs = [job for job in redis_jobs if job["status"] == status_filter]

    query = (
        db.query(ProcessingJob, User.email)
        .outerjoin(User, ProcessingJob.user_id == User.id)
        .order_by(ProcessingJob.created_at.desc())
    )
    if status_filter:
        query = query.filter(ProcessingJob.status == status_filter)

    rows = query.limit(safe_limit).all()
    db_jobs = [
        {
            "id": job.id,
            "job_id": job.job_id,
            "user_id": job.user_id,
            "user_email": email,
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "input_file_name": job.input_file_name,
            "input_file_size": job.input_file_size,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
        for job, email in rows
    ]
    seen = {job["job_id"] for job in redis_jobs}
    merged = redis_jobs + [job for job in db_jobs if job["job_id"] not in seen]
    merged.sort(key=lambda item: item["created_at"], reverse=True)
    return merged[:safe_limit]


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require an authenticated admin user."""
    if _role_value(current_user) != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def _seed_defaults(db: Session) -> None:
    existing_settings = {
        item[0] for item in db.query(SiteSetting.key).all()
    }
    for item in DEFAULT_SETTINGS:
        if item["key"] not in existing_settings:
            db.add(SiteSetting(**item))

    existing_flags = {
        item[0] for item in db.query(FeatureFlag.key).all()
    }
    for key, label, description, enabled, requires_login, requires_pro in DEFAULT_FEATURE_FLAGS:
        if key not in existing_flags:
            db.add(
                FeatureFlag(
                    key=key,
                    label=label,
                    description=description,
                    enabled=enabled,
                    requires_login=requires_login,
                    requires_pro=requires_pro,
                )
            )

    existing_blocks = {
        (item.key, item.locale): item for item in db.query(ContentBlock).all()
    }
    for key, locale, title, content in DEFAULT_CONTENT_BLOCKS:
        block = existing_blocks.get((key, locale))
        if block is None:
            db.add(ContentBlock(key=key, locale=locale, title=title, content=content))
        elif block.content in LEGACY_CONTENT_PLACEHOLDERS:
            block.title = title
            block.content = content

    db.commit()


def _write_audit(
    db: Session,
    request: Request,
    admin: User,
    action: str,
    target_type: str,
    target_key: str,
    detail: str | None = None,
) -> None:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_key=target_key,
            detail=detail,
            ip_address=client_host,
            user_agent=user_agent,
        )
    )


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_admin_overview(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return admin console summary and seed defaults on first use."""
    _seed_defaults(db)
    recent_logs = (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(8)
        .all()
    )
    return {
        "settings_count": db.query(SiteSetting).count(),
        "feature_flags_count": db.query(FeatureFlag).count(),
        "content_blocks_count": db.query(ContentBlock).count(),
        "users_count": db.query(User).count(),
        "active_users_count": db.query(User).filter(User.is_active == True).count(),  # noqa: E712
        "admin_users_count": db.query(User).filter(User.role == UserRole.ADMIN).count(),
        "jobs_count": db.query(ProcessingJob).count(),
        "failed_jobs_count": db.query(ProcessingJob).filter(ProcessingJob.status == "failed").count(),
        "feedback_count": db.query(FeedbackReport).count(),
        "open_feedback_count": db.query(FeedbackReport).filter(FeedbackReport.status.in_(["new", "reviewing"])).count(),
        "api_error_count": db.query(ApiErrorLog).count(),
        "recent_audit_logs": recent_logs,
    }


@router.get("/operations", response_model=AdminOperationsResponse)
async def get_operations_overview(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return one-shot operational dashboard data for the hidden control room."""
    _seed_defaults(db)
    users = db.query(User).order_by(User.created_at.desc()).limit(8).all()
    all_users = db.query(User).all()
    jobs = _list_all_jobs_for_admin(db, limit=50)
    failed_jobs = [job for job in jobs if job["status"] == "failed"]
    running_jobs = [job for job in jobs if job["status"] in ("pending", "processing")]

    return {
        "generated_at": datetime.utcnow(),
        "services": _check_services(db),
        "total_users": len(all_users),
        "active_users": len([user for user in all_users if user.is_active]),
        "banned_users": len([user for user in all_users if not user.is_active]),
        "test_users": len([user for user in all_users if _is_test_account(user)]),
        "total_jobs": db.query(ProcessingJob).count(),
        "visible_jobs": len(jobs),
        "failed_jobs": len(failed_jobs),
        "running_jobs": len(running_jobs),
        "recent_users": [_serialize_admin_user(user) for user in users],
        "recent_failed_jobs": failed_jobs[:5],
        "recent_jobs": jobs[:8],
    }


@router.get("/public-config")
async def get_public_config(db: Session = Depends(get_db)):
    """Public read-only site configuration used by the frontend."""
    _seed_defaults(db)
    settings = db.query(SiteSetting).filter(SiteSetting.is_public == True).all()  # noqa: E712
    feature_flags = db.query(FeatureFlag).order_by(FeatureFlag.key).all()
    content_blocks = db.query(ContentBlock).filter(ContentBlock.is_public == True).all()  # noqa: E712

    return {
        "settings": {
            item.key: {
                "value": item.value,
                "value_type": item.value_type,
                "group": item.group,
                "label": item.label,
            }
            for item in settings
        },
        "feature_flags": {
            item.key: {
                "label": item.label,
                "description": item.description,
                "enabled": item.enabled,
                "requires_login": item.requires_login,
                "requires_pro": item.requires_pro,
                "maintenance_message": item.maintenance_message,
            }
            for item in feature_flags
        },
        "content_blocks": {
            f"{item.key}:{item.locale}": {
                "title": item.title,
                "content": item.content,
                "description": item.description,
            }
            for item in content_blocks
        },
    }


@router.get("/settings", response_model=list[SiteSettingResponse])
async def list_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _seed_defaults(db)
    return db.query(SiteSetting).order_by(SiteSetting.group, SiteSetting.key).all()


@router.put("/settings/{key}", response_model=SiteSettingResponse)
async def update_setting(
    key: str,
    payload: SiteSettingUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _seed_defaults(db)
    setting = db.query(SiteSetting).filter(SiteSetting.key == key).first()
    if not setting:
        setting = SiteSetting(key=key)
        db.add(setting)

    for field, value in payload.model_dump().items():
        setattr(setting, field, value)
    setting.updated_by_id = admin.id
    _write_audit(db, request, admin, "update", "site_setting", key)
    db.commit()
    db.refresh(setting)
    return setting


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _seed_defaults(db)
    return db.query(FeatureFlag).order_by(FeatureFlag.key).all()


@router.put("/feature-flags/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    key: str,
    payload: FeatureFlagUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _seed_defaults(db)
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == key).first()
    if not flag:
        flag = FeatureFlag(key=key)
        db.add(flag)

    for field, value in payload.model_dump().items():
        setattr(flag, field, value)
    flag.updated_by_id = admin.id
    _write_audit(db, request, admin, "update", "feature_flag", key)
    db.commit()
    db.refresh(flag)
    return flag


@router.get("/content-blocks", response_model=list[ContentBlockResponse])
async def list_content_blocks(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _seed_defaults(db)
    return db.query(ContentBlock).order_by(ContentBlock.key, ContentBlock.locale).all()


@router.put("/content-blocks/{key}/{locale}", response_model=ContentBlockResponse)
async def update_content_block(
    key: str,
    locale: str,
    payload: ContentBlockUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _seed_defaults(db)
    block = (
        db.query(ContentBlock)
        .filter(ContentBlock.key == key, ContentBlock.locale == locale)
        .first()
    )
    if not block:
        block = ContentBlock(key=key, locale=locale)
        db.add(block)

    data = payload.model_dump()
    data["locale"] = locale
    for field, value in data.items():
        setattr(block, field, value)
    block.updated_by_id = admin.id
    _write_audit(db, request, admin, "update", "content_block", f"{key}:{locale}")
    db.commit()
    db.refresh(block)
    return block


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    search: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent users for hidden admin operations."""
    query = db.query(User).order_by(User.created_at.desc())
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (User.email.ilike(pattern)) | (User.full_name.ilike(pattern))
        )

    users = query.limit(min(max(limit, 1), 100)).all()
    return [_serialize_admin_user(user) for user in users]


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update a user's operational status or role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if user.id == admin.id and (
        data.get("is_active") is False
        or (data.get("role") is not None and data["role"] != UserRole.ADMIN.value)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin access.",
        )

    if "role" in data:
        try:
            user.role = UserRole(data["role"])
        except ValueError as exc:
            allowed = ", ".join(role.value for role in UserRole)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid role. Allowed values: {allowed}",
            ) from exc
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "is_verified" in data:
        user.is_verified = data["is_verified"]

    _write_audit(
        db,
        request,
        admin,
        "update",
        "user",
        user.email,
        detail=", ".join(sorted(data.keys())),
    )
    db.commit()
    db.refresh(user)
    return _serialize_admin_user(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a non-current user account and related owned records."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own admin account.",
        )

    email = user.email
    _write_audit(db, request, admin, "delete", "user", email)
    db.delete(user)
    db.commit()
    return None


@router.get("/jobs", response_model=list[AdminJobResponse])
async def list_jobs(
    status_filter: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent processing jobs with user context."""
    return _list_all_jobs_for_admin(db, limit=limit, status_filter=status_filter)


@router.get("/feedback", response_model=list[AdminFeedbackResponse])
async def list_feedback(
    status_filter: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent user-submitted feedback reports."""
    safe_limit = min(max(limit, 1), 100)
    query = db.query(FeedbackReport).order_by(FeedbackReport.created_at.desc())
    if status_filter:
        query = query.filter(FeedbackReport.status == status_filter)
    return query.limit(safe_limit).all()


@router.get("/errors", response_model=list[AdminApiErrorResponse])
async def list_api_errors(
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent API 500-level error summaries."""
    safe_limit = min(max(limit, 1), 100)
    return (
        db.query(ApiErrorLog)
        .order_by(ApiErrorLog.created_at.desc())
        .limit(safe_limit)
        .all()
    )


@router.get("/diagnostics", response_model=AdminDiagnosticsResponse)
async def get_diagnostics(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return combined live-testing signals for quick production triage."""
    errors = (
        db.query(ApiErrorLog)
        .order_by(ApiErrorLog.created_at.desc())
        .limit(20)
        .all()
    )
    jobs = _list_all_jobs_for_admin(db, limit=50)
    failed_jobs = [job for job in jobs if job["status"] == "failed"][:10]
    feedback = (
        db.query(FeedbackReport)
        .filter(FeedbackReport.status.in_(["new", "reviewing"]))
        .order_by(FeedbackReport.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "generated_at": datetime.utcnow(),
        "recent_errors": errors,
        "recent_failed_jobs": failed_jobs,
        "recent_feedback": [
            {
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "severity": item.severity,
                "page_url": item.page_url,
                "diagnostic_code": item.diagnostic_code,
                "created_at": item.created_at,
            }
            for item in feedback
        ],
        "open_feedback_count": db.query(FeedbackReport).filter(FeedbackReport.status.in_(["new", "reviewing"])).count(),
        "failed_jobs_count": len([job for job in jobs if job["status"] == "failed"]),
        "api_error_count": db.query(ApiErrorLog).count(),
    }


@router.patch("/feedback/{feedback_id}", response_model=AdminFeedbackResponse)
async def update_feedback(
    feedback_id: int,
    payload: AdminFeedbackUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update feedback triage status or internal admin note."""
    report = db.query(FeedbackReport).filter(FeedbackReport.id == feedback_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        allowed = {"new", "reviewing", "resolved", "closed"}
        if data["status"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid feedback status. Allowed values: {', '.join(sorted(allowed))}",
            )
        report.status = data["status"]
    if "admin_note" in data:
        report.admin_note = data["admin_note"]

    _write_audit(
        db,
        request,
        admin,
        "update",
        "feedback",
        str(report.id),
        detail=json.dumps(data, ensure_ascii=False),
    )
    db.commit()
    db.refresh(report)
    return report


@router.get("/audit-logs", response_model=list[AdminAuditLogResponse])
async def list_audit_logs(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(50)
        .all()
    )
