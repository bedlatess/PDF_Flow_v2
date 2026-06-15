"""Celery tasks for PDF to Excel conversion."""

from __future__ import annotations

import logging
from typing import Callable

from celery import Task

from app.celery_worker import celery_app
from app.domains.files.pdf_to_excel import PDFToExcelError, convert_text_pdf_to_xlsx, user_facing_pdf_to_excel_error
from app.domains.jobs.service import job_lifecycle

logger = logging.getLogger(__name__)


class ExcelTask(Task):
    """Base task for Excel conversion."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("PDF to Excel task %s failed: %s", task_id, user_facing_pdf_to_excel_error(exc))


@celery_app.task(base=ExcelTask, bind=True, max_retries=1)
def pdf_to_excel_task(self, file_path: str, output_path: str) -> dict:
    """Convert a text-based PDF into a simple XLSX workbook."""

    job_id = str(getattr(self.request, "id", "") or "")
    return _run_pdf_to_excel_with_job_lifecycle(
        job_id=job_id,
        operation=lambda: convert_text_pdf_to_xlsx(
            input_path=file_path,
            output_path=output_path,
        ),
        retry=lambda exc: self.retry(exc=exc, countdown=30),
    )


def _run_pdf_to_excel_with_job_lifecycle(
    *,
    job_id: str,
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
                output_file_url=result.get("output_path"),
            )
        return result
    except Exception as exc:
        error_message = user_facing_pdf_to_excel_error(exc)
        logger.error("PDF to Excel conversion failed: %s", error_message)
        if job_id:
            job_lifecycle.mark_failed(job_id, error_message=error_message)
        if retry is not None and not isinstance(exc, PDFToExcelError):
            raise retry(exc)
        raise
