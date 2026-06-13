"""
认证流程集成测试（SQLite + TestClient + stubbed infra）
端到端验证：注册 → 登录 → 获取用户 → 刷新 → 鉴权失败路径
"""


def _register(client, email="user@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User",
    })


def _login(client, email="user@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_session_middleware_is_available_for_oauth(self, client):
        from starlette.middleware.sessions import SessionMiddleware

        assert any(
            middleware.cls is SessionMiddleware
            for middleware in client.app.user_middleware
        )


class TestRegister:
    def test_register_success(self, client):
        r = _register(client)
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "user@example.com"
        assert body["role"] == "free"
        assert "hashed_password" not in body  # 不泄露密码哈希

    def test_register_persists_lowercase_role_value(self, client):
        from app.core.database import get_db
        from app.models.user import User

        r = _register(client, email="rolecheck@example.com")
        assert r.status_code == 201

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "rolecheck@example.com").first()
            assert user is not None
            assert user.role.value == "free"
        finally:
            db.close()

    def test_register_duplicate_email(self, client):
        _register(client)
        r = _register(client)
        assert r.status_code == 400

    def test_register_short_password(self, client):
        r = client.post("/api/v1/auth/register", json={
            "email": "x@y.com", "password": "short", "full_name": "X",
        })
        assert r.status_code == 422  # pydantic min_length=8


class TestLogin:
    def test_login_success(self, client):
        _register(client)
        r = _login(client)
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        _register(client)
        r = _login(client, password="WrongPass123")
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = _login(client, email="ghost@example.com")
        assert r.status_code == 401


class TestProtectedEndpoints:
    def test_me_with_token(self, client):
        _register(client)
        token = _login(client).json()["access_token"]
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "user@example.com"

    def test_me_without_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_with_bad_token(self, client):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_optional_auth_returns_none_without_token(self, client):
        from app.api.v1.endpoints.auth import get_current_user_optional
        from app.core.database import get_db

        db = next(client.app.dependency_overrides[get_db]())
        try:
            assert get_current_user_optional(token=None, db=db) is None
        finally:
            db.close()

    def test_stats_after_login(self, client):
        _register(client)
        token = _login(client).json()["access_token"]
        r = client.get("/api/v1/users/me/stats", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "free"
        assert body["quota_limit"] >= 0  # free 有配额上限

    def test_stats_sums_usage_log_file_sizes(self, client):
        from app.core.database import get_db
        from app.models.user import UsageLog, User

        _register(client, email="storage@example.com")
        token = _login(client, email="storage@example.com").json()["access_token"]

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "storage@example.com").first()
            db.add_all([
                UsageLog(
                    user_id=user.id,
                    endpoint="/api/v1/files/upload",
                    method="POST",
                    file_size=1024,
                    success=True,
                ),
                UsageLog(
                    user_id=user.id,
                    endpoint="/api/v1/files/merge",
                    method="POST",
                    file_size=2048,
                    success=True,
                ),
                UsageLog(
                    user_id=user.id,
                    endpoint="/api/v1/auth/me",
                    method="GET",
                    file_size=None,
                    success=True,
                ),
            ])
            db.commit()
        finally:
            db.close()

        r = client.get("/api/v1/users/me/stats", headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 200
        assert r.json()["storage_used"] == 3072


class TestRefresh:
    def test_refresh_returns_new_tokens(self, client):
        _register(client)
        refresh = _login(client).json()["refresh_token"]
        r = client.post("/api/v1/auth/refresh", params={"refresh_token": refresh})
        assert r.status_code == 200
        assert "access_token" in r.json()
