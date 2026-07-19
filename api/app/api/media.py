"""Media list compat for Intelligence UI — maps `records` until media_items exists."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.record import Record
from app.models.source import Source
from app.schemas import MediaItemList, MediaItemOut
from app.models.job import Job, JobStatus, JobType
from app.services.discovery_config import (
    MEDIA_PAGE_SIZE_CEILING,
    get_discovery_settings,
)
from app.services.jobs import enqueue_job

router = APIRouter()


def _record_to_media(r: Record, platform: str | None = None) -> MediaItemOut:
    fields = r.fields or {}
    transcription_status = fields.get("transcription_status") or "pending"
    download_status = fields.get("download_status") or "pending"
    if transcription_status == "completed":
        display_status = "completed"
    elif transcription_status == "failed":
        display_status = "failed"
    elif transcription_status == "running":
        display_status = "transcribing"
    elif download_status == "running":
        display_status = "downloading"
    elif transcription_status == "queued":
        display_status = "queued"
    else:
        display_status = "pending"
    published = None
    raw_pub = fields.get("published_at")
    if isinstance(raw_pub, str):
        try:
            published = datetime.fromisoformat(raw_pub)
        except ValueError:
            published = None
    elif isinstance(raw_pub, datetime):
        published = raw_pub
    return MediaItemOut(
        id=r.id,
        source_id=r.source_id,
        platform=platform or fields.get("platform"),
        external_id=r.external_id,
        canonical_url=r.canonical_url,
        title=r.title or fields.get("title"),
        description=fields.get("description"),
        content_type=fields.get("content_type"),
        stream_type=fields.get("stream_type"),
        thumbnail_url=fields.get("thumbnail_url"),
        channel_name=fields.get("channel_name"),
        duration_seconds=fields.get("duration_seconds"),
        file_size_bytes=fields.get("file_size_bytes"),
        view_count=fields.get("view_count"),
        download_status=download_status,
        transcription_status=transcription_status,
        transcript=fields.get("transcript"),
        summary=fields.get("summary"),
        published_at=published or r.captured_at,
        discovered_at=r.created_at,
        processed_at=None,
        status=display_status,
        error_message=r.error_message,
    )


@router.get("", response_model=MediaItemList)
async def list_media(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=MEDIA_PAGE_SIZE_CEILING),
    source_id: uuid.UUID | None = None,
    stream_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    discovery = await get_discovery_settings(db)
    page_size = min(page_size, discovery["media_page_size"])

    q = select(Record).where(Record.domain == "media")
    if source_id:
        q = q.where(Record.source_id == source_id)
    if stream_type:
        q = q.where(Record.fields["stream_type"].as_string() == stream_type)

    count_q = select(func.count()).select_from(Record).where(Record.domain == "media")
    if source_id:
        count_q = count_q.where(Record.source_id == source_id)
    if stream_type:
        count_q = count_q.where(Record.fields["stream_type"].as_string() == stream_type)
    total = await db.scalar(count_q)

    rows = (
        await db.scalars(
            q.order_by(Record.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()

    platform_by_source: dict[uuid.UUID, str] = {}
    source_ids = {r.source_id for r in rows if r.source_id}
    if source_ids:
        sources = (
            await db.scalars(select(Source).where(Source.id.in_(list(source_ids))))
        ).all()
        platform_by_source = {
            s.id: s.platform.value if hasattr(s.platform, "value") else str(s.platform)
            for s in sources
        }

    items = [
        _record_to_media(r, platform_by_source.get(r.source_id) if r.source_id else None)
        for r in rows
    ]
    return MediaItemList(items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/{media_id}", response_model=MediaItemOut)
async def get_media(media_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = await db.get(Record, media_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media not found")
    platform = None
    if record.source_id:
        source = await db.get(Source, record.source_id)
        if source:
            platform = source.platform.value if hasattr(source.platform, "value") else str(source.platform)
    return _record_to_media(record, platform)


async def _enqueue_transcription(record: Record, db: AsyncSession):
    existing = await db.scalar(
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
    return await enqueue_job(
        db,
        job_type=JobType.transcribe,
        domain=record.domain,
        source_id=record.source_id,
        record_id=record.id,
        payload={"dedup_key": record.dedup_key},
    )


@router.post("/transcribe-batch")
async def transcribe_batch(
    source_id: uuid.UUID | None = None,
    limit: int = Query(3, ge=1, le=10),
    retry_failed: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Queue a small batch for testing — default 3, hard max 10."""
    q = select(Record).where(Record.domain == "media")
    if source_id:
        q = q.where(Record.source_id == source_id)
    records = (await db.scalars(q.order_by(Record.created_at.asc()))).all()
    queued: list[str] = []
    skipped = 0
    for record in records:
        if len(queued) >= limit:
            break
        transcription_status = (record.fields or {}).get("transcription_status")
        if transcription_status in ("completed", "queued", "running"):
            skipped += 1
            continue
        if transcription_status == "failed" and not retry_failed:
            skipped += 1
            continue
        job = await _enqueue_transcription(record, db)
        queued.append(str(job.id))
    return {
        "queued": len(set(queued)),
        "skipped": skipped,
        "limit": limit,
        "job_ids": list(dict.fromkeys(queued)),
    }


@router.post("/{media_id}/transcribe")
@router.post("/{media_id}/reprocess")
async def reprocess_media(media_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = await db.get(Record, media_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media not found")
    try:
        job = await _enqueue_transcription(record, db)
    except RuntimeError as exc:
        fields = dict(record.fields or {})
        fields["transcription_status"] = "failed"
        record.fields = fields
        await db.flush()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"job_id": str(job.id), "status": job.status.value}
