"""
File Processing Endpoints
文件处理相关的 API 端点
"""
import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse

from app.schemas.file import (
    FileUploadResponse,
    PDFMergeRequest,
    PDFSplitRequest,
    PDFCompressRequest,
    PDFRotateRequest,
    ImageToPDFRequest,
    PDFToImageRequest,
    OCRRequest,
    ProcessingJobResponse,
    ProcessingJobStatusResponse,
)
from app.services.file_service import file_processing_service
from app.core.rate_limiter import rate_limit_middleware
from app.api.v1.endpoints.auth import get_current_user_optional
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


async def apply_upload_rate_limit(request: Request):
    """上传端点的限流"""
    await rate_limit_middleware.apply_rate_limit(
        request=request,
        max_requests=10,  # 10 次上传
        window_seconds=60,  # 每分钟
        key_suffix="upload"
    )


async def apply_processing_rate_limit(request: Request):
    """处理端点的限流"""
    await rate_limit_middleware.apply_rate_limit(
        request=request,
        max_requests=20,  # 20 次处理
        window_seconds=60,  # 每分钟
        key_suffix="processing"
    )


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="要上传的文件"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_upload_rate_limit)
):
    """
    上传文件

    - **file**: 要上传的文件（PDF、图片等）
    - 支持的格式: PDF, JPEG, PNG, WEBP, GIF, TIFF, DOCX, XLSX
    - 文件大小限制:
        - Free: 20MB
        - Pro: 500MB
        - Enterprise: 2GB
    """
    # 确定用户等级（基于 role；admin 视为 enterprise 级配额）
    user_tier = "free"
    if current_user:
        role_value = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        user_tier = "enterprise" if role_value == "admin" else role_value

    try:
        result = await file_processing_service.upload_file(file, user_tier)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.post("/merge", response_model=ProcessingJobResponse)
async def merge_pdfs(
    request: Request,
    payload: PDFMergeRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    合并多个 PDF 文件

    - **file_ids**: 要合并的文件 ID 列表（至少 2 个）
    - **output_filename**: 输出文件名（可选）
    """
    try:
        result = await file_processing_service.merge_pdfs(
            file_ids=payload.file_ids,
            output_filename=payload.output_filename
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge PDFs"
        )


@router.post("/split", response_model=ProcessingJobResponse)
async def split_pdf(
    request: Request,
    payload: PDFSplitRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    拆分 PDF 文件

    - **file_id**: PDF 文件 ID
    - **page_ranges**: 页面范围列表，例如 [[1,3], [5,7]]
    """
    try:
        result = await file_processing_service.split_pdf(
            file_id=payload.file_id,
            page_ranges=payload.page_ranges
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Split failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to split PDF"
        )


@router.post("/compress", response_model=ProcessingJobResponse)
async def compress_pdf(
    request: Request,
    payload: PDFCompressRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    压缩 PDF 文件

    - **file_id**: PDF 文件 ID
    - **quality**: 压缩质量（low, medium, high）
    """
    try:
        result = await file_processing_service.compress_pdf(
            file_id=payload.file_id,
            quality=payload.quality.value
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compress failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compress PDF"
        )


@router.post("/rotate", response_model=ProcessingJobResponse)
async def rotate_pdf(
    request: Request,
    payload: PDFRotateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    旋转 PDF 页面

    - **file_id**: PDF 文件 ID
    - **rotation**: 旋转角度（90, 180, 270）
    - **pages**: 要旋转的页面（可选，默认所有页面）
    """
    try:
        result = await file_processing_service.rotate_pdf(
            file_id=payload.file_id,
            rotation=payload.rotation
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rotate failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate PDF"
        )


@router.post("/images-to-pdf", response_model=ProcessingJobResponse)
async def images_to_pdf(
    request: Request,
    payload: ImageToPDFRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    将图片转换为 PDF

    - **file_ids**: 图片文件 ID 列表
    - **output_filename**: 输出文件名（可选）
    """
    try:
        result = await file_processing_service.images_to_pdf(
            file_ids=payload.file_ids,
            output_filename=payload.output_filename
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Images to PDF failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert images to PDF"
        )


@router.post("/pdf-to-images", response_model=ProcessingJobResponse)
async def pdf_to_images(
    request: Request,
    payload: PDFToImageRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    将 PDF 转换为图片

    - **file_id**: PDF 文件 ID
    - **format**: 输出格式（png, jpeg）
    - **pages**: 要转换的页面（可选，默认所有页面）
    - **dpi**: 输出 DPI（72-600）
    """
    try:
        result = await file_processing_service.pdf_to_images(
            file_id=payload.file_id,
            format=payload.format.value
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to images failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert PDF to images"
        )


@router.post("/ocr", response_model=ProcessingJobResponse)
async def extract_text_ocr(
    request: Request,
    payload: OCRRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    OCR 文本提取

    - **file_id**: 文件 ID（PDF 或图片）
    - **language**: OCR 语言（eng, chi_sim, chi_tra 等）
    - **pages**: 要识别的页面（可选，默认所有页面）

    **注意**: OCR 功能为 Pro 和 Enterprise 用户专属
    """
    # 检查用户权限（免费用户不能使用 OCR）
    user_role = getattr(current_user, "role", None)
    role_value = user_role.value if hasattr(user_role, "value") else user_role
    if not current_user or role_value == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OCR feature is only available for Pro and Enterprise users"
        )

    try:
        result = await file_processing_service.extract_text_ocr(
            file_id=payload.file_id,
            language=payload.language
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text"
        )


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    下载已完成任务的处理结果

    - **job_id**: 任务 ID
    - 单文件结果直接下载；多文件结果打包为 zip；OCR 返回 .txt
    - 任务未完成返回 425，失败返回 422
    """
    download_path = file_processing_service.get_download_path(job_id)
    return FileResponse(
        path=str(download_path),
        filename=download_path.name,
        media_type="application/octet-stream"
    )


@router.get("/jobs/{job_id}", response_model=ProcessingJobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    查询处理任务状态

    - **job_id**: 任务 ID
    """
    status_data = file_processing_service.get_job_status(job_id)

    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )

    return status_data


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    取消处理任务

    - **job_id**: 任务 ID
    """
    # TODO: 实现任务取消逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Job cancellation not yet implemented"
    )


@router.post("/office-to-pdf", response_model=ProcessingJobResponse)
async def office_to_pdf(
    request: Request,
    file: UploadFile = File(..., description="Office文件（DOCX/XLSX/PPTX）"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_processing_rate_limit)
):
    """
    Office 文件转 PDF

    支持的格式：
    - Word: .docx, .doc
    - Excel: .xlsx, .xls
    - PowerPoint: .pptx, .ppt

    注意：需要系统安装 LibreOffice
    """
    try:
        # 验证文件类型
        allowed_extensions = ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        result = await file_processing_service.office_to_pdf(file)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Office to PDF conversion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert Office file: {str(e)}"
        )
