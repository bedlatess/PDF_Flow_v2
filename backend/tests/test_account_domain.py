from datetime import datetime, timedelta


def _register(client, email="account@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Account User",
    })


def _login(client, email="account@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })


def _auth_headers(client, email="account@example.com", password="SecurePass123!"):
    _register(client, email=email, password=password)
    token = _login(client, email=email, password=password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_account_stats_apply_free_quota_and_storage_sum(client):
    from app.core.database import get_db
    from app.core.config import settings
    from app.models.user import UsageLog, User

    email = "stats@example.com"
    headers = _auth_headers(client, email=email)

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == email).first()
        db.add_all([
            UsageLog(
                user_id=user.id,
                endpoint="/api/v1/files/upload",
                method="POST",
                file_size=100,
                success=True,
                created_at=datetime.utcnow(),
            ),
            UsageLog(
                user_id=user.id,
                endpoint="/api/v1/files/merge",
                method="POST",
                file_size=200,
                success=True,
                created_at=datetime.utcnow(),
            ),
            UsageLog(
                user_id=user.id,
                endpoint="/api/v1/files/old",
                method="POST",
                file_size=300,
                success=True,
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
            UsageLog(
                user_id=user.id,
                endpoint="/api/v1/auth/me",
                method="GET",
                file_size=None,
                success=True,
                created_at=datetime.utcnow(),
            ),
        ])
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/users/me/stats", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 4
    assert body["requests_today"] == 3
    assert body["storage_used"] == 600
    assert body["quota_limit"] == settings.RATE_LIMIT_FREE
    assert body["quota_remaining"] == max(0, settings.RATE_LIMIT_FREE - 3)
    assert body["role"] == "free"


def test_account_stats_treats_non_free_plans_as_unlimited(client):
    from app.core.database import get_db
    from app.models.user import User, UserRole

    email = "pro-stats@example.com"
    headers = _auth_headers(client, email=email)

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == email).first()
        user.role = UserRole.PRO
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/users/me/stats", headers=headers)

    assert response.status_code == 200
    assert response.json()["quota_limit"] == -1
    assert response.json()["quota_remaining"] == -1
    assert response.json()["role"] == "pro"


def test_account_update_changes_name_and_password(client):
    from app.core.database import get_db
    from app.core.security import verify_password
    from app.models.user import User

    email = "update@example.com"
    headers = _auth_headers(client, email=email)

    response = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"full_name": "Updated User", "password": "NewSecurePass123!"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated User"

    assert _login(client, email=email, password="SecurePass123!").status_code == 401
    assert _login(client, email=email, password="NewSecurePass123!").status_code == 200

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == email).first()
        assert verify_password("NewSecurePass123!", user.hashed_password)
    finally:
        db.close()


def test_account_delete_removes_current_user(client):
    from app.core.database import get_db
    from app.models.user import User

    email = "delete@example.com"
    headers = _auth_headers(client, email=email)

    response = client.delete("/api/v1/users/me", headers=headers)

    assert response.status_code == 204
    assert _login(client, email=email).status_code == 401

    db = next(client.app.dependency_overrides[get_db]())
    try:
        assert db.query(User).filter(User.email == email).first() is None
    finally:
        db.close()
