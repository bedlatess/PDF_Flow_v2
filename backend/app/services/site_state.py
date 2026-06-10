"""Shared site-wide operational state helpers."""
from sqlalchemy.orm import Session

from app.models.user import SiteSetting


def parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def get_site_setting(db: Session, key: str) -> SiteSetting | None:
    return db.query(SiteSetting).filter(SiteSetting.key == key).first()


def get_site_setting_value(db: Session, key: str, fallback: str = "") -> str:
    setting = get_site_setting(db, key)
    if setting is None:
        return fallback
    return setting.value or fallback


def is_maintenance_mode_enabled(db: Session) -> bool:
    return parse_bool(get_site_setting_value(db, "maintenance_mode", "false"))


def get_maintenance_message(db: Session) -> str:
    announcement = get_site_setting_value(db, "global_announcement").strip()
    if announcement:
        return announcement
    return "站点正在维护中，请稍后再试。"
