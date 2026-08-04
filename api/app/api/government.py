"""Government domain — SAM.gov Contract Opportunities (GOV-0001)."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.government_detail import GovernmentDetail
from app.models.job import JobType
from app.models.source import Source, SourceStatus
from app.schemas import JobOut, MediaItemList, MediaItemOut
from app.services.discovery_config import MEDIA_PAGE_SIZE_CEILING
from app.services.jobs import enqueue_job
from app.services.sam_gov import GOV_CATALOG_OPPORTUNITIES, credentials_configured
from app.services.sam_gov_sync import CONNECTOR

router = APIRouter()


class OpportunitiesSyncRequest(BaseModel):
    posted_from: str | None = Field(None, description="MM/dd/yyyy")
    posted_to: str | None = Field(None, description="MM/dd/yyyy")
    limit: int = Field(100, ge=1, le=1000)
    max_pages: int = Field(1, ge=1, le=10)


def _detail_to_opportunity(row: GovernmentDetail) -> MediaItemOut:
    return MediaItemOut(
        id=row.id,
        source_id=row.source_id,
        platform="government",
        external_id=row.notice_id,
        canonical_url=row.canonical_url,
        title=row.title,
        description=row.organization,
        content_type=row.notice_type,
        stream_type="contract_opportunity",
        published_at=row.posted_at,
        discovered_at=row.created_at,
        processed_at=row.updated_at,
        status="completed",
        error_message=row.error_message,
    )


@router.get("/opportunities", response_model=MediaItemList)
async def list_opportunities(
    source_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=MEDIA_PAGE_SIZE_CEILING),
    db: AsyncSession = Depends(get_db),
):
    page_size = min(page_size, MEDIA_PAGE_SIZE_CEILING)
    q = select(GovernmentDetail).where(GovernmentDetail.connector == CONNECTOR)
    count_q = select(func.count()).select_from(GovernmentDetail).where(
        GovernmentDetail.connector == CONNECTOR
    )
    if source_id:
        q = q.where(GovernmentDetail.source_id == source_id)
        count_q = count_q.where(GovernmentDetail.source_id == source_id)

    total = int(await db.scalar(count_q) or 0)
    rows = (
        await db.scalars(
            q.order_by(GovernmentDetail.posted_at.desc().nullslast(), GovernmentDetail.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return MediaItemList(
        items=[_detail_to_opportunity(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/sources/{source_id}/sync-opportunities", response_model=JobOut)
async def sync_opportunities(
    source_id: uuid.UUID,
    body: OpportunitiesSyncRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    if not credentials_configured():
        raise HTTPException(
            status_code=400,
            detail="SAM_GOV_API_KEY missing in v2/.env",
        )
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if (source.catalog_id or "").strip().upper() != GOV_CATALOG_OPPORTUNITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Sync only supported for catalog {GOV_CATALOG_OPPORTUNITIES}",
        )
    if source.status != SourceStatus.active:
        raise HTTPException(status_code=409, detail="Turn source on before syncing")

    req = body or OpportunitiesSyncRequest()
    try:
        job = await enqueue_job(
            db,
            job_type=JobType.acquire,
            domain="government",
            source_id=source.id,
            payload={
                "action": "sam_gov_opportunities_sync",
                "posted_from": req.posted_from,
                "posted_to": req.posted_to,
                "limit": req.limit,
                "max_pages": req.max_pages,
            },
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return job
