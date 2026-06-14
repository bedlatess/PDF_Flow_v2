"""
Celery Tasks Package
"""
from app.tasks.pdf_tasks import (
    merge_pdfs_task,
    split_pdf_task,
    compress_pdf_task,
    rotate_pdf_task,
    convert_images_to_pdf_task,
    convert_pdf_to_images_task,
)
from app.tasks.ocr_tasks import extract_text_task
from app.tasks.html_tasks import html_to_pdf_task

__all__ = [
    "merge_pdfs_task",
    "split_pdf_task",
    "compress_pdf_task",
    "rotate_pdf_task",
    "convert_images_to_pdf_task",
    "convert_pdf_to_images_task",
    "extract_text_task",
    "html_to_pdf_task",
]
