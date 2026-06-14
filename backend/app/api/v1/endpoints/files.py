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
from app.models.user import User
from app.schemas.file import (
    FileUploadResponse,
    ImageToPDFRequest,
    OCRRequest,
    PDFCompressRequest,
    PDFMergeRequest,
    PDFRotateRequest,
    PDFSplitRequest,
    PDFToImageRequest,
    ProcessingJobHistoryItem,
    ProcessingJobHistoryListResponse,
    ProcessingJobResponse,
    ProcessingJobStatusResponse,
)
from app.services.file_service import file_processing_service

router = APIRouter(prefix="/files", tags=["files"])


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
    require_file_feature(db, "merge_pdf", current_user)
    return await run_file_operation(
        lambda: file_processing_service.merge_pdfs(
            file_ids=payload.file_ids,
            output_filename=payload.output_filename,
            db=db,
        ),
        error_detail="Failed to merge PDFs",
        log_message="Merge failed",
    )


@router.post("/split", response_model=ProcessingJobResponse)
async def split_pdf(
    request: Request,
    payload: PDFSplitRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    require_file_feature(db, "split_pdf", current_user)
    return await run_file_operation(
        lambda: file_processing_service.split_pdf(
            file_id=payload.file_id,
            page_ranges=payload.page_ranges,
            db=db,
        ),
        error_detail="Failed to split PDF",
        log_message="Split failed",
    )


@router.post("/compress", response_model=ProcessingJobResponse)
async def compress_pdf(
    request: Request,
    payload: PDFCompressRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    require_file_feature(db, "compress_pdf", current_user)
    return await run_file_operation(
        lambda: file_processing_service.compress_pdf(
            file_id=payload.file_id,
            quality=payload.quality.value,
            db=db,
        ),
        error_detail="Failed to compress PDF",
        log_message="Compress failed",
    )


@router.post("/rotate", response_model=ProcessingJobResponse)
async def rotate_pdf(
    request: Request,
    payload: PDFRotateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    require_file_feature(db, "rotate_pdf", current_user)
    return await run_file_operation(
        lambda: file_processing_service.rotate_pdf(
            file_id=payload.file_id,
            rotation=payload.rotation,
            db=db,
        ),
        error_detail="Failed to rotate PDF",
        log_message="Rotate failed",
    )


@router.post("/images-to-pdf", response_model=ProcessingJobResponse)
async def images_to_pdf(
    request: Request,
    payload: ImageToPDFRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    require_file_feature(db, "image_to_pdf", current_user)
    return await run_file_operation(
        lambda: file_processing_service.images_to_pdf(
            file_ids=payload.file_ids,
            output_filename=payload.output_filename,
            db=db,
        ),
        error_detail="Failed to convert images to PDF",
        log_message="Images to PDF failed",
    )


@router.post("/pdf-to-images", response_model=ProcessingJobResponse)
async def pdf_to_images(
    request: Request,
    payload: PDFToImageRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    require_file_feature(db, "pdf_to_image", current_user)
    return await run_file_operation(
        lambda: file_processing_service.pdf_to_images(
            file_id=payload.file_id,
            format=payload.format.value,
            db=db,
        ),
        error_detail="Failed to convert PDF to images",
        log_message="PDF to images failed",
    )


@router.post("/ocr", response_model=ProcessingJobResponse)
async def extract_text_ocr(
    request: Request,
    payload: OCRRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(apply_processing_rate_limit),
):
    require_file_feature(db, "ocr_pdf", current_user)
    return await run_file_operation(
        lambda: file_processing_service.extract_text_ocr(
            file_id=payload.file_id,
            language=payload.language,
            db=db,
        ),
        error_detail="Failed to extract text",
        log_message="OCR failed",
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
    require_file_feature(db, "office_to_pdf", current_user)
    validate_office_upload(file)
    return await run_file_operation(
        lambda: file_processing_service.office_to_pdf(file, db=db),
        error_detail="Failed to convert Office file",
        log_message="Office to PDF conversion failed",
    )
