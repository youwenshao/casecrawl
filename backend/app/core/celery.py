"""
Celery configuration for async task processing.
"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "casecrawl",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.services.tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Hong_Kong",
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing without worker
    task_store_eager_result=False,
    task_ignore_result=False,
    task_track_started=True,
    
    # Rate limiting
    task_default_rate_limit="4/m",  # 4 tasks per minute default
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Don't prefetch tasks (sequential processing)
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    
    # Redis settings
    redis_socket_keepalive=True,
    redis_retry_on_timeout=True,
)

# Queue definitions
celery_app.conf.task_routes = {
    "app.services.tasks.*": {"queue": "default"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-files": {
        "task": "app.services.tasks.cleanup_old_files",
        "schedule": 86400.0,  # Daily
    },
    "cleanup-expired-sessions": {
        "task": "app.services.tasks.cleanup_expired_sessions",
        "schedule": 3600.0,  # Hourly
    },
}
