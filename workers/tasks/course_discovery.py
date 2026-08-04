"""Course discovery worker — scrapes course sources and writes lessons to v2/data/."""
from __future__ import annotations

from datetime import datetime, timezone

from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope


def _run_course_discover_impl(job_id: str):
    """Parse curriculum and persist lessons under v2/data/{course_id}/."""
    with session_scope() as session:
        job = mark_running(session, job_id)
        source_id = job.source_id

        if not source_id:
            raise ValueError("Course discover job missing source_id")

        from app.models.source import Source, SourceStatus
        from app.services.course_parsers.registry import discover_curriculum, lessons_to_dicts
        from app.services.library_course_paths import persist_course_lessons
        from app.services.library_course_ready import ensure_library_course_ready

        source = session.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        if source.status != SourceStatus.active:
            mark_completed(
                session,
                job_id,
                {"skipped": True, "reason": "source not active", "discovered": 0, "new": 0},
            )
            return {"job_id": job_id, "skipped": True}

        course_id, connector, curriculum_url = ensure_library_course_ready(source)

        if connector == "manual":
            raise ValueError(
                "Curriculum type is Manual only — use Add YouTube lessons, "
                "or set Video curriculum / Article hub / Generic website before Discover."
            )
        if not curriculum_url.startswith("http"):
            raise ValueError(
                "Source URL must be an http(s) curriculum page for auto-discover "
                "(set Source URL or vanity URL for mi:// sources)"
            )

        parse_result = discover_curriculum(
            curriculum_url,
            connector,
            id_prefix=course_id,
        )

        if not parse_result.lessons:
            anomaly = ", ".join(parse_result.anomalies) or "COURSE_NO_LESSONS"
            raise RuntimeError(
                f"Discovery found 0 lessons ({parse_result.parser_key}, "
                f"fetch={parse_result.fetch_mode}, score={parse_result.quality_score}): {anomaly}"
            )

        lessons = lessons_to_dicts(parse_result.lessons)
        course_name = (source.name or parse_result.course_title or course_id).strip()
        disk_result = persist_course_lessons(
            course_id=course_id,
            course_name=course_name,
            lessons=lessons,
        )

        from app.services.library_source_lessons import sync_lessons_from_disk

        db_synced = sync_lessons_from_disk(session, source_id=source.id, course_id=course_id)

        source.last_checked = datetime.now(timezone.utc)
        source.error_message = None
        session.commit()

        result = {
            "source_id": str(source.id),
            "course_id": course_id,
            "connector": connector,
            "parser_key": parse_result.parser_key,
            "fetch_mode": parse_result.fetch_mode,
            "quality_score": parse_result.quality_score,
            "anomalies": parse_result.anomalies,
            "curriculum_url": curriculum_url,
            "discovered": len(lessons),
            "new": disk_result.get("lessons_written", 0),
            "data_dir": disk_result.get("data_dir"),
            "lessons_skipped_manual": disk_result.get("lessons_skipped_manual", 0),
            "db_lessons_synced": db_synced,
        }
        mark_completed(session, job_id, result)

    return {"job_id": job_id, "ok": True, **result}


@celery_app.task(
    name="tasks.course_discovery.run_discover",
    bind=True,
    max_retries=2,
    soft_time_limit=120,
    time_limit=150,
)
def run_course_discover(self, job_id: str):
    """Discover lessons for a course source; writes to v2/data/{course_id}/."""
    try:
        return _run_course_discover_impl(job_id)
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        raise self.retry(exc=exc, countdown=60)
