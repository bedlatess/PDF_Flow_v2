"""Feature flag access checks shared by public and admin-facing routes."""

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.account.entitlements import has_active_subscription, role_value
from app.models.user import FeatureFlag, User, UserRole
from app.services.site_state import get_maintenance_message, is_maintenance_mode_enabled


@dataclass(frozen=True)
class DefaultFeatureFlag:
    key: str
    label: str
    description: str
    enabled: bool = True
    is_public: bool = True
    requires_login: bool = False
    requires_pro: bool = False
    free_daily_limit: int | None = 10
    free_max_file_size_mb: int | None = 25
    free_batch_file_limit: int | None = 5
    pro_daily_limit: int | None = 200
    pro_max_file_size_mb: int | None = 200
    pro_batch_file_limit: int | None = 25
    pro_unlimited: bool = False


DEFAULT_FEATURE_FLAGS = [
    DefaultFeatureFlag("merge_pdf", "Merge PDF", "Merge multiple PDF files into one document."),
    DefaultFeatureFlag("split_pdf", "Split PDF", "Split a PDF into selected page ranges."),
    DefaultFeatureFlag("compress_pdf", "Compress PDF", "Reduce PDF file size."),
    DefaultFeatureFlag("rotate_pdf", "Rotate PDF", "Rotate PDF pages."),
    DefaultFeatureFlag("image_to_pdf", "Image to PDF", "Convert images into a PDF."),
    DefaultFeatureFlag("pdf_to_image", "PDF to Image", "Export PDF pages as images."),
    DefaultFeatureFlag("pdf_to_word", "PDF to Word", "Convert text-based PDFs to DOCX Beta.", requires_login=True),
    DefaultFeatureFlag("pdf_to_excel", "PDF to Excel", "Convert simple text-based PDF tables to XLSX Beta.", requires_login=True),
    DefaultFeatureFlag("batch_convert", "Batch Convert", "Submit multiple Word/Excel conversion tasks.", requires_login=True),
    DefaultFeatureFlag("html_to_pdf", "HTML to PDF", "Convert a public URL or pasted HTML into a PDF.", requires_login=True),
    DefaultFeatureFlag("delete_pages_pdf", "Delete PDF Pages", "Remove unwanted pages from a PDF."),
    DefaultFeatureFlag("organize_pdf", "Organize PDF", "Reorder PDF pages."),
    DefaultFeatureFlag("page_numbers_pdf", "Add Page Numbers", "Add page numbers to a PDF."),
    DefaultFeatureFlag("crop_pdf", "Crop PDF", "Crop visible PDF page areas in the browser."),
    DefaultFeatureFlag("flatten_pdf", "Flatten PDF", "Flatten fillable form content into regular PDF pages."),
    DefaultFeatureFlag("repair_pdf", "Repair PDF", "Rebuild a readable PDF structure on the server.", requires_login=True),
    DefaultFeatureFlag("protect_pdf", "Protect PDF", "Add an open password to a PDF.", requires_login=True),
    DefaultFeatureFlag("unlock_pdf", "Unlock PDF", "Remove a known PDF open password.", requires_login=True),
    DefaultFeatureFlag("sign_pdf", "Sign PDF", "Add a visual signature image in the browser."),
    DefaultFeatureFlag("extract_text_pdf", "Extract PDF Text", "Extract copyable text from a text-based PDF in the browser."),
    DefaultFeatureFlag("extract_images_pdf", "Extract PDF Images", "Extract embedded images from a PDF in the browser."),
    DefaultFeatureFlag("watermark_pdf", "Watermark PDF", "Add a watermark to a PDF."),
    DefaultFeatureFlag("ocr_pdf", "OCR PDF", "Submit an OCR text recognition task.", requires_login=True, requires_pro=True),
    DefaultFeatureFlag("office_to_pdf", "Office to PDF", "Convert Office documents to PDF.", requires_login=True),
    DefaultFeatureFlag("ai_analyzer", "AI PDF Analyzer", "Analyze PDFs with AI.", requires_login=True, requires_pro=True),
    DefaultFeatureFlag("fill_form", "Fill PDF Form", "Fill PDF forms.", requires_login=True, requires_pro=True),
    DefaultFeatureFlag("annotate_pdf", "Annotate PDF", "Add PDF annotations.", requires_login=True, requires_pro=True),
]

DEFAULT_FEATURE_FLAGS_BY_KEY = {item.key: item for item in DEFAULT_FEATURE_FLAGS}


def can_use_pro_feature(user: User | None) -> bool:
    return has_active_subscription(user)


def _feature_flag_kwargs(item: DefaultFeatureFlag) -> dict:
    return {
        "key": item.key,
        "label": item.label,
        "description": item.description,
        "enabled": item.enabled,
        "is_public": item.is_public,
        "requires_login": item.requires_login,
        "requires_pro": item.requires_pro,
        "free_daily_limit": item.free_daily_limit,
        "free_max_file_size_mb": item.free_max_file_size_mb,
        "free_batch_file_limit": item.free_batch_file_limit,
        "pro_daily_limit": item.pro_daily_limit,
        "pro_max_file_size_mb": item.pro_max_file_size_mb,
        "pro_batch_file_limit": item.pro_batch_file_limit,
        "pro_unlimited": item.pro_unlimited,
    }


def _apply_missing_default_limits(flag: FeatureFlag, default: DefaultFeatureFlag) -> bool:
    changed = False
    for field in (
        "free_daily_limit",
        "free_max_file_size_mb",
        "free_batch_file_limit",
        "pro_daily_limit",
        "pro_max_file_size_mb",
        "pro_batch_file_limit",
    ):
        if getattr(flag, field, None) is None:
            setattr(flag, field, getattr(default, field))
            changed = True
    if getattr(flag, "pro_unlimited", None) is None:
        flag.pro_unlimited = default.pro_unlimited
        changed = True
    return changed


def seed_default_feature_flags(db: Session) -> None:
    existing_flags = {item.key: item for item in db.query(FeatureFlag).all()}
    if not existing_flags:
        db.add_all(FeatureFlag(**_feature_flag_kwargs(item)) for item in DEFAULT_FEATURE_FLAGS)
        db.commit()
        return

    changed = False
    for item in DEFAULT_FEATURE_FLAGS:
        flag = existing_flags.get(item.key)
        if flag is None:
            db.add(FeatureFlag(**_feature_flag_kwargs(item)))
            changed = True
            continue
        if flag.label.startswith(("鍚", "鎷", "PDF 杞")):
            flag.label = item.label
            flag.description = item.description
            changed = True
        changed = _apply_missing_default_limits(flag, item) or changed

    if changed:
        db.commit()


def get_feature_flag(db: Session, key: str) -> FeatureFlag | None:
    return db.query(FeatureFlag).filter(FeatureFlag.key == key).first()


def get_or_create_feature_flag(db: Session, key: str) -> FeatureFlag | None:
    flag = get_feature_flag(db, key)
    if flag is not None:
        default = DEFAULT_FEATURE_FLAGS_BY_KEY.get(key)
        if default and _apply_missing_default_limits(flag, default):
            db.commit()
            db.refresh(flag)
        return flag

    default = DEFAULT_FEATURE_FLAGS_BY_KEY.get(key)
    if default is None:
        return None

    flag = FeatureFlag(**_feature_flag_kwargs(default))
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
