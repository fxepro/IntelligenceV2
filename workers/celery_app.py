import os
from pathlib import Path

from celery import Celery

# Prefer project-local Playwright browsers (Facebook discover) over sandbox/temp caches.
_browsers = Path(__file__).resolve().parents[1] / "infra" / "playwright-browsers"
if _browsers.is_dir() and not os.getenv("PLAYWRIGHT_BROWSERS_PATH"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_browsers)

broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery("intelligence_v2", broker=broker, backend=backend)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    beat_schedule={
        "scan-autorun-sources-every-minute": {
            "task": "tasks.discovery.run_autorun_scan",
            "schedule": 60.0,
            "options": {"queue": "discovery", "expires": 55},
        },
        "drain-auto-transcribe-every-minute": {
            "task": "tasks.transcription.drain_auto_transcribe",
            "schedule": 60.0,
            "options": {"queue": "transcription", "expires": 55},
        },
    },
    task_routes={
        "tasks.discovery.*": {"queue": "discovery"},
        "tasks.acquisition.*": {"queue": "acquisition"},
        "tasks.transcription.*": {"queue": "transcription"},
        "tasks.intelligence.*": {"queue": "intelligence"},
    },
    imports=(
        "tasks.discovery",
        "tasks.acquisition",
        "tasks.transcription",
        "tasks.intelligence",
    ),
)
