"""Admin operations/diagnostics domain tests."""

from datetime import datetime
import os
import time


def _register(client, email="admin-ops-domain@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Admin Ops Domain",
    })


def _request_stub():
    return type("RequestStub", (), {
        "client": type("ClientStub", (), {"host": "127.0.0.1"})(),
        "headers": {"user-agent": "domain-test"},
    })()


def test_admin_operations_domain_reports_health_jobs_and_diagnostics(client):
    from app.core.database import get_db
    from app.domains.admin.operations import (
        build_diagnostic_summary,
        get_diagnostics,
        get_health_report,
        get_maintenance_summary,
        get_operations_overview,
        list_api_errors,
        list_jobs,
    )
    from app.models.user import ApiErrorLog, FeedbackReport, ProcessingJob, User, UserRole
    from app.services.file_service import file_processing_service

    _register(client)
    _register(client, email="smoke-ops-domain@example.com")

    file_processing_service._save_job_status("job_ops_domain_redis_failed", {
        "job_id": "job_ops_domain_redis_failed",
        "status": "failed",
        "progress": 40,
        "message": "OCR job queued",
        "created_at": time.time(),
        "updated_at": time.time(),
        "error": "redacted redis failure",
    })

    db = next(client.app.dependency_overrides[get_db]())
    try:
        admin = db.query(User).filter(User.email == "admin-ops-domain@example.com").first()
        admin.role = UserRole.ADMIN
        db.add_all([
            ProcessingJob(
                job_id="job_ops_domain_db_failed",
                user_id=admin.id,
                job_type="merge_pdf",
                status="failed",
                progress=25,
                input_file_name="private-input.pdf",
                input_file_size=2048,
                error_message="database job failure",
            ),
            ApiErrorLog(
                user_id=admin.id,
                request_id="req_ops_domain",
                method="POST",
                path="/api/v1/domain-error",
                query_string="debug=true",
                status_code=500,
                error_type="RuntimeError",
                error_message="observable domain failure without body payload",
            ),
            FeedbackReport(
                user_id=admin.id,
                title="live acceptance ops domain",
                message="synthetic probe",
                page_url="https://pdf-flow.test/tools/merge?token=secret",
                diagnostic_code="OPS-DOMAIN",
            ),
        ])
        db.commit()

        operations = get_operations_overview(db)
        health = get_health_report(db)
        jobs = list_jobs(db, status_filter="failed", limit=10)
        errors = list_api_errors(db, limit=5)
        diagnostics = get_diagnostics(db)
        maintenance = get_maintenance_summary(db, admin=admin)
        summary = build_diagnostic_summary(
            generated_at=datetime.utcnow(),
            services=operations["services"],
            errors=errors,
            failed_jobs=jobs,
            feedback=db.query(FeedbackReport).all(),
            open_feedback_count=1,
            failed_jobs_count=len(jobs),
            api_error_count=len(errors),
        )

        assert operations["services"]["database"]["status"] == "healthy"
        assert operations["services"]["redis"]["status"] == "healthy"
        assert operations["total_users"] == 2
        assert operations["test_users"] == 2
        assert health["users_count"] == 2
        assert health["api_error_count"] == 1
        assert health["recent_error_path"] == "/api/v1/domain-error"
        assert {job["job_id"] for job in jobs} >= {
            "job_ops_domain_redis_failed",
            "job_ops_domain_db_failed",
        }
        assert errors[0].request_id == "req_ops_domain"
        assert diagnostics["open_feedback_count"] == 1
        assert diagnostics["failed_jobs_count"] >= 2
        assert diagnostics["api_error_count"] == 1
        assert "PDF-Flow diagnostic packet" in diagnostics["diagnostic_summary"]
        assert "request bodies and document contents are not included" in diagnostics["diagnostic_summary"]
        assert "token=secret" not in diagnostics["diagnostic_summary"]
        assert "req_ops_domain" in summary
        assert "observable domain failure" in summary
        assert "token=secret" not in summary
        assert "raw payload" not in summary.lower()
        assert maintenance["test_users_count"] == 1
        assert maintenance["live_acceptance_feedback_count"] == 1
        assert "file_retention" in maintenance
    finally:
        db.close()


def test_admin_operations_domain_cleanup_expired_files_audits_result(client, tmp_path, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.admin.operations import cleanup_expired_files
    from app.models.user import AdminAuditLog, User, UserRole

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "CLOUD_FILE_UPLOAD_TTL_SECONDS", 10)
    monkeypatch.setattr(settings, "CLOUD_FILE_RESULT_TTL_SECONDS", 10)
    monkeypatch.setattr(settings, "CLOUD_FILE_DOWNLOAD_TTL_SECONDS", 10)

    expired_upload = tmp_path / "file_ops_domain_old"
    keep_manual = tmp_path / "manual_docs"
    for directory in (expired_upload, keep_manual):
        directory.mkdir()
        (directory / "sample.pdf").write_bytes(b"%PDF-1.4")
    old_time = time.time() - 60
    os.utime(expired_upload, (old_time, old_time))

    _register(client)

    db = next(client.app.dependency_overrides[get_db]())
    try:
        admin = db.query(User).filter(User.email == "admin-ops-domain@example.com").first()
        admin.role = UserRole.ADMIN
        db.commit()

        result = cleanup_expired_files(db, request=_request_stub(), admin=admin)

        assert result["removed_count"] == 1
        assert not expired_upload.exists()
        assert keep_manual.exists()
        audit = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).first()
        assert audit.action == "cleanup"
        assert audit.target_type == "file_retention"
        assert audit.target_key == str(tmp_path)
        assert "removed=1" in audit.detail
    finally:
        db.close()


def test_admin_operations_prefers_db_job_when_redis_has_same_job_id(client):
    from app.core.database import get_db
    from app.domains.admin.operations import list_jobs
    from app.models.user import ProcessingJob, User
    from app.services.file_service import file_processing_service

    _register(client, email="admin-ops-dedupe@example.com")
    file_processing_service._save_job_status("job_dedupe", {
        "job_id": "job_dedupe",
        "status": "pending",
        "progress": 0,
        "message": "PDF compression job queued",
        "created_at": time.time(),
        "updated_at": time.time(),
    })

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == "admin-ops-dedupe@example.com").first()
        db.add(ProcessingJob(
            job_id="job_dedupe",
            user_id=user.id,
            job_type="compress_pdf",
            status="completed",
            progress=100,
            input_file_name="db-source.pdf",
            input_file_size=1234,
            output_file_url="/tmp/compressed.pdf",
        ))
        db.commit()

        jobs = list_jobs(db, status_filter=None, limit=10)
        matches = [job for job in jobs if job["job_id"] == "job_dedupe"]

        assert len(matches) == 1
        assert matches[0]["id"] is not None
        assert matches[0]["status"] == "completed"
        assert matches[0]["input_file_name"] == "db-source.pdf"
    finally:
        db.close()
