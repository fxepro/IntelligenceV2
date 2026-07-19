"""Intelligence worker stub — summaries / entities / claims."""
from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope


@celery_app.task(name="tasks.intelligence.run_intelligence", bind=True, max_retries=2)
def run_intelligence(self, job_id: str):
    try:
        with session_scope() as session:
            mark_running(session, job_id)
            mark_completed(session, job_id, {"note": "intelligence stub"})
        return {"job_id": job_id, "ok": True}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        raise
