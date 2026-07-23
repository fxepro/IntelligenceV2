import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job, JobStatus, JobType
from app.models.record import Record
from app.models.source import Source, SourcePriority, SourceStatus
from app.models.source_stream import SourceStream
from app.schemas import (
    DiscoverRequest,
    DiscoverSourceResponse,
    SourceCreate,
    SourceList,
    SourceOut,
    SourceStreamOut,
    SourceUpdate,
    TranscriptListItem,
    TranscriptListResponse,
)
from app.services.jobs import enqueue_job
from app.services.source_streams import default_streams_for_platform

router = APIRouter()


def _normalize_tags(raw: list[str] | None) -> list[str]:
    if not raw:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        tag = " ".join(str(item).strip().split())
        if not tag:
            continue
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag[:64])
        if len(out) >= 20:
            break
    return out


def _source_tags(source: Source) -> list[str]:
    raw = getattr(source, "tags", None)
    if isinstance(raw, list):
        return [str(t) for t in raw if t]
    return []


def _source_priority(source: Source) -> SourcePriority:
    value = getattr(source, "priority", None)
    if isinstance(value, SourcePriority):
        return value
    if isinstance(value, str):
        try:
            return SourcePriority(value)
        except ValueError:
            pass
    return SourcePriority.normal


async def _stream_item_counts(
    db: AsyncSession, source_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict[str, int]]:
    """Per-source item counts keyed by stream_type (from records.fields)."""
    if not source_ids:
        return {}
    stream_type_expr = func.coalesce(Record.fields["stream_type"].as_string(), "unknown")
    rows = (
        await db.execute(
            select(
                Record.source_id,
                stream_type_expr.label("stream_type"),
                func.count().label("n"),
            )
            .where(Record.domain == "media", Record.source_id.in_(source_ids))
            .group_by(Record.source_id, stream_type_expr)
        )
    ).all()
    out: dict[uuid.UUID, dict[str, int]] = {}
    for sid, stream_type, n in rows:
        if sid is None:
            continue
        key = sid if isinstance(sid, uuid.UUID) else uuid.UUID(str(sid))
        out.setdefault(key, {})[str(stream_type)] = int(n)
    return out


async def _transcription_completed_counts(
    db: AsyncSession, source_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Per-source count of media records with transcription_status=completed."""
    if not source_ids:
        return {}
    rows = (
        await db.execute(
            select(Record.source_id, func.count().label("n"))
            .where(
                Record.domain == "media",
                Record.source_id.in_(source_ids),
                Record.fields["transcription_status"].as_string() == "completed",
            )
            .group_by(Record.source_id)
        )
    ).all()
    out: dict[uuid.UUID, int] = {}
    for sid, n in rows:
        if sid is None:
            continue
        key = sid if isinstance(sid, uuid.UUID) else uuid.UUID(str(sid))
        out[key] = int(n)
    return out


async def _load_streams(
    db: AsyncSession, source_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[SourceStream]]:
    if not source_ids:
        return {}
    rows = (
        await db.scalars(
            select(SourceStream)
            .where(SourceStream.source_id.in_(source_ids))
            .order_by(SourceStream.stream_type.asc())
        )
    ).all()
    out: dict[uuid.UUID, list[SourceStream]] = {}
    for row in rows:
        out.setdefault(row.source_id, []).append(row)
    return out


def _source_out(
    s: Source,
    streams: list[SourceStream],
    stream_counts: dict[str, int],
    *,
    transcription_completed: int = 0,
) -> SourceOut:
    stream_outs: list[SourceStreamOut] = []
    total_items = 0
    for stream in streams:
        count = stream_counts.get(
            stream.stream_type.value
            if hasattr(stream.stream_type, "value")
            else str(stream.stream_type),
            0,
        )
        total_items += count
        stream_outs.append(
            SourceStreamOut(
                id=stream.id,
                stream_type=stream.stream_type,
                stream_url=stream.stream_url,
                enabled=stream.enabled,
                item_count=count,
                last_checked=stream.last_checked,
                error_message=stream.error_message,
            )
        )
    primary_type = streams[0].stream_type if streams else s.source_type
    tx_done = total_items > 0 and transcription_completed >= total_items
    return SourceOut(
        id=s.id,
        domain=s.domain,
        catalog_id=getattr(s, "catalog_id", None),
        platform=s.platform,
        source_type=primary_type,
        source_url=s.source_url,
        vanity_url=getattr(s, "vanity_url", None),
        name=s.name,
        description=s.description,
        category=getattr(s, "category", None),
        tags=_source_tags(s),
        priority=_source_priority(s),
        access_mode="public",
        autorun=s.autorun,
        auto_transcribe=bool(getattr(s, "auto_transcribe", False)),
        status=s.status,
        error_message=s.error_message,
        last_checked=s.last_checked,
        subscriber_count=None,
        video_count=total_items,
        total_views=None,
        joined_at=None,
        item_count=total_items,
        reel_count=total_items,
        transcription_completed=transcription_completed,
        transcription_done=tx_done,
        streams=stream_outs,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


async def _serialize_source(db: AsyncSession, source: Source) -> SourceOut:
    streams_by_source = await _load_streams(db, [source.id])
    counts_by_source = await _stream_item_counts(db, [source.id])
    tx_by_source = await _transcription_completed_counts(db, [source.id])
    streams = streams_by_source.get(source.id, [])
    counts = counts_by_source.get(source.id, {})
    return _source_out(
        source,
        streams,
        counts,
        transcription_completed=tx_by_source.get(source.id, 0),
    )


@router.get("", response_model=SourceList)
async def list_sources(
    domain: str = Query("media"),
    db: AsyncSession = Depends(get_db),
):
    items = (
        await db.scalars(
            select(Source).where(Source.domain == domain).order_by(Source.created_at.desc())
        )
    ).all()
    source_ids = [s.id for s in items]
    streams_by_source = await _load_streams(db, source_ids)
    counts_by_source = await _stream_item_counts(db, source_ids)
    tx_by_source = await _transcription_completed_counts(db, source_ids)
    total = await db.scalar(select(func.count()).select_from(Source).where(Source.domain == domain))
    return SourceList(
        items=[
            _source_out(
                s,
                streams_by_source.get(s.id, []),
                counts_by_source.get(s.id, {}),
                transcription_completed=tx_by_source.get(s.id, 0),
            )
            for s in items
        ],
        total=total or 0,
    )


@router.post("", response_model=SourceOut, status_code=201)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    import asyncio

    url = payload.source_url.rstrip("/")
    vanity_url = (payload.vanity_url or "").rstrip("/") or None
    platform = payload.platform.value if hasattr(payload.platform, "value") else str(payload.platform)

    if platform == "facebook":
        from app.services.facebook_reels import (
            extract_facebook_profile_id,
            resolve_facebook_identity_from_vanity,
        )

        entered = (vanity_url or url).rstrip("/")
        vanity, identity, _page_id = await asyncio.to_thread(
            resolve_facebook_identity_from_vanity, entered
        )
        if not identity:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not find page_id in Facebook page source for that vanity URL. "
                    "Check the URL and that Access has a valid Facebook session."
                ),
            )
        url = identity
        # Preserve vanity only when the user entered a handle URL, not an id URL.
        if extract_facebook_profile_id(entered):
            vanity_url = vanity_url if vanity_url and vanity_url != identity else None
        else:
            vanity_url = vanity or entered

    existing = await db.scalar(select(Source).where(Source.source_url == url))
    if existing:
        raise HTTPException(status_code=409, detail="Source URL already exists")

    from app.services.catalog_ids import allocate_catalog_id

    catalog_id = (payload.catalog_id or "").strip().upper() or None
    if catalog_id:
        clash = await db.scalar(
            select(Source).where(
                Source.domain == payload.domain,
                Source.catalog_id == catalog_id,
            )
        )
        if clash:
            raise HTTPException(
                status_code=409,
                detail=f"catalog_id {catalog_id} already exists in domain {payload.domain}",
            )
    else:
        catalog_id = await allocate_catalog_id(db, payload.domain)

    category = (payload.category or "").strip() or None
    if category:
        category = category[:128]
    source = Source(
        domain=payload.domain,
        catalog_id=catalog_id,
        platform=payload.platform,
        source_type=payload.source_type,
        source_url=url,
        vanity_url=vanity_url,
        name=payload.name,
        description=payload.description,
        category=category,
        tags=_normalize_tags(payload.tags),
        priority=payload.priority,
        autorun=payload.autorun,
        auto_transcribe=payload.auto_transcribe,
    )
    db.add(source)
    await db.flush()

    for stream_type, enabled, stream_url in default_streams_for_platform(
        payload.platform,
        payload.source_type,
        source_url=url,
        stream_urls=payload.stream_urls,
    ):
        db.add(
            SourceStream(
                source_id=source.id,
                stream_type=stream_type,
                stream_url=stream_url,
                enabled=enabled,
            )
        )
    await db.flush()
    await db.refresh(source)
    return await _serialize_source(db, source)


@router.get("/{source_id}/transcripts", response_model=TranscriptListResponse)
async def list_source_transcripts(
    source_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Ordered transcript list for sequential reading on a channel."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    base = (
        select(Record)
        .where(
            Record.domain == "media",
            Record.source_id == source_id,
            Record.fields["transcription_status"].as_string() == "completed",
            Record.fields["transcript"].isnot(None),
        )
        .order_by(Record.created_at.asc())
    )
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        await db.scalars(base.offset((page - 1) * page_size).limit(page_size))
    ).all()

    items: list[TranscriptListItem] = []
    for record in rows:
        fields = record.fields or {}
        transcript = fields.get("transcript") or {}
        full_text = transcript.get("full_text") or transcript.get("text") or ""
        if not full_text:
            continue
        published = fields.get("published_at")
        items.append(
            TranscriptListItem(
                media_id=record.id,
                title=record.title or fields.get("title"),
                canonical_url=record.canonical_url,
                thumbnail_url=fields.get("thumbnail_url"),
                published_at=published if isinstance(published, str) else None,
                discovered_at=record.created_at.isoformat() if record.created_at else None,
                status="completed",
                full_text=full_text,
                language=transcript.get("language"),
                word_count=transcript.get("word_count"),
                model_used=transcript.get("model"),
                generated_at=transcript.get("created_at"),
            )
        )
    return TranscriptListResponse(
        items=items,
        total=total or len(items),
        page=page,
        page_size=page_size,
    )


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return await _serialize_source(db, source)


@router.patch("/{source_id}", response_model=SourceOut)
async def patch_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await _patch_source_impl(source_id, payload, db)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc


async def _patch_source_impl(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    db: AsyncSession,
) -> SourceOut:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    data = payload.model_dump(exclude_unset=True)
    stream_urls = data.pop("stream_urls", None)
    if "tags" in data:
        data["tags"] = _normalize_tags(data["tags"])
    if "catalog_id" in data:
        cid = (data["catalog_id"] or "").strip().upper() or None
        data["catalog_id"] = cid
        if cid:
            clash = await db.scalar(
                select(Source).where(
                    Source.domain == source.domain,
                    Source.catalog_id == cid,
                    Source.id != source.id,
                )
            )
            if clash:
                raise HTTPException(
                    status_code=409,
                    detail=f"catalog_id {cid} already exists in domain {source.domain}",
                )
    if "source_url" in data and data["source_url"]:
        import asyncio

        entered = data["source_url"].rstrip("/")
        data["source_url"] = entered
        platform = (
            source.platform.value if hasattr(source.platform, "value") else str(source.platform)
        )
        if platform == "facebook":
            from app.services.facebook_reels import (
                extract_facebook_profile_id,
                resolve_facebook_identity_from_vanity,
            )

            def _fb_key(u: str) -> str:
                return (
                    u.rstrip("/")
                    .lower()
                    .replace("https://m.facebook.com", "https://www.facebook.com")
                    .replace("https://facebook.com", "https://www.facebook.com")
                )

            existing = (source.source_url or "").rstrip("/")
            vanity_existing = (source.vanity_url or "").rstrip("/")
            entered_id = extract_facebook_profile_id(entered)
            entered_key = _fb_key(entered)
            existing_key = _fb_key(existing) if existing else ""
            vanity_key = _fb_key(vanity_existing) if vanity_existing else ""
            same_as_stored = bool(entered_key) and entered_key in {existing_key, vanity_key}

            # Skip scrape when URL unchanged (including vanity-only rows with no page_id).
            if same_as_stored:
                data["source_url"] = existing or entered
            elif entered_id:
                data["source_url"] = (
                    f"https://www.facebook.com/profile.php?id={entered_id}"
                )
            else:
                try:
                    vanity, identity, _page_id = await asyncio.to_thread(
                        resolve_facebook_identity_from_vanity, entered
                    )
                except Exception as exc:
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            f"Facebook identity resolve failed: {type(exc).__name__}: {exc}"
                        ),
                    ) from exc
                if identity:
                    data["source_url"] = identity
                    if not entered_id:
                        data["vanity_url"] = vanity or entered
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Could not find page_id in Facebook page source for that vanity URL. "
                            "Check the URL and that Access has a valid Facebook session."
                        ),
                    )
    if "vanity_url" in data and data["vanity_url"]:
        data["vanity_url"] = data["vanity_url"].rstrip("/")
    if "source_url" in data and data["source_url"]:
        clash = await db.scalar(
            select(Source.id).where(
                Source.source_url == data["source_url"],
                Source.id != source.id,
            )
        )
        if clash:
            raise HTTPException(
                status_code=409,
                detail=f"Another source already uses URL {data['source_url']}",
            )
    for k, v in data.items():
        setattr(source, k, v)
    if "tags" in data:
        # JSONB assignment can be missed by change tracking without an explicit flag.
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(source, "tags")
    if stream_urls is not None:
        streams = (
            await db.scalars(
                select(SourceStream).where(SourceStream.source_id == source.id)
            )
        ).all()
        for stream in streams:
            stream_type = (
                stream.stream_type.value
                if hasattr(stream.stream_type, "value")
                else str(stream.stream_type)
            )
            if stream_type in stream_urls:
                from app.services.source_streams import normalize_stream_url

                url = normalize_stream_url(stream_urls[stream_type])
                stream.stream_url = url
                stream.enabled = bool(url)
    await db.flush()
    await db.refresh(source)
    return await _serialize_source(db, source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Hard-delete a channel and all of its catalog (media + jobs). Streams cascade via FK."""
    from sqlalchemy import delete, text

    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.execute(delete(Job).where(Job.source_id == source_id))
    await db.execute(
        delete(Job).where(
            Job.record_id.in_(select(Record.id).where(Record.source_id == source_id))
        )
    )
    # Explicit SQL — records have no FK to sources.
    await db.execute(
        text("DELETE FROM records WHERE source_id = CAST(:sid AS uuid)"),
        {"sid": str(source_id)},
    )
    await db.delete(source)
    await db.flush()


@router.post("/{source_id}/discover", response_model=DiscoverSourceResponse)
async def discover_source(
    source_id: uuid.UUID,
    payload: DiscoverRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Enqueue discovery — worker scans all enabled streams for this source."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    body = payload or DiscoverRequest()
    job = await enqueue_job(
        db,
        job_type=JobType.discover,
        domain=source.domain,
        source_id=source.id,
        payload={
            "max_items": body.max_items,
            "source_url": source.source_url,
            "platform": source.platform.value,
        },
    )
    return DiscoverSourceResponse(
        source_id=source.id,
        job_id=job.id,
        new=0,
        total_found=0,
        items=[],
        status=job.status.value,
    )


async def _enqueue_transcription(record: Record, db: AsyncSession) -> Job:
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


@router.post("/{source_id}/transcribe-all")
async def transcribe_all(
    source_id: uuid.UUID,
    retry_failed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Queue transcription for every pending item on this source (manual Transcribe all)."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    records = (
        await db.scalars(
            select(Record)
            .where(Record.domain == "media", Record.source_id == source_id)
            .order_by(Record.created_at.asc())
        )
    ).all()

    queued: list[str] = []
    skipped_completed = 0
    skipped_active = 0
    skipped_failed = 0
    for record in records:
        tx_status = (record.fields or {}).get("transcription_status") or "pending"
        if tx_status == "completed":
            skipped_completed += 1
            continue
        if tx_status in ("queued", "running"):
            skipped_active += 1
            continue
        if tx_status == "failed" and not retry_failed:
            skipped_failed += 1
            continue
        try:
            job = await _enqueue_transcription(record, db)
            queued.append(str(job.id))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    unique_queued = list(dict.fromkeys(queued))
    completed = skipped_completed
    total = len(records)
    active = skipped_active + len(unique_queued)
    channel_status = (
        "done"
        if total > 0 and completed == total
        else "running"
        if active
        else "pending"
    )
    return {
        "source_id": str(source_id),
        "total": total,
        "queued": len(unique_queued),
        "already_completed": skipped_completed,
        "already_active": skipped_active,
        "skipped_failed": skipped_failed,
        "completed": completed,
        "pending_after": max(0, total - completed - skipped_active - len(unique_queued)),
        "job_ids": unique_queued,
        "status": channel_status,
    }

