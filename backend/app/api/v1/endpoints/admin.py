"""Hidden admin console endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.user import (
    AdminAuditLog,
    ContentBlock,
    FeatureFlag,
    ProcessingJob,
    SiteSetting,
    User,
    UserRole,
)
from app.services.feature_gate import DEFAULT_FEATURE_FLAGS
from app.schemas.admin import (
    AdminAuditLogResponse,
    AdminJobResponse,
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
        "recent_audit_logs": recent_logs,
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
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": _role_value(user),
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        }
        for user in users
    ]


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
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": _role_value(user),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


@router.get("/jobs", response_model=list[AdminJobResponse])
async def list_jobs(
    status_filter: str | None = None,
    limit: int = 50,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return recent processing jobs with user context."""
    query = (
        db.query(ProcessingJob, User.email)
        .outerjoin(User, ProcessingJob.user_id == User.id)
        .order_by(ProcessingJob.created_at.desc())
    )
    if status_filter:
        query = query.filter(ProcessingJob.status == status_filter)

    rows = query.limit(min(max(limit, 1), 100)).all()
    return [
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
