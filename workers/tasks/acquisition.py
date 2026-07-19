"""Acquisition worker stub — download / fetch raw artifacts."""
from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope


@celery_app.task(name="tasks.acquisition.run_acquire", bind=True, max_retries=3)
def run_acquire(self, job_id: str):
    try:
        with session_scope() as session:
            mark_running(session, job_id)
            mark_completed(session, job_id, {"note": "acquisition stub"})
        return {"job_id": job_id, "ok": True}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        raise self.retry(exc=exc, countdown=30)
