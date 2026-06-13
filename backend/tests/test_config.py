from app.core.config import Settings


def _settings(**overrides):
    values = {
        "SECRET_KEY": "test-secret-key-for-config",
        "DATABASE_URL": "sqlite:///./test_pdfflow.db",
    }
    values.update(overrides)
    return Settings(**values)


def test_cors_allowed_origins_include_public_and_admin_frontends():
    settings = _settings(
        ALLOWED_ORIGINS="https://extra.pdf-flow.test",
        FRONTEND_URL="https://app.pdf-flow.test",
        ADMIN_FRONTEND_URL="https://admin.pdf-flow.test",
    )

    assert settings.CORS_ALLOWED_ORIGINS == [
        "https://extra.pdf-flow.test",
        "https://app.pdf-flow.test",
        "https://admin.pdf-flow.test",
    ]


def test_cors_allowed_origins_preserve_wildcard():
    settings = _settings(ALLOWED_ORIGINS="*")

    assert settings.CORS_ALLOWED_ORIGINS == ["*"]
