"""Celery tasks for PDF processing."""
import logging
import os
from typing import List

from celery import Task
from PIL import Image
from pypdf import PdfReader, PdfWriter

from app.celery_worker import celery_app

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
    try:
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

    except Exception as exc:
        logger.error(f"PDF merge failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def split_pdf_task(self, file_path: str, page_ranges: List[tuple], output_dir: str) -> dict:
    """Split a PDF file into separate files by page range."""
    try:
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

    except Exception as exc:
        logger.error(f"PDF split failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def compress_pdf_task(self, file_path: str, output_path: str, quality: str = "medium") -> dict:
    """Compress a PDF file with pypdf content stream compression."""
    try:
        logger.info(f"Compressing PDF: {file_path} (quality: {quality})")

        reader = PdfReader(file_path)
        writer = PdfWriter()

        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        original_size = os.path.getsize(file_path)
        compressed_size = os.path.getsize(output_path)
        compression_ratio = (1 - compressed_size / original_size) * 100

        logger.info(
            f"Compressed: {original_size} -> {compressed_size} bytes "
            f"({compression_ratio:.1f}% reduction)"
        )

        return {
            "success": True,
            "output_path": output_path,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": round(compression_ratio, 2),
        }

    except Exception as exc:
        logger.error(f"PDF compression failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def rotate_pdf_task(self, file_path: str, output_path: str, rotation: int) -> dict:
    """Rotate every page in a PDF file."""
    try:
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

    except Exception as exc:
        logger.error(f"PDF rotation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def convert_images_to_pdf_task(self, image_paths: List[str], output_path: str) -> dict:
    """Convert image files into one PDF file."""
    try:
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

    except Exception as exc:
        logger.error(f"Image to PDF conversion failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=PDFTask, bind=True, max_retries=3)
def convert_pdf_to_images_task(self, file_path: str, output_dir: str, format: str = "png") -> dict:
    """Convert a PDF file into page images."""
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
        logger.error(f"PDF to image conversion failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
