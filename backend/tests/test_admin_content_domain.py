"""Admin content/settings domain tests."""


def _register(client, email="admin-content@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Admin Content",
    })


def test_admin_content_domain_seeds_public_config_and_updates_with_audit(client):
    from app.core.database import get_db
    from app.domains.admin.content import (
        get_public_config,
        list_content_blocks,
        list_feature_flags,
        list_settings,
        update_content_block,
        update_feature_flag,
        update_setting,
    )
    from app.models.user import AdminAuditLog, ContentBlock, User, UserRole
    from app.schemas.admin import ContentBlockUpdate, FeatureFlagUpdate, SiteSettingUpdate

    _register(client)
    db = next(client.app.dependency_overrides[get_db]())
    try:
        admin = db.query(User).filter(User.email == "admin-content@example.com").first()
        admin.role = UserRole.ADMIN
        legacy = ContentBlock(
            key="privacy_policy",
            locale="zh",
            title="旧标题",
            content="由后台接管后，可在这里维护隐私政策正文。",
        )
        db.add(legacy)
        db.commit()

        request = type("RequestStub", (), {
            "client": type("ClientStub", (), {"host": "127.0.0.1"})(),
            "headers": {"user-agent": "domain-test"},
        })()

        public_config = get_public_config(db)
        assert public_config["settings"]["support_email"]["value"] == "support@pdf-flow.com"
        assert public_config["settings"]["site_name"]["label"] == "站点名称"
        assert public_config["content_blocks"]["home_hero:zh"]["content"].startswith("隐私优先")
        assert public_config["content_blocks"]["privacy_policy:zh"]["content"].startswith("我们不会出售")

        settings = list_settings(db)
        flags = list_feature_flags(db)
        blocks = list_content_blocks(db)
        assert any(item.key == "maintenance_mode" for item in settings)
        assert any(item.key == "merge_pdf" for item in flags)
        assert any(item.key == "terms_of_service" and item.locale == "zh" for item in blocks)

        setting = update_setting(
            db,
            key="global_announcement",
            payload=SiteSettingUpdate(
                value="系统维护测试中",
                value_type="textarea",
                group="notice",
                label="全站公告",
                description="测试公告",
                is_public=True,
            ),
            request=request,
            admin=admin,
        )
        flag = update_feature_flag(
            db,
            key="merge_pdf",
            payload=FeatureFlagUpdate(
                label="合并 PDF",
                description="允许用户合并多个 PDF 文件。",
                enabled=False,
                requires_login=False,
                requires_pro=False,
                maintenance_message="合并功能维护中",
            ),
            request=request,
            admin=admin,
        )
        block = update_content_block(
            db,
            key="home_hero",
            locale="zh",
            payload=ContentBlockUpdate(
                locale="zh",
                title="PDF-Flow",
                content="新的首页文案",
                description="首页首屏",
                is_public=True,
            ),
            request=request,
            admin=admin,
        )

        assert setting.value == "系统维护测试中"
        assert flag.enabled is False
        assert block.content == "新的首页文案"

        audit_targets = [
            item.target_type
            for item in db.query(AdminAuditLog).order_by(AdminAuditLog.created_at).all()
        ]
        assert audit_targets[-3:] == ["site_setting", "feature_flag", "content_block"]
    finally:
        db.close()
