"""Email/password authentication domain tests."""

from fastapi import BackgroundTasks


def test_auth_domain_register_login_refresh_and_current_user(client):
    from app.core.database import get_db
    from app.domains.auth.service import (
        get_current_user_from_token,
        get_optional_user_from_token,
        login_user,
        parse_token_user_id,
        refresh_token_pair,
        register_user,
    )
    from app.models.user import User
    from app.schemas.user import UserCreate

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = register_user(
            db,
            user_data=UserCreate(
                email="auth-domain@example.com",
                password="SecurePass123!",
                full_name="Auth Domain",
            ),
            background_tasks=BackgroundTasks(),
        )
        assert user.id is not None
        assert user.role.value == "free"

        tokens = login_user(
            db,
            email="auth-domain@example.com",
            password="SecurePass123!",
        )
        assert tokens["token_type"] == "bearer"
        assert parse_token_user_id(tokens["access_token"]) == user.id

        current = get_current_user_from_token(db, tokens["access_token"])
        assert current.email == "auth-domain@example.com"
        assert get_optional_user_from_token(db, None) is None
        assert get_optional_user_from_token(db, "garbage") is None

        refreshed = refresh_token_pair(db, refresh_token=tokens["refresh_token"])
        assert parse_token_user_id(refreshed["access_token"]) == user.id

        persisted = db.query(User).filter(User.email == "auth-domain@example.com").first()
        assert persisted.last_login_at is not None
    finally:
        db.close()


def test_auth_domain_password_reset_and_inactive_user_guards(client):
    import pytest
    from fastapi import HTTPException

    from app.core.database import get_db
    from app.core.security import create_access_token, verify_password
    from app.domains.auth.service import register_user
    from app.domains.auth.service import (
        get_current_user_from_token,
        login_user,
        request_password_reset,
        reset_password,
    )
    from app.models.user import User
    from app.schemas.user import PasswordResetConfirm, PasswordResetRequest, UserCreate

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = register_user(
            db,
            user_data=UserCreate(
                email="reset-domain@example.com",
                password="SecurePass123!",
                full_name="Reset Domain",
            ),
            background_tasks=BackgroundTasks(),
        )

        response = request_password_reset(
            db,
            request=PasswordResetRequest(email="reset-domain@example.com"),
            background_tasks=BackgroundTasks(),
        )
        assert "password reset link" in response["message"]

        token = create_access_token(data={"sub": user.id, "type": "password_reset"})
        reset_password(
            db,
            request=PasswordResetConfirm(
                token=token,
                new_password="NewSecurePass123!",
            ),
        )
        db.refresh(user)
        assert verify_password("NewSecurePass123!", user.hashed_password)

        inactive_token = create_access_token(data={"sub": user.id})
        user.is_active = False
        db.commit()

        with pytest.raises(HTTPException) as login_error:
            login_user(db, email="reset-domain@example.com", password="NewSecurePass123!")
        assert login_error.value.status_code == 403

        with pytest.raises(HTTPException) as current_error:
            get_current_user_from_token(db, inactive_token)
        assert current_error.value.status_code == 403

        inactive = db.query(User).filter(User.email == "reset-domain@example.com").first()
        assert inactive.is_active is False
    finally:
        db.close()


def test_auth_domain_oauth_user_creation_linking_and_redirects(client):
    import pytest
    from fastapi import HTTPException

    from app.core.database import get_db
    from app.core.security import verify_password
    from app.domains.auth.service import (
        get_or_create_oauth_user,
        link_oauth_identity,
        oauth_callback_redirect_url,
        oauth_error_redirect_url,
        oauth_link_result_redirect_url,
        register_user,
        token_pair_for_user,
    )
    from app.models.user import User
    from app.schemas.user import UserCreate

    db = next(client.app.dependency_overrides[get_db]())
    try:
        oauth_user = get_or_create_oauth_user(
            db,
            provider="google",
            oauth_id="google-123",
            email="oauth-domain@example.com",
            full_name="OAuth Domain",
        )
        assert oauth_user.is_verified is True
        assert oauth_user.oauth_provider == "google"
        assert oauth_user.oauth_id == "google-123"
        assert verify_password("not-the-random-password", oauth_user.hashed_password) is False

        existing_login_time = oauth_user.last_login_at
        same_user = get_or_create_oauth_user(
            db,
            provider="google",
            oauth_id="google-123",
            email="oauth-domain@example.com",
        )
        assert same_user.id == oauth_user.id
        assert same_user.last_login_at >= existing_login_time

        password_user = register_user(
            db,
            user_data=UserCreate(
                email="link-existing@example.com",
                password="SecurePass123!",
                full_name="Link Existing",
            ),
            background_tasks=BackgroundTasks(),
        )
        linked_user = get_or_create_oauth_user(
            db,
            provider="github",
            oauth_id="github-456",
            email="link-existing@example.com",
            full_name="Ignored",
        )
        assert linked_user.id == password_user.id
        assert linked_user.oauth_provider == "github"
        assert linked_user.oauth_id == "github-456"
        assert linked_user.is_verified is True

        other_user = register_user(
            db,
            user_data=UserCreate(
                email="other-oauth-link@example.com",
                password="SecurePass123!",
                full_name="Other Link",
            ),
            background_tasks=BackgroundTasks(),
        )
        with pytest.raises(HTTPException) as conflict:
            link_oauth_identity(
                db,
                user=other_user,
                provider="github",
                oauth_id="github-456",
            )
        assert conflict.value.status_code == 400

        link_oauth_identity(
            db,
            user=other_user,
            provider="google",
            oauth_id="google-789",
        )
        refreshed_other = db.query(User).filter(User.id == other_user.id).first()
        assert refreshed_other.oauth_provider == "google"
        assert refreshed_other.oauth_id == "google-789"

        token_pair = token_pair_for_user(oauth_user)
        callback_url = oauth_callback_redirect_url(
            frontend_url="https://app.pdf-flow.test",
            token_pair=token_pair,
        )
        assert callback_url.startswith("https://app.pdf-flow.test/auth/oauth-callback?")
        assert "token_type=bearer" in callback_url
        assert oauth_error_redirect_url(
            frontend_url="https://app.pdf-flow.test",
            provider="github bad",
        ).endswith("error=oauth_failed&provider=github+bad")
        assert oauth_link_result_redirect_url(
            frontend_url="https://app.pdf-flow.test",
            success=True,
        ) == "https://app.pdf-flow.test/profile?oauth_linked=success"
    finally:
        db.close()
