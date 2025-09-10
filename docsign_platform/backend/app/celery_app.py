from celery import Celery
from app.core.config import settings

# Initialize the Celery app
# The first argument 'tasks' is the conventional name for the main module.
# The broker and backend URLs are pulled from our application settings.
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.finalize_document"] # Tell Celery where to find tasks
)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
)