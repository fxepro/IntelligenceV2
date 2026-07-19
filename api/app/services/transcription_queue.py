"""Sync helpers to enqueue transcription jobs from Celery workers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus, JobType
from app.models.record import Record
from app.services.transcription_config import get_transcription_settings_sync


def _tx_status(record: Record) -> str:
    return (record.fields or {}).get("transcription_status") or "pending"


def _pipeline_transcription_count(session: Session) -> int:
    """Queued + running transcription jobs (global pipeline depth)."""
    return (
        session.query(Job.id)
        .filter(
            Job.job_type == JobType.transcribe,
            Job.status.in_([JobStatus.queued, JobStatus.running]),
        )
        .count()
    )


def enqueue_transcription_sync(session: Session, record: Record) -> Job | None:
    """Create a transcribe job for one record if none is already active."""
    existing = session.scalar(
        select(Job).where(
            Job.record_id == record.id,
            Job.job_type == JobType.transcribe,
            Job.status.in_([JobStatus.queued, JobStatus.running]),
        )
    )
    if existing:
        return existing

    fields = dict(record.fields or {})
    fields["transcription_status"] = "queued"
    record.fields = fields

    job = Job(
        job_type=JobType.transcribe,
        status=JobStatus.queued,
        domain=record.domain,
        source_id=record.source_id,
        record_id=record.id,
        payload={"dedup_key": record.dedup_key},
        progress=0.0,
    )
    session.add(job)
    session.flush()
    session.commit()

    try:
        from celery_app import celery_app

        task = celery_app.send_task(
            "tasks.transcription.run_transcribe",
            args=[str(job.id)],
            queue="transcription",
        )
        job.celery_task_id = task.id
        session.commit()
    except Exception as exc:
        job.status = JobStatus.failed
        job.error_message = f"Broker enqueue failed: {type(exc).__name__}: {exc}"[:2000]
        fields = dict(record.fields or {})
        fields["transcription_status"] = "failed"
        record.fields = fields
        session.commit()
        return None

    return job


def enqueue_pending_for_source_sync(
    session: Session,
    source_id: uuid.UUID,
    *,
    respect_caps: bool = True,
    retry_failed: bool = False,
    max_to_queue: int | None = None,
) -> dict:
    """
    Queue pending transcriptions for a source.

    When respect_caps=True (auto-transcribe):
    - keep global pipeline (queued + running) at or below Settings batch_size
    - top up remaining slots this pass
    """
    config = get_transcription_settings_sync(session)
    limit: int | None = None
    if respect_caps:
        batch = int(config["batch_size"])
        in_flight = _pipeline_transcription_count(session)
        slots = max(0, batch - in_flight)
        if max_to_queue is not None:
            slots = min(slots, max_to_queue)
        if slots <= 0:
            return {
                "queued": 0,
                "skipped_capacity": True,
                "concurrency": config["concurrency"],
                "batch_size": batch,
                "in_flight": in_flight,
            }
        limit = slots
    elif max_to_queue is not None:
        limit = max_to_queue

    records = (
        session.execute(
            select(Record)
            .where(Record.domain == "media", Record.source_id == source_id)
            .order_by(Record.created_at.asc())
        )
        .scalars()
        .all()
    )

    queued = 0
    skipped_completed = 0
    skipped_active = 0
    skipped_failed = 0
    for record in records:
        if limit is not None and queued >= limit:
            break
        status = _tx_status(record)
        if status == "completed":
            skipped_completed += 1
            continue
        if status in ("queued", "running"):
            skipped_active += 1
            continue
        if status == "failed" and not retry_failed:
            skipped_failed += 1
            continue
        job = enqueue_transcription_sync(session, record)
        if job is not None:
            queued += 1

    return {
        "queued": queued,
        "already_completed": skipped_completed,
        "already_active": skipped_active,
        "skipped_failed": skipped_failed,
        "concurrency": config["concurrency"],
        "batch_size": config["batch_size"],
    }


def drain_auto_transcribe_sync(session: Session) -> dict:
    """
    Top up the transcription pipeline for every source with Auto-transcribe on.

    Keeps filling batches until pending work is gone: each pass enqueues only
    enough to bring global queued+running up to batch_size. Beat / post-job
    hooks call this repeatedly so a 100-item channel finishes in ~5 batches
    of 20 without another Discover.
    """
    from app.models.source import Source, SourcePriority, SourceStatus

    config = get_transcription_settings_sync(session)
    batch = int(config["batch_size"])
    in_flight = _pipeline_transcription_count(session)
    slots = max(0, batch - in_flight)
    if slots <= 0:
        return {
            "queued": 0,
            "skipped_capacity": True,
            "batch_size": batch,
            "in_flight": in_flight,
            "sources": 0,
        }

    priority_order = {
        SourcePriority.urgent: 0,
        SourcePriority.high: 1,
        SourcePriority.normal: 2,
        SourcePriority.low: 3,
        SourcePriority.lowest: 4,
    }
    sources = (
        session.query(Source)
        .filter(
            Source.auto_transcribe.is_(True),
            Source.status == SourceStatus.active,
        )
        .all()
    )
    sources.sort(
        key=lambda s: (
            priority_order.get(s.priority, 9),
            s.created_at.isoformat() if s.created_at else "",
        )
    )

    total_queued = 0
    per_source: list[dict] = []
    for source in sources:
        remaining = slots - total_queued
        if remaining <= 0:
            break
        result = enqueue_pending_for_source_sync(
            session,
            source.id,
            respect_caps=True,
            retry_failed=False,
            max_to_queue=remaining,
        )
        q = int(result.get("queued") or 0)
        total_queued += q
        if q or result.get("skipped_capacity"):
            per_source.append({"source_id": str(source.id), **result})

    return {
        "queued": total_queued,
        "batch_size": batch,
        "in_flight_before": in_flight,
        "sources": len(per_source),
        "details": per_source,
    }
