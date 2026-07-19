"""Discover compatibility routes for the Sources UI (v1 paths)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobType
from app.models.source import Source
from app.schemas import DiscoverSourceResponse
from app.services.discovery_config import get_discovery_settings
from app.services.jobs import enqueue_job

router = APIRouter()


@router.post("/source/{source_id}", response_model=DiscoverSourceResponse)
async def discover_source_compat(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    discovery = await get_discovery_settings(db)
    job = await enqueue_job(
        db,
        job_type=JobType.discover,
        domain=source.domain,
        source_id=source.id,
        payload={
            "max_items": discovery["max_items"],
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


@router.post("/all")
async def discover_all_compat(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    sources = (await db.scalars(select(Source).where(Source.domain == "media"))).all()
    discovery = await get_discovery_settings(db)
    results = []
    for source in sources:
        job = await enqueue_job(
            db,
            job_type=JobType.discover,
            domain=source.domain,
            source_id=source.id,
            payload={
                "max_items": discovery["max_items"],
                "source_url": source.source_url,
                "platform": source.platform.value,
            },
        )
        results.append(
            {
                "source_id": str(source.id),
                "job_id": str(job.id),
                "new": 0,
                "total_found": 0,
                "items": [],
                "error": None,
            }
        )
    return {
        "sources_checked": len(sources),
        "total_new": 0,
        "results": results,
    }
