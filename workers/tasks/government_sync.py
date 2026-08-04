"""Government domain Celery tasks (GOV-0001 SAM opportunities)."""
from __future__ import annotations

from uuid import UUID

from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope


@celery_app.task(name="tasks.government_sync.run_sam_opportunities", bind=True, max_retries=1)
def run_sam_opportunities(self, job_id: str):
    try:
        with session_scope() as session:
            job = mark_running(session, job_id)
            payload = job.payload or {}
            source_id = payload.get("source_id") or job.source_id
            if not source_id:
                raise ValueError("sam opportunities sync requires source_id")

            from app.services.sam_gov_sync import sync_opportunities

            result = sync_opportunities(
                session,
                source_id=UUID(str(source_id)),
                posted_from=payload.get("posted_from"),
                posted_to=payload.get("posted_to"),
                limit=int(payload.get("limit") or 100),
                max_pages=int(payload.get("max_pages") or 1),
            )
            mark_completed(session, job_id, result)
        return {"job_id": job_id, **result}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        return {"job_id": job_id, "ok": False, "error": str(exc)}
