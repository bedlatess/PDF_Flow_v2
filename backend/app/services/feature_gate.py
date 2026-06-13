"""Feature flag access checks shared by public and admin-facing routes."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.account.entitlements import has_active_subscription, role_value
from app.models.user import FeatureFlag, User, UserRole
from app.services.site_state import get_maintenance_message, is_maintenance_mode_enabled


DEFAULT_FEATURE_FLAGS = [
    ("merge_pdf", "合并 PDF", "允许用户合并多个 PDF 文件。", True, False, False),
    ("split_pdf", "拆分 PDF", "允许用户按页码拆分 PDF。", True, False, False),
    ("compress_pdf", "压缩 PDF", "允许用户压缩 PDF 文件。", True, False, False),
    ("rotate_pdf", "旋转 PDF", "允许用户旋转 PDF 页面。", True, False, False),
    ("image_to_pdf", "图片转 PDF", "允许用户将图片转换为 PDF。", True, False, False),
    ("pdf_to_image", "PDF 转图片", "允许用户将 PDF 页面导出为图片。", True, False, False),
    ("delete_pages_pdf", "删除 PDF 页面", "允许用户移除 PDF 中不需要的页面。", True, False, False),
    ("organize_pdf", "整理 PDF 页面", "允许用户调整 PDF 页面顺序。", True, False, False),
    ("page_numbers_pdf", "添加 PDF 页码", "允许用户为 PDF 添加页码。", True, False, False),
    ("crop_pdf", "裁剪 PDF", "允许用户在浏览器本地裁剪 PDF 可视区域。", True, False, False),
    ("flatten_pdf", "扁平化 PDF", "允许用户在浏览器本地将可填写表单固化为普通页面内容。", True, False, False),
    ("repair_pdf", "修复 PDF", "允许登录用户在服务器上重新整理可读取的 PDF 结构。", True, True, False),
    ("protect_pdf", "保护 PDF", "允许登录用户为 PDF 添加打开密码。", True, True, False),
    ("unlock_pdf", "解锁 PDF", "允许登录用户在知道密码的前提下移除 PDF 打开密码。", True, True, False),
    ("sign_pdf", "签署 PDF", "允许用户在浏览器本地为 PDF 添加可视签名图片。", True, False, False),
    ("extract_text_pdf", "提取 PDF 文字", "允许用户在浏览器本地从文本型 PDF 提取可复制文字。", True, False, False),
    ("extract_images_pdf", "提取 PDF 图片", "允许用户在浏览器本地从 PDF 提取内嵌图片资源。", True, False, False),
    ("ocr_pdf", "OCR 文字识别", "允许登录用户提交 OCR 识别任务。", True, True, True),
    ("office_to_pdf", "Office 转 PDF", "允许登录用户将 Office 文件转换为 PDF。", True, True, False),
    ("ai_analyzer", "AI PDF 分析器", "允许 Pro 用户进行 PDF 智能分析。", True, True, True),
    ("fill_form", "PDF 表单填写", "允许 Pro 用户填写 PDF 表单。", True, True, True),
    ("annotate_pdf", "PDF 标注", "允许 Pro 用户添加 PDF 标注。", True, True, True),
    ("watermark_pdf", "添加水印", "允许用户为 PDF 添加水印。", True, False, False),
]


def can_use_pro_feature(user: User | None) -> bool:
    return has_active_subscription(user)


def seed_default_feature_flags(db: Session) -> None:
    if db.query(FeatureFlag).count() > 0:
        return

    db.add_all(
        FeatureFlag(
            key=key,
            label=label,
            description=description,
            enabled=enabled,
            requires_login=requires_login,
            requires_pro=requires_pro,
        )
        for key, label, description, enabled, requires_login, requires_pro in DEFAULT_FEATURE_FLAGS
    )
    db.commit()


def get_feature_flag(db: Session, key: str) -> FeatureFlag | None:
    return db.query(FeatureFlag).filter(FeatureFlag.key == key).first()


def get_or_create_feature_flag(db: Session, key: str) -> FeatureFlag | None:
    flag = get_feature_flag(db, key)
    if flag is not None:
        return flag

    default = next((item for item in DEFAULT_FEATURE_FLAGS if item[0] == key), None)
    if default is None:
        return None

    _, label, description, enabled, requires_login, requires_pro = default
    flag = FeatureFlag(
        key=key,
        label=label,
        description=description,
        enabled=enabled,
        requires_login=requires_login,
        requires_pro=requires_pro,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def require_feature_access(
    db: Session,
    feature_key: str,
    current_user: User | None = None,
) -> FeatureFlag | None:
    """Enforce feature flag rules before executing a feature."""
    if is_maintenance_mode_enabled(db) and role_value(current_user) != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_maintenance_message(db),
        )

    flag = get_or_create_feature_flag(db, feature_key)
    if flag is None:
        return None

    if not flag.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=flag.maintenance_message or "This feature is temporarily unavailable.",
        )

    if flag.requires_login and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to use this feature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if flag.requires_pro and not can_use_pro_feature(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires Pro access.",
        )

    return flag
