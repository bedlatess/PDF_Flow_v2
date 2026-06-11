"""
Advanced PDF endpoints
水印 / 表单填写 / 表单字段读取 / 注释 / 高亮 / 签名字段

注：基础水印已在前端纯本地实现（src/utils/pdf/watermark.ts）。
本端点为云端/企业 API 调用提供后端能力（表单、注释等需服务端 PyPDF2/reportlab）。
"""
import json
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body, Form
from fastapi.responses import FileResponse

from app.models.user import User, UserRole
from app.core.database import get_db
from app.schemas.advanced_pdf import (
    WatermarkRequest,
    SignatureFieldRequest,
)
from app.api.v1.endpoints.auth import get_current_user
from app.services.advanced_pdf_service import get_advanced_pdf_service
from app.services.feature_gate import require_feature_access
from sqlalchemy.orm import Session

router = APIRouter(prefix="/advanced", tags=["advanced-pdf"])


# ============================================================================
# Dependencies
# ============================================================================

async def require_pro_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user has Pro or Enterprise subscription"""
    if current_user.role not in [UserRole.PRO, UserRole.ENTERPRISE, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pro or Enterprise subscription required for advanced PDF features",
        )
    return current_user


def _validate_pdf(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )


async def _save_temp(file: UploadFile) -> str:
    """Save uploaded file to a temp path and return the path"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        return tmp.name


def _new_output_path() -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    return path


# ============================================================================
# Watermark
# ============================================================================

@router.post("/watermark")
async def add_watermark(
    file: UploadFile = File(...),
    request: WatermarkRequest = Body(...),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """
    Add a text watermark to a PDF (server-side).

    **Requires**: Pro or Enterprise subscription
    """
    require_feature_access(db, "watermark_pdf", current_user)
    _validate_pdf(file)
    input_path = await _save_temp(file)
    output_path = _new_output_path()

    try:
        service = get_advanced_pdf_service()
        service.add_watermark(
            pdf_path=input_path,
            output_path=output_path,
            watermark_text=request.text,
            opacity=request.opacity,
            rotation=request.rotation,
            font_size=request.font_size,
            position=request.position,
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="watermarked.pdf",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Watermark failed: {str(e)}",
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


# ============================================================================
# Form fields
# ============================================================================

@router.post("/form/fields")
async def get_form_fields(
    file: UploadFile = File(...),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """
    Read form field names and types from a PDF.

    **Requires**: Pro or Enterprise subscription
    """
    require_feature_access(db, "fill_form", current_user)
    _validate_pdf(file)
    input_path = await _save_temp(file)

    try:
        service = get_advanced_pdf_service()
        fields = service.get_form_fields(input_path)
        field_list = list(fields.values()) if isinstance(fields, dict) else fields
        return {
            "success": True,
            "has_form": len(field_list) > 0,
            "fields": field_list,
            "field_count": len(field_list),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read form fields: {str(e)}",
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


@router.post("/form/fill")
async def fill_form(
    file: UploadFile = File(...),
    form_data: str = Form(...),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """
    Fill PDF form fields.

    **Requires**: Pro or Enterprise subscription
    """
    require_feature_access(db, "fill_form", current_user)
    _validate_pdf(file)
    input_path = await _save_temp(file)
    output_path = _new_output_path()

    try:
        try:
            field_data = json.loads(form_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid form data payload",
            )

        service = get_advanced_pdf_service()
        service.fill_form(input_path, output_path, field_data)
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="filled.pdf",
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Form fill failed: {str(e)}",
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


# ============================================================================
# Annotations
# ============================================================================

@router.post("/annotate/text")
async def add_text_annotation(
    file: UploadFile = File(...),
    page_number: int = Form(...),
    text: str = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    width: float = Form(200),
    height: float = Form(100),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """
    Add a text annotation to a PDF page.

    **Requires**: Pro or Enterprise subscription
    """
    require_feature_access(db, "annotate_pdf", current_user)
    _validate_pdf(file)
    input_path = await _save_temp(file)
    output_path = _new_output_path()

    try:
        service = get_advanced_pdf_service()
        service.add_text_annotation(
            pdf_path=input_path,
            output_path=output_path,
            page_number=page_number,
            text=text,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="annotated.pdf",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Annotation failed: {str(e)}",
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


@router.post("/annotate/highlight")
async def add_highlight(
    file: UploadFile = File(...),
    page_number: int = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """
    Add a highlight annotation to a PDF page.

    **Requires**: Pro or Enterprise subscription
    """
    require_feature_access(db, "annotate_pdf", current_user)
    _validate_pdf(file)
    input_path = await _save_temp(file)
    output_path = _new_output_path()

    try:
        service = get_advanced_pdf_service()
        service.add_highlight(
            pdf_path=input_path,
            output_path=output_path,
            page_number=page_number,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="highlighted.pdf",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Highlight failed: {str(e)}",
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


# ============================================================================
# Signature field
# ============================================================================

@router.post("/signature/field")
async def add_signature_field(
    file: UploadFile = File(...),
    request: SignatureFieldRequest = Body(...),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """
    Add a (visual) signature field to a PDF page.

    Note: Cryptographic signing requires endesive/pyHanko (not included).

    **Requires**: Pro or Enterprise subscription
    """
    require_feature_access(db, "annotate_pdf", current_user)
    _validate_pdf(file)
    input_path = await _save_temp(file)
    output_path = _new_output_path()

    try:
        service = get_advanced_pdf_service()
        service.add_signature_field(
            pdf_path=input_path,
            output_path=output_path,
            page_number=request.page_number,
            x=request.x,
            y=request.y,
            width=request.width,
            height=request.height,
            field_name=request.field_name,
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="signature_field.pdf",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signature field failed: {str(e)}",
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
