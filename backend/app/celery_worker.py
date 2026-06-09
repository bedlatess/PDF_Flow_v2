"""
Celery Worker Configuration
异步任务处理器，用于处理耗时的 PDF 操作
"""
from celery import Celery
from kombu import Queue
from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "pdf_flow_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.pdf_tasks",
        "app.tasks.ocr_tasks",
        "app.tasks.office_tasks",
        "app.tasks.email_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任务结果过期时间（秒）
    result_expires=3600,

    # 任务序列化格式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区设置
    timezone="UTC",
    enable_utc=True,

    # 显式声明 worker 需要消费的队列，避免任务被路由到自定义队列后无人消费
    task_default_queue="pdf_processing",
    task_queues=(
        Queue("pdf_processing"),
        Queue("ocr_processing"),
        Queue("office_processing"),
        Queue("email"),
    ),

    # 任务路由
    task_routes={
        "app.tasks.pdf_tasks.*": {"queue": "pdf_processing"},
        "app.tasks.ocr_tasks.*": {"queue": "ocr_processing"},
        "app.tasks.office_tasks.*": {"queue": "office_processing"},
        "app.tasks.email_tasks.*": {"queue": "email"},
    },

    # 任务优先级
    task_default_priority=5,

    # 限流配置
    task_annotations={
        "app.tasks.pdf_tasks.compress_pdf": {"rate_limit": "10/m"},
        "app.tasks.ocr_tasks.extract_text": {"rate_limit": "5/m"},
        "app.tasks.email_tasks.send_churn_prevention_emails": {"rate_limit": "1/h"},
    },

    # 定时任务 (Celery Beat)
    beat_schedule={
        "send-churn-prevention-emails": {
            "task": "send_churn_prevention_emails",
            "schedule": 86400.0,  # 每24小时运行一次
        },
        "send-subscription-expiry-reminders": {
            "task": "send_subscription_expiry_reminders",
            "schedule": 43200.0,  # 每12小时运行一次
        },
    },

    # Worker 配置
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # 任务重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# 任务自动发现
celery_app.autodiscover_tasks(["app.tasks"])

if __name__ == "__main__":
    celery_app.start()
