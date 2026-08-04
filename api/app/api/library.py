"""Library items list + asset streaming for local folder sources."""
from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain_keys import LIBRARY_DOMAIN, is_library_domain
from app.models.record import Record
from app.models.source import Source
from app.schemas import MediaItemList, MediaItemOut
from app.services.discovery_config import MEDIA_PAGE_SIZE_CEILING
from app.services.library_assets import resolve_record_file

router = APIRouter()


def _record_to_library_item(r: Record) -> MediaItemOut:
    fields = r.fields or {}
    inventory_status = fields.get("inventory_status") or "present"
    modified_raw = fields.get("modified_at")
    modified_at: datetime | None = None
    if isinstance(modified_raw, str):
        try:
            modified_at = datetime.fromisoformat(modified_raw)
        except ValueError:
            modified_at = None
    elif isinstance(modified_raw, datetime):
        modified_at = modified_raw

    display_status = "completed" if inventory_status == "present" else "failed"
    media_type = fields.get("media_type") or fields.get("stream_type") or "other"

    return MediaItemOut(
        id=r.id,
        source_id=r.source_id,
        platform="local",
        external_id=fields.get("relative_path"),
        canonical_url=r.canonical_url,
        title=r.title or fields.get("title"),
        description=fields.get("relative_path"),
        content_type=media_type,
        stream_type=media_type,
        thumbnail_url=None,
        channel_name=None,
        duration_seconds=None,
        file_size_bytes=fields.get("size_bytes") or fields.get("file_size_bytes"),
        view_count=None,
        download_status="completed" if inventory_status == "present" else "failed",
        transcription_status="pending",
        transcript=None,
        summary=None,
        published_at=modified_at or r.captured_at,
        discovered_at=r.created_at,
        processed_at=r.updated_at,
        status=display_status,
        error_message=r.error_message if inventory_status != "present" else None,
    )


@router.get("", response_model=MediaItemList)
async def list_library_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=MEDIA_PAGE_SIZE_CEILING),
    source_id: uuid.UUID | None = None,
    media_type: str | None = Query(None, alias="stream_type"),
    domain: str = Query(LIBRARY_DOMAIN),
    db: AsyncSession = Depends(get_db),
):
    if not is_library_domain(domain):
        raise HTTPException(status_code=400, detail="domain must be library")

    # Library inventories can be large — allow full page up to ceiling (not media UI cap).
    page_size = min(page_size, MEDIA_PAGE_SIZE_CEILING)

    rel_path_field = Record.fields["relative_path"].as_string()
    q = select(Record).where(Record.domain == LIBRARY_DOMAIN)
    q = q.where(
        func.coalesce(Record.fields["inventory_status"].as_string(), "present") == "present"
    )
    # Top-level entries only — hide legacy nested rows until re-scan marks them missing.
    q = q.where(not_(rel_path_field.like("%/%")))
    if source_id:
        q = q.where(Record.source_id == source_id)
    if media_type:
        q = q.where(Record.fields["media_type"].as_string() == media_type)

    count_q = select(func.count()).select_from(Record).where(Record.domain == LIBRARY_DOMAIN)
    count_q = count_q.where(
        func.coalesce(Record.fields["inventory_status"].as_string(), "present") == "present"
    )
    count_q = count_q.where(not_(rel_path_field.like("%/%")))
    if source_id:
        count_q = count_q.where(Record.source_id == source_id)
    if media_type:
        count_q = count_q.where(Record.fields["media_type"].as_string() == media_type)
    total = await db.scalar(count_q)

    rel_path = Record.fields["relative_path"].as_string()
    rows = (
        await db.scalars(
            q.order_by(rel_path.asc().nulls_last())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    items = [_record_to_library_item(r) for r in rows]
    return MediaItemList(items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/assets/{item_id}")
async def stream_library_asset(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = await db.get(Record, item_id)
    if not record or not is_library_domain(record.domain):
        raise HTTPException(status_code=404, detail="Library item not found")
    if not record.source_id:
        raise HTTPException(status_code=404, detail="Item has no source")
    source = await db.get(Source, record.source_id)
    if not source or not is_library_domain(source.domain):
        raise HTTPException(status_code=404, detail="Source not found")

    path = resolve_record_file(record, source)
    if not path:
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    safe_name = path.name.replace('"', "")
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.get("/{item_id}", response_model=MediaItemOut)
async def get_library_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = await db.get(Record, item_id)
    if not record or not is_library_domain(record.domain):
        raise HTTPException(status_code=404, detail="Library item not found")
    return _record_to_library_item(record)
