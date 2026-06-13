"""Celery worker configuration for PDF-Flow background jobs."""
from celery import Celery
from kombu import Queue

from app.core.config import settings

celery_app = Celery(
    "pdf_flow_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.pdf_tasks",
        "app.tasks.ocr_tasks",
        "app.tasks.office_tasks",
        "app.tasks.email_tasks",
    ],
)

celery_app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="pdf_processing",
    task_queues=(
        Queue("pdf_processing"),
        Queue("ocr_processing"),
        Queue("office_processing"),
        Queue("email"),
    ),
    task_routes={
        "app.tasks.pdf_tasks.*": {"queue": "pdf_processing"},
        "app.tasks.ocr_tasks.*": {"queue": "ocr_processing"},
        "app.tasks.office_tasks.*": {"queue": "office_processing"},
        "app.tasks.email_tasks.*": {"queue": "email"},
    },
    task_default_priority=5,
    task_annotations={
        "app.tasks.pdf_tasks.compress_pdf": {"rate_limit": "10/m"},
        "app.tasks.ocr_tasks.extract_text": {"rate_limit": "5/m"},
        "app.tasks.email_tasks.send_churn_prevention_emails": {"rate_limit": "1/h"},
    },
    beat_schedule={
        "send-churn-prevention-emails": {
            "task": "send_churn_prevention_emails",
            "schedule": 86400.0,
        },
    },
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

if __name__ == "__main__":
    celery_app.start()
