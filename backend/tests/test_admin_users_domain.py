"""Admin user-management domain tests."""

import pytest
from fastapi import HTTPException


def _register(client, email="admin-users-domain@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Admin Users Domain",
    })


def _request_stub():
    return type("RequestStub", (), {
        "client": type("ClientStub", (), {"host": "127.0.0.1"})(),
        "headers": {"user-agent": "domain-test"},
    })()


def test_admin_users_domain_lists_updates_and_protects_admin_self(client):
    from datetime import datetime, timedelta

    from app.core.database import get_db
    from app.domains.admin.users import (
        list_users,
        serialize_admin_user,
        update_user,
    )
    from app.models.user import AdminAuditLog, User, UserRole
    from app.schemas.admin import AdminUserUpdate

    _register(client)
    _register(client, email="customer-users-domain@example.com")

    db = next(client.app.dependency_overrides[get_db]())
    try:
        admin = db.query(User).filter(User.email == "admin-users-domain@example.com").first()
        admin.role = UserRole.ADMIN
        customer = db.query(User).filter(
            User.email == "customer-users-domain@example.com"
        ).first()
        db.commit()

        listed = list_users(db, search="customer-users", limit=10)
        assert [item["email"] for item in listed] == ["customer-users-domain@example.com"]
        assert listed[0]["is_test_account"] is True

        updated = update_user(
            db,
            user_id=customer.id,
            payload=AdminUserUpdate(
                role="pro",
                is_verified=True,
                subscription_status="manual",
                subscription_end_date=datetime.utcnow() + timedelta(days=365),
            ),
            request=_request_stub(),
            admin=admin,
        )
        assert updated["role"] == "pro"
        assert updated["is_verified"] is True
        assert updated["subscription_status"] == "manual"
        assert updated["subscription_end_date"] is not None

        with pytest.raises(HTTPException) as demote_error:
            update_user(
                db,
                user_id=admin.id,
                payload=AdminUserUpdate(role="free"),
                request=_request_stub(),
                admin=admin,
            )
        assert demote_error.value.status_code == 400

        with pytest.raises(HTTPException) as deactivate_error:
            update_user(
                db,
                user_id=admin.id,
                payload=AdminUserUpdate(is_active=False),
                request=_request_stub(),
                admin=admin,
            )
        assert deactivate_error.value.status_code == 400

        serialized_admin = serialize_admin_user(admin)
        assert serialized_admin["role"] == "admin"
        assert serialized_admin["is_test_account"] is True

        audits = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at).all()
        assert audits[-1].target_type == "user"
        assert audits[-1].target_key == "customer-users-domain@example.com"
        assert audits[-1].detail == "is_verified, role, subscription_end_date, subscription_status"
    finally:
        db.close()


def test_admin_users_domain_delete_and_cleanup_keep_real_accounts(client):
    from app.core.database import get_db
    from app.domains.admin.users import cleanup_test_users, delete_user, list_users
    from app.models.user import (
        AdminAuditLog,
        ApiErrorLog,
        FeedbackReport,
        ProcessingJob,
        User,
        UserRole,
        Webhook,
    )

    _register(client)
    _register(client, email="remove-users-domain@example.com")
    _register(client, email="smoke-users-domain@example.com")
    _register(client, email="real-users-domain@pdf-flow.com")

    db = next(client.app.dependency_overrides[get_db]())
    try:
        admin = db.query(User).filter(User.email == "admin-users-domain@example.com").first()
        admin.role = UserRole.ADMIN
        remove_user = db.query(User).filter(
            User.email == "remove-users-domain@example.com"
        ).first()
        test_user = db.query(User).filter(
            User.email == "smoke-users-domain@example.com"
        ).first()
        real_user = db.query(User).filter(
            User.email == "real-users-domain@pdf-flow.com"
        ).first()
        db.commit()

        with pytest.raises(HTTPException) as self_delete_error:
            delete_user(db, user_id=admin.id, request=_request_stub(), admin=admin)
        assert self_delete_error.value.status_code == 400

        delete_user(db, user_id=remove_user.id, request=_request_stub(), admin=admin)
        assert db.query(User).filter(User.email == "remove-users-domain@example.com").first() is None

        db.add_all([
            FeedbackReport(
                user_id=test_user.id,
                title="test feedback",
                message="keep report and detach user",
            ),
            ApiErrorLog(
                user_id=test_user.id,
                method="POST",
                path="/api/v1/test",
                status_code=500,
            ),
            ProcessingJob(
                job_id="job_users_domain_cleanup",
                user_id=test_user.id,
                job_type="merge_pdf",
                status="failed",
                progress=25,
                input_file_name="sample.pdf",
                input_file_size=1024,
            ),
            Webhook(
                user_id=test_user.id,
                url="https://example.com/webhook",
                events='["job.failed"]',
            ),
        ])
        db.commit()

        cleaned = cleanup_test_users(db, request=_request_stub(), admin=admin)
        remaining_emails = [item["email"] for item in list_users(db, limit=100)]

        assert cleaned["deleted_count"] == 1
        assert cleaned["deleted_emails"] == ["smoke-users-domain@example.com"]
        assert cleaned["remaining_test_users_count"] == 0
        assert "smoke-users-domain@example.com" not in remaining_emails
        assert "real-users-domain@pdf-flow.com" in remaining_emails
        assert db.query(User).filter(User.id == real_user.id).first() is not None
        assert db.query(FeedbackReport).filter(
            FeedbackReport.title == "test feedback"
        ).first().user_id is None
        assert db.query(ApiErrorLog).filter(ApiErrorLog.path == "/api/v1/test").first().user_id is None
        assert db.query(ProcessingJob).filter(
            ProcessingJob.job_id == "job_users_domain_cleanup"
        ).first() is None
        assert db.query(Webhook).filter(Webhook.url == "https://example.com/webhook").first() is None

        audits = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at).all()
        assert [item.action for item in audits[-2:]] == ["delete", "cleanup"]
    finally:
        db.close()
