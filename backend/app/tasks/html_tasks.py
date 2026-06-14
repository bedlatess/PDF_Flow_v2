"""Celery tasks for HTML to PDF conversion."""

from __future__ import annotations

import logging
from typing import Callable

from celery import Task

from app.celery_worker import celery_app
from app.domains.files.html_to_pdf import render_html_to_pdf
from app.domains.jobs.service import job_lifecycle

logger = logging.getLogger(__name__)


class HTMLTask(Task):
    """Base HTML conversion task."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("HTML to PDF task %s failed: %s", task_id, exc)


@celery_app.task(base=HTMLTask, bind=True, max_retries=1)
def html_to_pdf_task(
    self,
    mode: str,
    source: str,
    output_path: str,
    page_size: str = "A4",
    orientation: str = "portrait",
    margin: str = "normal",
) -> dict:
    """Render URL or HTML source to a PDF file."""

    job_id = str(getattr(self.request, "id", "") or "")
    return _run_html_to_pdf_with_job_lifecycle(
        job_id=job_id,
        operation=lambda: render_html_to_pdf(
            mode=mode,
            source=source,
            output_path=output_path,
            page_size=page_size,
            orientation=orientation,
            margin=margin,
        ),
        retry=lambda exc: self.retry(exc=exc, countdown=30),
    )


def _run_html_to_pdf_with_job_lifecycle(
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
        logger.error("HTML to PDF conversion failed: %s", exc)
        if job_id:
            job_lifecycle.mark_failed(job_id, error_message=str(exc))
        if retry is not None:
            raise retry(exc)
        raise
