"""Admin user management and test-account cleanup."""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.admin.audit import write_admin_audit
from app.domains.auth.service import create_password_reset_link_token
from app.models.user import (
    AdminAuditLog,
    ApiErrorLog,
    FeedbackReport,
    ProcessingJob,
    User,
    UserRole,
    Webhook,
)
from app.schemas.admin import AdminUserUpdate


def role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def is_test_account(user: User) -> bool:
    email = (user.email or "").lower()
    return (
        email.startswith("smoke-")
        or email.startswith("ocr-")
        or email.startswith("office-")
        or email.endswith("@example.com")
    )


def serialize_admin_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_value(user),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_test_account": is_test_account(user),
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


def test_user_query(db: Session, admin: User | None = None):
    query = db.query(User).filter(User.role != UserRole.ADMIN)
    if admin is not None:
        query = query.filter(User.id != admin.id)
    audited_admin_ids = db.query(AdminAuditLog.admin_user_id)
    query = query.filter(~User.id.in_(audited_admin_ids))
    return query.filter(
        (User.email.ilike("smoke-%"))
        | (User.email.ilike("ocr-%"))
        | (User.email.ilike("office-%"))
        | (User.email.ilike("%@example.com"))
    )


def list_users(
    db: Session,
    *,
    search: str | None = None,
    limit: int = 50,
) -> list[dict]:
    query = db.query(User).order_by(User.created_at.desc())
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (User.email.ilike(pattern)) | (User.full_name.ilike(pattern))
        )

    users = query.limit(min(max(limit, 1), 100)).all()
    return [serialize_admin_user(user) for user in users]


def update_user(
    db: Session,
    *,
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    admin: User,
) -> dict:
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

    write_admin_audit(
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
    return serialize_admin_user(user)


def create_user_password_reset_link(
    db: Session,
    *,
    user_id: int,
    request: Request,
    admin: User,
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a reset link for an inactive user.",
        )

    token, expires_at = create_password_reset_link_token(
        db,
        user=user,
        source="admin_generated",
        admin=admin,
    )
    reset_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/zh-cn/auth/reset-password?token={token}"
    )

    write_admin_audit(
        db,
        request,
        admin,
        "create",
        "password_reset_link",
        user.email,
        detail=f"expires_at={expires_at.isoformat()}",
    )
    db.commit()

    return {
        "user_id": user.id,
        "email": user.email,
        "reset_url": reset_url,
        "expires_at": expires_at,
    }


def delete_user(
    db: Session,
    *,
    user_id: int,
    request: Request,
    admin: User,
) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own admin account.",
        )

    email = user.email
    write_admin_audit(db, request, admin, "delete", "user", email)
    db.delete(user)
    db.commit()


def cleanup_test_users(
    db: Session,
    *,
    request: Request,
    admin: User,
) -> dict:
    users = test_user_query(db, admin).all()
    user_ids = [user.id for user in users]
    deleted_emails = [user.email for user in users]

    if user_ids:
        db.query(FeedbackReport).filter(FeedbackReport.user_id.in_(user_ids)).update(
            {FeedbackReport.user_id: None},
            synchronize_session=False,
        )
        db.query(ApiErrorLog).filter(ApiErrorLog.user_id.in_(user_ids)).update(
            {ApiErrorLog.user_id: None},
            synchronize_session=False,
        )
        db.query(ProcessingJob).filter(ProcessingJob.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )
        db.query(Webhook).filter(Webhook.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )

        for user in users:
            db.delete(user)

    write_admin_audit(
        db,
        request,
        admin,
        "cleanup",
        "user",
        "test_accounts",
        detail=f"deleted={len(users)}",
    )
    db.commit()

    return {
        "deleted_count": len(users),
        "deleted_emails": deleted_emails,
        "remaining_test_users_count": test_user_query(db, admin).count(),
    }
