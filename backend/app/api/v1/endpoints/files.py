"""File processing API route wrappers."""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.core.rate_limiter import rate_limit_middleware
from app.domains.jobs.repository import ProcessingJobRepository
from app.domains.jobs.service import JobService
from app.domains.files.service import (
    require_file_feature,
    require_job_status,
    run_file_operation,
    sync_cancelled_processing_job,
    user_upload_tier,
    validate_office_upload,
)
from app.domains.usage_limits import ToolUsageContext, enforce_tool_limits_for_flag, record_tool_usage
from app.models.user import User
from app.schemas.file import (
    FileUploadResponse,
    HTMLToPDFRequest,
    ImageToPDFRequest,
    OCRRequest,
    PDFCompressRequest,
    PDFMergeRequest,
    PDFRotateRequest,
    PDFSplitRequest,
    PDFToImageRequest,
    PDFToExcelRequest,
    PDFToWordRequest,
    ProcessingJobHistoryItem,
    ProcessingJobHistoryListResponse,
    ProcessingJobResponse,
    ProcessingJobStatusResponse,
)
from app.services.file_service import file_processing_service

router = APIRouter(prefix="/files", tags=["files"])


def _file_metadata_for_limits(file_id: str) -> dict:
    return file_processing_service._get_file_metadata(file_id)


def _metadata_sizes(items: list[dict]) -> list[int]:
    return [int(item.get("size") or 0) for item in items]


def _record_usage_callback(
    *,
    db: Session,
    context: ToolUsageContext,
    request: Request,
    file_size: int,
    file_count: int,
):
    return lambda result: record_tool_usage(
        db,
        context=context,
        job_id=result.get("job_id"),
        file_size=file_size,
        file_count=file_count,
        request=request,
    )


def _enforce_limits(
    db: Session,
    *,
    feature_key: str,
    current_user: User | None,
    request: Request,
    file_sizes: list[int] | None = None,
    batch_count: int = 1,
) -> ToolUsageContext:
    flag = require_file_feature(db, feature_key, current_user)
    return enforce_tool_limits_for_flag(
        db,
        feature_key=feature_key,
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=file_sizes,
        batch_count=batch_count,
    )


def _enforce_limits_for_flag(
    db: Session,
    *,
    feature_key: str,
    flag,
    current_user: User | None,
    request: Request,
    file_sizes: list[int] | None = None,
    batch_count: int = 1,
) -> ToolUsageContext:
    return enforce_tool_limits_for_flag(
        db,
        feature_key=feature_key,
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=file_sizes,
        batch_count=batch_count,
    )


async def apply_upload_rate_limit(request: Request):
    """Rate limit upload endpoints."""
    await rate_limit_middleware.apply_rate_limit(
        request=request,
        max_requests=10,
        window_seconds=60,
        key_suffix="upload",
    )


async def apply_processing_rate_limit(request: Request):
    """Rate limit processing endpoints."""
    await rate_limit_middleware.apply_rate_limit(
        request=request,
        max_requests=20,
        window_seconds=60,
        key_suffix="processing",
    )


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    _rate_limit: None = Depends(apply_upload_rate_limit),
):
    return await run_file_operation(
        lambda: file_processing_service.upload_file(file, user_upload_tier(current_user)),
        error_detail="Failed to upload file",
        log_message="Upload failed",
    )


@router.post("/merge", response_model=ProcessingJobResponse)
async def merge_pdfs(
    request: Request,
    payload: PDFMergeRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "merge_pdf", current_user)
    metadata = [_file_metadata_for_limits(file_id) for file_id in payload.file_ids]
    sizes = _metadata_sizes(metadata)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="merge_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=sizes,
        batch_count=len(metadata),
    )
    return await run_file_operation(
        lambda: file_processing_service.merge_pdfs(
            file_ids=payload.file_ids,
            output_filename=payload.output_filename,
            db=db,
        ),
        error_detail="Failed to merge PDFs",
        log_message="Merge failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=sum(sizes),
            file_count=len(metadata),
        ),
    )


@router.post("/split", response_model=ProcessingJobResponse)
async def split_pdf(
    request: Request,
    payload: PDFSplitRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "split_pdf", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="split_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.split_pdf(
            file_id=payload.file_id,
            page_ranges=payload.page_ranges,
            db=db,
        ),
        error_detail="Failed to split PDF",
        log_message="Split failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )


@router.post("/compress", response_model=ProcessingJobResponse)
async def compress_pdf(
    request: Request,
    payload: PDFCompressRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "compress_pdf", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="compress_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.compress_pdf(
            file_id=payload.file_id,
            quality=payload.quality.value,
            db=db,
        ),
        error_detail="Failed to compress PDF",
        log_message="Compress failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )


@router.post("/rotate", response_model=ProcessingJobResponse)
async def rotate_pdf(
    request: Request,
    payload: PDFRotateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "rotate_pdf", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="rotate_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.rotate_pdf(
            file_id=payload.file_id,
            rotation=payload.rotation,
            db=db,
        ),
        error_detail="Failed to rotate PDF",
        log_message="Rotate failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )


@router.post("/images-to-pdf", response_model=ProcessingJobResponse)
async def images_to_pdf(
    request: Request,
    payload: ImageToPDFRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "image_to_pdf", current_user)
    metadata = [_file_metadata_for_limits(file_id) for file_id in payload.file_ids]
    sizes = _metadata_sizes(metadata)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="image_to_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=sizes,
        batch_count=len(metadata),
    )
    return await run_file_operation(
        lambda: file_processing_service.images_to_pdf(
            file_ids=payload.file_ids,
            output_filename=payload.output_filename,
            db=db,
        ),
        error_detail="Failed to convert images to PDF",
        log_message="Images to PDF failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=sum(sizes),
            file_count=len(metadata),
        ),
    )


@router.post("/pdf-to-images", response_model=ProcessingJobResponse)
async def pdf_to_images(
    request: Request,
    payload: PDFToImageRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "pdf_to_image", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="pdf_to_image",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.pdf_to_images(
            file_id=payload.file_id,
            format=payload.format.value,
            db=db,
        ),
        error_detail="Failed to convert PDF to images",
        log_message="PDF to images failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )


@router.post("/ocr", response_model=ProcessingJobResponse)
async def extract_text_ocr(
    request: Request,
    payload: OCRRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "ocr_pdf", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="ocr_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.extract_text_ocr(
            file_id=payload.file_id,
            language=payload.language,
            db=db,
        ),
        error_detail="Failed to extract text",
        log_message="OCR failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    download_path = file_processing_service.get_download_path(job_id)
    return FileResponse(
        path=str(download_path),
        filename=download_path.name,
        media_type="application/octet-stream",
    )


@router.get("/history", response_model=ProcessingJobHistoryListResponse)
async def list_job_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    job_type: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = JobService(ProcessingJobRepository(db))
    items, total = service.user_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        status_filter=status_filter,
        job_type=job_type,
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/history/{job_id}", response_model=ProcessingJobHistoryItem)
async def get_job_history_detail(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = JobService(ProcessingJobRepository(db))
    item = service.user_history_detail(job_id=job_id, user_id=current_user.id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    return item


@router.get("/history/{job_id}/download")
async def download_history_result(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = JobService(ProcessingJobRepository(db))
    item = service.user_history_detail(job_id=job_id, user_id=current_user.id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    if not item["download_available"]:
        is_expired = item["download_state"] == "expired"
        raise HTTPException(
            status_code=status.HTTP_410_GONE if is_expired else status.HTTP_409_CONFLICT,
            detail="Result file has expired" if is_expired else "Job result is not available for download",
        )

    download_path = file_processing_service.get_download_path(job_id)
    return FileResponse(
        path=str(download_path),
        filename=download_path.name,
        media_type="application/octet-stream",
    )


@router.get("/jobs/{job_id}", response_model=ProcessingJobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    return require_job_status(job_id, file_processing_service.get_job_status(job_id))


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    file_processing_service.cancel_job(job_id)
    sync_cancelled_processing_job(db, job_id)


@router.post("/office-to-pdf", response_model=ProcessingJobResponse)
async def office_to_pdf(
    request: Request,
    file: UploadFile = File(..., description="Office file"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "office_to_pdf", current_user)
    validate_office_upload(file)
    file_size = int(getattr(file, "size", None) or 0)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="office_to_pdf",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[file_size] if file_size else [],
    )
    return await run_file_operation(
        lambda: file_processing_service.office_to_pdf(file, db=db),
        error_detail="Failed to convert Office file",
        log_message="Office to PDF conversion failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=file_size,
            file_count=1,
        ),
    )


@router.post("/html-to-pdf", response_model=ProcessingJobResponse)
async def html_to_pdf(
    request: Request,
    payload: HTMLToPDFRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    source = payload.url if payload.mode == "url" else payload.html
    source_size = len((source or "").encode("utf-8"))
    usage_context = _enforce_limits(
        db,
        feature_key="html_to_pdf",
        current_user=current_user,
        request=request,
        file_sizes=[source_size],
    )
    return await run_file_operation(
        lambda: file_processing_service.html_to_pdf(
            mode=payload.mode,
            source=source or "",
            page_size=payload.page_size,
            orientation=payload.orientation,
            margin=payload.margin,
            user_id=current_user.id,
            db=db,
        ),
        error_detail="Failed to queue HTML to PDF conversion",
        log_message="HTML to PDF queue failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=source_size,
            file_count=1,
        ),
    )


@router.post("/pdf-to-word", response_model=ProcessingJobResponse)
async def pdf_to_word(
    request: Request,
    payload: PDFToWordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "pdf_to_word", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="pdf_to_word",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.pdf_to_word(
            file_id=payload.file_id,
            user_id=current_user.id,
            db=db,
        ),
        error_detail="Failed to queue PDF to Word conversion",
        log_message="PDF to Word queue failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )


@router.post("/pdf-to-excel", response_model=ProcessingJobResponse)
async def pdf_to_excel(
    request: Request,
    payload: PDFToExcelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    flag = require_file_feature(db, "pdf_to_excel", current_user)
    metadata = _file_metadata_for_limits(payload.file_id)
    usage_context = _enforce_limits_for_flag(
        db,
        feature_key="pdf_to_excel",
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=[int(metadata.get("size") or 0)],
    )
    return await run_file_operation(
        lambda: file_processing_service.pdf_to_excel(
            file_id=payload.file_id,
            user_id=current_user.id,
            db=db,
        ),
        error_detail="Failed to queue PDF to Excel conversion",
        log_message="PDF to Excel queue failed",
        on_success=_record_usage_callback(
            db=db,
            context=usage_context,
            request=request,
            file_size=int(metadata.get("size") or 0),
            file_count=1,
        ),
    )
