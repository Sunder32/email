from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "email_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "reset-hourly-counters": {
            "task": "app.tasks.reset_counters.reset_hourly",
            "schedule": 3600.0,
        },
        "reset-daily-counters": {
            "task": "app.tasks.reset_counters.reset_daily",
            "schedule": 86400.0,
        },
    },
)

celery_app.conf.imports = [
    "app.tasks.send_campaign",
    "app.tasks.validate_contacts",
    "app.tasks.generate_variations",
    "app.tasks.reset_counters",
]
