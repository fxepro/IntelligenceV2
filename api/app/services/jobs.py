"""Job enqueue helpers — control plane never runs long work itself."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus, JobType


def _send_task(name: str, args: list[Any], queue: str) -> str:
    """Publish to Redis with hard socket timeouts so the API cannot hang."""
    from celery import Celery
    from app.config import get_settings

    settings = get_settings()
    app = Celery("intelligence_v2", broker=settings.celery_broker_url)
    app.conf.update(
        broker_connection_timeout=2,
        broker_connection_retry=False,
        broker_connection_retry_on_startup=False,
        broker_transport_options={
            "socket_timeout": 2,
            "socket_connect_timeout": 2,
            "retry_on_timeout": False,
        },
    )
    result = app.send_task(name, args=args, queue=queue)
    return result.id


QUEUE_BY_TYPE = {
    JobType.discover: ("tasks.discovery.run_discover", "discovery"),
    JobType.acquire: ("tasks.acquisition.run_acquire", "acquisition"),
    JobType.transcribe: ("tasks.transcription.run_transcribe", "transcription"),
    JobType.intelligence: ("tasks.intelligence.run_intelligence", "intelligence"),
    JobType.research: ("tasks.discovery.run_research", "discovery"),
}


async def enqueue_job(
    db: AsyncSession,
    *,
    job_type: JobType,
    domain: str = "media",
    source_id: uuid.UUID | None = None,
    record_id: uuid.UUID | None = None,
    payload: dict | None = None,
) -> Job:
    job = Job(
        job_type=job_type,
        status=JobStatus.queued,
        domain=domain,
        source_id=source_id,
        record_id=record_id,
        payload=payload or {},
        progress=0.0,
    )
    db.add(job)
    await db.flush()
    # Persist before broker publish so a Redis hang cannot roll the job back.
    await db.commit()
    await db.refresh(job)

    task_name, queue = QUEUE_BY_TYPE[job_type]
    try:
        task_id = await asyncio.wait_for(
            asyncio.to_thread(_send_task, task_name, [str(job.id)], queue),
            timeout=5,
        )
    except Exception as exc:
        job.status = JobStatus.failed
        job.error_message = f"Broker enqueue failed: {type(exc).__name__}: {exc}"[:2000]
        await db.commit()
        await db.refresh(job)
        raise RuntimeError(job.error_message) from exc

    job.celery_task_id = task_id
    await db.commit()
    await db.refresh(job)
    return job
