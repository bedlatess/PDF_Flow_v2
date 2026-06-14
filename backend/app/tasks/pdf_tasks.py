"""Celery tasks for PDF processing."""
import logging
import os
from typing import Callable, List, Mapping

from celery import Task
from PIL import Image
from pypdf import PdfReader, PdfWriter

from app.celery_worker import celery_app
from app.domains.jobs.service import job_lifecycle

logger = logging.getLogger(__name__)


class PDFTask(Task):
    """Base task with shared failure cleanup behavior."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Clean temporary files after task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        self._cleanup_temp_files(kwargs.get("temp_files", []))

    def _cleanup_temp_files(self, file_paths: List[str]):
        """Remove temporary files created during a task."""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def merge_pdfs_task(self, file_paths: List[str], output_path: str) -> dict:
    """Merge multiple PDF files into one output file."""
    job_id = _current_job_id(self)
    return _run_pdf_task_with_job_lifecycle(
        job_id=job_id,
        operation_label="PDF merge",
        operation=lambda: _merge_pdfs(file_paths, output_path),
        retry=lambda exc: self.retry(exc=exc, countdown=60),
    )


def _merge_pdfs(file_paths: List[str], output_path: str) -> dict:
    logger.info(f"Merging {len(file_paths)} PDFs")

    writer = PdfWriter()
    total_pages = 0

    for file_path in file_paths:
        reader = PdfReader(file_path)
        for page in reader.pages:
            writer.add_page(page)
            total_pages += 1

    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    logger.info(f"Merged PDF created: {output_path} ({total_pages} pages)")

    return {
        "success": True,
        "output_path": output_path,
        "page_count": total_pages,
        "file_size": os.path.getsize(output_path),
    }


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def split_pdf_task(self, file_path: str, page_ranges: List[tuple], output_dir: str) -> dict:
    """Split a PDF file into separate files by page range."""
    job_id = _current_job_id(self)
    return _run_pdf_task_with_job_lifecycle(
        job_id=job_id,
        operation_label="PDF split",
        operation=lambda: _split_pdf(file_path, page_ranges, output_dir),
        retry=lambda exc: self.retry(exc=exc, countdown=60),
    )


def _split_pdf(file_path: str, page_ranges: List[tuple], output_dir: str) -> dict:
    logger.info(f"Splitting PDF: {file_path}")

    reader = PdfReader(file_path)
    output_files = []

    for idx, (start, end) in enumerate(page_ranges):
        writer = PdfWriter()

        for page_num in range(start - 1, end):
            if page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

        output_path = os.path.join(output_dir, f"split_{idx + 1}.pdf")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        output_files.append(output_path)

    logger.info(f"PDF split into {len(output_files)} files")

    return {
        "success": True,
        "output_files": output_files,
        "count": len(output_files),
    }


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def compress_pdf_task(self, file_path: str, output_path: str, quality: str = "medium") -> dict:
    """Compress a PDF file with pypdf content stream compression."""
    job_id = _current_job_id(self)
    return _run_compress_pdf_with_job_lifecycle(
        job_id=job_id,
        file_path=file_path,
        output_path=output_path,
        quality=quality,
        retry=lambda exc: self.retry(exc=exc, countdown=60),
    )


def _run_compress_pdf_with_job_lifecycle(
    *,
    job_id: str,
    file_path: str,
    output_path: str,
    quality: str = "medium",
    retry=None,
) -> dict:
    return _run_pdf_task_with_job_lifecycle(
        job_id=job_id,
        operation_label="PDF compression",
        operation=lambda: _compress_pdf(file_path, output_path, quality),
        retry=retry,
    )


def _compress_pdf(file_path: str, output_path: str, quality: str = "medium") -> dict:
    logger.info(f"Compressing PDF: {file_path} (quality: {quality})")

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    for page in writer.pages:
        page.compress_content_streams()

    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(output_path)
    compression_ratio = (1 - compressed_size / original_size) * 100

    logger.info(
        f"Compressed: {original_size} -> {compressed_size} bytes "
        f"({compression_ratio:.1f}% reduction)"
    )

    result = {
        "success": True,
        "output_path": output_path,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": round(compression_ratio, 2),
    }

    return result


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def rotate_pdf_task(self, file_path: str, output_path: str, rotation: int) -> dict:
    """Rotate every page in a PDF file."""
    job_id = _current_job_id(self)
    return _run_pdf_task_with_job_lifecycle(
        job_id=job_id,
        operation_label="PDF rotation",
        operation=lambda: _rotate_pdf(file_path, output_path, rotation),
        retry=lambda exc: self.retry(exc=exc, countdown=60),
    )


def _rotate_pdf(file_path: str, output_path: str, rotation: int) -> dict:
    logger.info(f"Rotating PDF: {file_path} by {rotation} degrees")

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(rotation)
        writer.add_page(page)

    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    logger.info(f"Rotated PDF saved: {output_path}")

    return {
        "success": True,
        "output_path": output_path,
        "rotation": rotation,
        "page_count": len(reader.pages),
    }


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def convert_images_to_pdf_task(self, image_paths: List[str], output_path: str) -> dict:
    """Convert image files into one PDF file."""
    job_id = _current_job_id(self)
    return _run_pdf_task_with_job_lifecycle(
        job_id=job_id,
        operation_label="Image to PDF conversion",
        operation=lambda: _convert_images_to_pdf(image_paths, output_path),
        retry=lambda exc: self.retry(exc=exc, countdown=60),
    )


def _convert_images_to_pdf(image_paths: List[str], output_path: str) -> dict:
    logger.info(f"Converting {len(image_paths)} images to PDF")

    images = []
    for img_path in image_paths:
        img = Image.open(img_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        images.append(img)

    if images:
        images[0].save(output_path, save_all=True, append_images=images[1:])

    logger.info(f"PDF created from images: {output_path}")

    return {
        "success": True,
        "output_path": output_path,
        "page_count": len(images),
        "file_size": os.path.getsize(output_path),
    }


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def convert_pdf_to_images_task(self, file_path: str, output_dir: str, format: str = "png") -> dict:
    """Convert a PDF file into page images."""
    job_id = _current_job_id(self)
    return _run_pdf_task_with_job_lifecycle(
        job_id=job_id,
        operation_label="PDF to image conversion",
        operation=lambda: _convert_pdf_to_images(file_path, output_dir, format),
        retry=lambda exc: self.retry(exc=exc, countdown=60),
    )


def _convert_pdf_to_images(file_path: str, output_dir: str, format: str = "png") -> dict:
    try:
        from pdf2image import convert_from_path

        logger.info(f"Converting PDF to {format.upper()} images: {file_path}")

        images = convert_from_path(file_path, dpi=300)
        output_files = []

        for idx, image in enumerate(images):
            output_path = os.path.join(output_dir, f"page_{idx + 1}.{format}")
            image.save(output_path, format.upper())
            output_files.append(output_path)

        logger.info(f"PDF converted to {len(output_files)} {format.upper()} images")

        return {
            "success": True,
            "output_files": output_files,
            "count": len(output_files),
            "format": format,
        }

    except Exception as exc:
        logger.error(f"PDF to image conversion failed before lifecycle retry: {exc}")
        raise


def _current_job_id(task: Task) -> str:
    return str(getattr(task.request, "id", "") or "")


def _run_pdf_task_with_job_lifecycle(
    *,
    job_id: str,
    operation_label: str,
    operation: Callable[[], dict],
    retry=None,
) -> dict:
    if job_id:
        job_lifecycle.mark_processing(job_id, progress=0)

    try:
        result = operation()
        if job_id:
            job_lifecycle.mark_completed(
                job_id,
                result_data=result,
                output_file_url=_result_output_url(result),
            )
        return result
    except Exception as exc:
        logger.error("%s failed: %s", operation_label, exc)
        if job_id:
            job_lifecycle.mark_failed(job_id, error_message=str(exc))
        if retry is not None:
            raise retry(exc)
        raise


def _result_output_url(result: Mapping[str, object]) -> str | None:
    output_path = result.get("output_path")
    if output_path:
        return str(output_path)
    output_files = result.get("output_files")
    if isinstance(output_files, list) and output_files:
        return str(output_files[0])
    return None
