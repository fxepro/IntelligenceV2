"""Discovery worker — runs connectors and upserts media records."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.postgresql import insert

from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope


def _iso_to_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _is_transient_db_error(exc: BaseException | str) -> bool:
    """Postgres dropped / pool blip — not a channel failure."""
    text = str(exc)
    return any(
        marker in text
        for marker in (
            "server closed the connection unexpectedly",
            "consuming input failed",
            "connection is closed",
            "ConnectionDoesNotExistError",
            "InterfaceError",
        )
    ) or "OperationalError" in type(exc).__name__


def _safe_title(
    title: str | None,
    external_id: str | None = None,
    *,
    stream_type: str | None = None,
) -> str | None:
    from app.services.discover_media import _is_placeholder_title
    from app.services.facebook_reels import clean_reel_title

    cleaned = clean_reel_title(title)
    if cleaned and not _is_placeholder_title(cleaned):
        return cleaned
    if external_id:
        label = "Video" if stream_type == "facebook_videos" else "Reel"
        return f"{label} {external_id}"
    return None


def _persist_items(
    session,
    source,
    items,
    job_id: str,
    platform: str,
    stream_type: str,
) -> tuple[int, int]:
    from sqlalchemy import select

    from app.models.record import Record, RecordStatus
    from app.services.discover_media import _is_placeholder_title

    new_count = 0
    require_thumb = platform in ("facebook", "youtube")
    for it in items:
        if not it.canonical_url:
            continue
        dedup = it.canonical_url.rstrip("/")
        title = _safe_title(it.title, it.external_id, stream_type=stream_type)
        existing = session.scalar(
            select(Record).where(Record.domain == "media", Record.dedup_key == dedup)
        )
        if existing:
            fields = dict(existing.fields or {})
            if it.duration_seconds is not None:
                fields["duration_seconds"] = it.duration_seconds
            if it.published_at:
                fields["published_at"] = it.published_at
            if it.view_count is not None:
                fields["view_count"] = it.view_count
            if it.file_size_bytes is not None:
                fields["file_size_bytes"] = it.file_size_bytes
            if it.thumbnail_url:
                fields["thumbnail_url"] = it.thumbnail_url
            if it.channel_name:
                fields["channel_name"] = it.channel_name
            if it.description:
                fields["description"] = it.description
            fields["stream_type"] = stream_type
            fields["content_type"] = it.content_type
            fields["platform"] = platform
            existing.fields = fields
            # Never leave "Reel tile preview" stuck — overwrite any placeholder.
            if title and (_is_placeholder_title(existing.title) or not existing.title):
                existing.title = title
            published_dt = _iso_to_dt(it.published_at)
            if published_dt and not existing.captured_at:
                existing.captured_at = published_dt
            continue

        # Guarantee: never create FB/YT media rows without a playable grid thumb.
        if require_thumb and not (it.thumbnail_url or "").strip():
            continue

        fields = {
            "platform": platform,
            "stream_type": stream_type,
            "content_type": it.content_type,
            "thumbnail_url": it.thumbnail_url,
            "channel_name": it.channel_name,
            "duration_seconds": it.duration_seconds,
            "file_size_bytes": it.file_size_bytes,
            "view_count": it.view_count,
            "description": it.description,
            "published_at": it.published_at,
            "enclosure_url": it.enclosure_url,
            "download_status": "pending",
            "transcription_status": "pending",
            "local_file_path": None,
        }
        status = RecordStatus.needs_review
        # Prefer an existence check over INSERT rowcount: with
        # ON CONFLICT DO NOTHING, drivers often report 0 even when a row was inserted.
        before = session.scalar(
            select(Record.id).where(Record.domain == "media", Record.dedup_key == dedup)
        )
        if before:
            continue
        stmt = (
            insert(Record)
            .values(
                id=uuid.uuid4(),
                domain="media",
                source_id=source.id,
                connector=f"discover.{platform}",
                external_id=it.external_id,
                dedup_key=dedup,
                canonical_url=it.canonical_url,
                title=title,
                fields=fields,
                status=status,
                captured_at=_iso_to_dt(it.published_at),
                provenance={
                    "job_id": job_id,
                    "connector": f"discover.{platform}",
                    "stream_type": stream_type,
                },
            )
            .on_conflict_do_nothing(constraint="uq_records_domain_dedup")
        )
        session.execute(stmt)
        after = session.scalar(
            select(Record.id).where(Record.domain == "media", Record.dedup_key == dedup)
        )
        if after:
            new_count += 1
    return len(items), new_count


@celery_app.task(name="tasks.discovery.run_autorun_scan")
def run_autorun_scan():
    """Queue due discovery jobs for active sources with Autorun enabled."""
    from app.models.job import Job, JobStatus, JobType
    from app.models.source import Source, SourceStatus
    from app.models.source_stream import SourceStream

    from app.services.discovery_config import get_discovery_settings_sync

    now = datetime.now(timezone.utc)
    queued = 0
    with session_scope() as session:
        config = get_discovery_settings_sync(session)
        interval_minutes = config["interval_minutes"]
        max_items = config["max_items"]
        due_before = now - timedelta(minutes=interval_minutes)

        sources = (
            session.query(Source)
            .filter(
                Source.autorun.is_(True),
                Source.status == SourceStatus.active,
            )
            .all()
        )
        for source in sources:
            if source.last_checked and source.last_checked > due_before:
                continue
            active_job = (
                session.query(Job.id)
                .filter(
                    Job.job_type == JobType.discover,
                    Job.source_id == source.id,
                    Job.status.in_([JobStatus.queued, JobStatus.running]),
                )
                .first()
            )
            if active_job:
                continue

            job = Job(
                job_type=JobType.discover,
                status=JobStatus.queued,
                domain=source.domain,
                source_id=source.id,
                payload={"max_items": max_items, "trigger": "autorun"},
                progress=0.0,
            )
            session.add(job)
            session.flush()
            session.commit()  # Job must exist before the worker can consume it.
            try:
                task = celery_app.send_task(
                    "tasks.discovery.run_discover",
                    args=[str(job.id)],
                    queue="discovery",
                )
                job.celery_task_id = task.id
                session.commit()
                queued += 1
            except Exception as exc:
                job.status = JobStatus.failed
                job.error_message = f"Autorun enqueue failed: {type(exc).__name__}: {exc}"[:2000]
                job.finished_at = now
                session.commit()
    return {"queued": queued}


@celery_app.task(name="tasks.discovery.run_url_check_scan")
def run_url_check_scan(force: bool = False):
    """Retired — URL check was removed (false positives / noise)."""
    return {"checked": 0, "failed": 0, "skipped": "removed"}


@celery_app.task(
    name="tasks.discovery.run_discover",
    bind=True,
    max_retries=3,
    soft_time_limit=120,
    time_limit=150,
)
def run_discover(self, job_id: str):
    try:
        # Library courses use a separate impl — must not nest session_scope (solo worker deadlock).
        with session_scope() as session:
            from app.models.job import Job

            job = session.get(Job, uuid.UUID(str(job_id)))
            if not job:
                raise ValueError(f"Job {job_id} not found")
            if not job.source_id:
                raise ValueError("Discover job missing source_id")
            from app.models.source import Source

            source = session.get(Source, job.source_id)
            if not source:
                raise ValueError(f"Source {job.source_id} not found")
            from app.domain_keys import is_courses_domain

            courses_route = is_courses_domain(source.domain)

        if courses_route:
            from tasks.course_discovery import _run_course_discover_impl

            return _run_course_discover_impl(job_id)

        with session_scope() as session:
            job = mark_running(session, job_id)
            payload = job.payload or {}

            if not job.source_id:
                raise ValueError("Discover job missing source_id")

            from app.models.source import Source, SourceStatus
            from app.models.source_stream import SourceStream

            source = session.get(Source, job.source_id)
            if not source:
                raise ValueError(f"Source {job.source_id} not found")

            # Media domain discovery continues below
            max_items = int(payload.get("max_items") or 50)

            if source.status != SourceStatus.active:
                mark_completed(
                    session,
                    job_id,
                    {"skipped": True, "reason": "source not active", "discovered": 0, "new": 0},
                )
                return {"job_id": job_id, "skipped": True}

            platform = source.platform.value if hasattr(source.platform, "value") else str(source.platform)
            from app.services.discover_media import (
                extract_items,
                facebook_items,
                facebook_video_items,
            )

            stream_rows = (
                session.query(SourceStream)
                .filter(SourceStream.source_id == source.id)
                .order_by(SourceStream.stream_type.asc())
                .all()
            )

            stream_specs: list[tuple[str, str, object | None]] = []
            if stream_rows:
                for row in stream_rows:
                    if not row.enabled:
                        continue
                    stream_url = (row.stream_url or "").strip()
                    if not stream_url:
                        continue
                    stream_type = (
                        row.stream_type.value
                        if hasattr(row.stream_type, "value")
                        else str(row.stream_type)
                    )
                    stream_specs.append((stream_type, stream_url, row.id))
            elif source.source_url:
                stream_specs = [
                    (
                        source.source_type.value
                        if hasattr(source.source_type, "value")
                        else str(source.source_type),
                        source.source_url.strip(),
                        None,
                    )
                ]

            total_found = 0
            total_new = 0
            stream_results: list[dict] = []
            attempted = 0
            any_ok = False

            for stream_type, stream_url, stream_id in stream_specs:
                attempted += 1
                try:
                    if platform == "facebook" and stream_type == "facebook_reels":
                        items, resolved_page = facebook_items(stream_url, max_items)
                        if resolved_page and resolved_page.rstrip("/") != source.source_url.rstrip("/"):
                            clash = (
                                session.query(Source)
                                .filter(Source.source_url == resolved_page, Source.id != source.id)
                                .first()
                            )
                            if not clash:
                                source.source_url = resolved_page
                    elif platform == "facebook" and stream_type == "facebook_videos":
                        items, _resolved_videos = facebook_video_items(stream_url, max_items)
                    else:
                        items = extract_items(
                            platform,
                            stream_url,
                            max_items,
                            source_type=stream_type,
                        )

                    found, new = _persist_items(
                        session, source, items, job_id, platform, stream_type
                    )
                    if stream_id:
                        stream_row = session.get(SourceStream, stream_id)
                        if stream_row:
                            stream_row.last_checked = datetime.now(timezone.utc)
                            if (
                                stream_type == "facebook_videos"
                                and found == 0
                                and not items
                            ):
                                stream_row.error_message = (
                                    "No videos found on Videos tab "
                                    "(tab may be empty, hidden, or login-gated)"
                                )
                            else:
                                stream_row.error_message = None
                    session.commit()
                    any_ok = True
                    total_found += found
                    total_new += new
                    stream_results.append(
                        {"stream_type": stream_type, "found": found, "new": new}
                    )
                except Exception as exc:
                    session.rollback()
                    source = session.get(Source, job.source_id)
                    err_text = (
                        "database connection dropped — retry Discover"
                        if _is_transient_db_error(exc)
                        else f"{type(exc).__name__}: {exc}"[:500]
                    )
                    if stream_id:
                        stream_row = session.get(SourceStream, stream_id)
                        if stream_row:
                            stream_row.error_message = err_text[:1000]
                            stream_row.last_checked = datetime.now(timezone.utc)
                            session.commit()
                    stream_results.append(
                        {
                            "stream_type": stream_type,
                            "found": 0,
                            "new": 0,
                            "error": err_text,
                            "transient": _is_transient_db_error(exc),
                        }
                    )

            source = session.get(Source, job.source_id)
            source.last_checked = datetime.now(timezone.utc)
            if attempted == 0:
                source.error_message = None
                if source.status == SourceStatus.error:
                    source.status = SourceStatus.active
                stream_results.append({"skipped": "no stream URLs configured"})
            elif any_ok:
                source.error_message = None
                if source.status == SourceStatus.error:
                    source.status = SourceStatus.active
            else:
                errs = [s for s in stream_results if s.get("error")]
                # Don't paint the channel red for Postgres pool blips.
                if errs and all(s.get("transient") for s in errs):
                    source.error_message = None
                    if source.status == SourceStatus.error:
                        source.status = SourceStatus.active
                else:
                    source.status = SourceStatus.error
                    source.error_message = (
                        (errs[0].get("error") if errs else None) or "All streams failed"
                    )[:1000]

            auto_tx = {"queued": 0}
            if any_ok and bool(getattr(source, "auto_transcribe", False)):
                # First batch now; Beat + post-transcribe drain keep topping up
                # until pending items are gone (batch_size at a time).
                from app.services.transcription_queue import enqueue_pending_for_source_sync

                auto_tx = enqueue_pending_for_source_sync(
                    session,
                    source.id,
                    respect_caps=True,
                    retry_failed=False,
                )

            mark_completed(
                session,
                job_id,
                {
                    "source_id": str(source.id),
                    "platform": platform,
                    "source_url": source.source_url,
                    "discovered": total_found,
                    "new": total_new,
                    "total_found": total_found,
                    "streams": stream_results,
                    "auto_transcribe_queued": auto_tx.get("queued", 0),
                    "auto_transcribe": auto_tx,
                },
            )
        return {"job_id": job_id, "ok": True, "auto_transcribe_queued": auto_tx.get("queued", 0)}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.discovery.run_research", bind=True, max_retries=2)
def run_research(self, job_id: str):
    """Research is served sync by the API today; task kept for job-type parity."""
    try:
        with session_scope() as session:
            mark_running(session, job_id)
            mark_completed(session, job_id, {"note": "research runs via API providers"})
        return {"job_id": job_id, "ok": True}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        raise
