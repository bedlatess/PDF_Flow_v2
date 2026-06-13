from datetime import datetime, timedelta


def test_entitlement_rules_for_manual_and_expired_plans(client):
    from app.domains.account.entitlements import effective_role
    from app.models.user import User, UserRole
    from app.services.feature_gate import can_use_pro_feature

    manual = User(
        email="manual-entitlement@example.com",
        hashed_password="x",
        role=UserRole.PRO,
        subscription_status="manual",
        subscription_end_date=datetime.utcnow() + timedelta(days=7),
    )
    expired = User(
        email="expired-entitlement@example.com",
        hashed_password="x",
        role=UserRole.PRO,
        subscription_status="expired",
        subscription_end_date=datetime.utcnow() - timedelta(days=1),
    )
    canceled = User(
        email="canceled-entitlement@example.com",
        hashed_password="x",
        role=UserRole.PRO,
        subscription_status="canceled",
        subscription_end_date=datetime.utcnow() + timedelta(days=7),
    )

    assert can_use_pro_feature(manual) is True
    assert effective_role(manual) == "pro"
    assert can_use_pro_feature(expired) is False
    assert effective_role(expired) == "free"
    assert can_use_pro_feature(canceled) is False
    assert effective_role(canceled) == "free"
