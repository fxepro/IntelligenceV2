"""Library inventory worker — scans local folders and upserts records."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope


def _run_library_scan_impl(job_id: str):
    with session_scope() as session:
        job = mark_running(session, job_id)
        source_id = job.source_id
        if not source_id:
            raise ValueError("Library scan job missing source_id")

        from app.domain_keys import is_library_domain
        from app.models.record import Record, RecordStatus
        from app.models.source import Source, SourceStatus
        from app.services.library_inventory import scan_source_folder

        source = session.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        if not is_library_domain(source.domain):
            raise ValueError(f"Source {source_id} is not a library source")
        if source.status != SourceStatus.active:
            mark_completed(
                session,
                job_id,
                {"skipped": True, "reason": "source not active", "discovered": 0, "new": 0},
            )
            return {"job_id": job_id, "skipped": True}

        try:
            found_items = scan_source_folder(source.source_url)
        except ValueError as exc:
            mark_failed(session, job_id, str(exc))
            source.error_message = str(exc)[:1024]
            session.commit()
            raise

        seen_keys: set[str] = set()
        new_count = 0
        updated = 0
        purged_nested = 0
        now = datetime.now(timezone.utc)

        for item in found_items:
            dedup = item.canonical_url.rstrip("/")
            seen_keys.add(dedup)
            existing = session.scalar(
                select(Record).where(
                    Record.domain == "library",
                    Record.dedup_key == dedup,
                )
            )
            fields = {
                "media_type": item.media_type,
                "stream_type": item.media_type,
                "extension": item.extension,
                "size_bytes": item.size_bytes,
                "file_size_bytes": item.size_bytes,
                "modified_at": item.modified_at.isoformat(),
                "relative_path": item.relative_path,
                "absolute_path": str(item.absolute_path),
                "inventory_status": "present",
            }
            if existing:
                existing.source_id = source.id
                existing.title = item.title
                existing.canonical_url = item.canonical_url
                existing.fields = fields
                existing.status = RecordStatus.completed
                existing.error_message = None
                existing.captured_at = item.modified_at
                updated += 1
            else:
                session.add(
                    Record(
                        domain="library",
                        source_id=source.id,
                        connector="local_fs",
                        dedup_key=dedup,
                        canonical_url=item.canonical_url,
                        title=item.title,
                        fields=fields,
                        status=RecordStatus.completed,
                        captured_at=item.modified_at,
                    )
                )
                new_count += 1

        existing_rows = (
            session.query(Record)
            .filter(Record.domain == "library", Record.source_id == source.id)
            .all()
        )
        missing = 0
        for row in existing_rows:
            rel = (row.fields or {}).get("relative_path") or ""
            if "/" in rel.replace("\\", "/"):
                session.delete(row)
                purged_nested += 1
                continue
            if row.dedup_key in seen_keys:
                continue
            fields = dict(row.fields or {})
            if fields.get("inventory_status") == "missing":
                continue
            fields["inventory_status"] = "missing"
            row.fields = fields
            row.status = RecordStatus.failed
            row.error_message = "No longer at source root"
            missing += 1

        source.last_checked = now
        source.error_message = None
        session.commit()

        result = {
            "source_id": str(source.id),
            "discovered": len(found_items),
            "new": new_count,
            "updated": updated,
            "missing": missing,
            "purged_nested": purged_nested,
            "total_found": len(found_items),
        }
        mark_completed(session, job_id, result)
        return {"job_id": job_id, **result}


@celery_app.task(
    name="tasks.library_inventory.run_library_scan",
    bind=True,
    max_retries=2,
    soft_time_limit=3600,
    time_limit=3900,
)
def run_library_scan(self, job_id: str):
    try:
        return _run_library_scan_impl(job_id)
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, str(exc))
        raise
