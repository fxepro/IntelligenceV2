"""
Research API — Layer 0.

Fan out across real platform providers (ported from v1) + catalog matches.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.source import Source, SourceType
from app.schemas import ResearchCandidateOut, ResearchRequest, ResearchResponse
from app.services.research import run_research

router = APIRouter()

_CANDIDATES: dict[str, ResearchCandidateOut] = {}

@router.post("", response_model=ResearchResponse)
async def research(payload: ResearchRequest, db: AsyncSession = Depends(get_db)):
    q = payload.query.strip()
    platforms = payload.platforms or None

    result = await run_research(q, platforms=platforms, max_per_platform=payload.max_per_platform or 10)

    # Catalog boosts
    all_sources = (await db.scalars(select(Source))).all()
    existing_by_url = {s.source_url.rstrip("/").lower(): s for s in all_sources}

    candidates: list[ResearchCandidateOut] = []
    for raw in result.candidates:
        cid = str(uuid.uuid4())
        key = (raw.url or "").rstrip("/").lower()
        in_catalog = key in existing_by_url
        cand = ResearchCandidateOut(
            id=cid,
            query=q,
            platform=raw.platform,
            external_id=raw.external_id,
            name=raw.name,
            url=raw.url,
            thumbnail_url=raw.thumbnail_url,
            description=raw.description,
            suggested_source_type=raw.suggested_source_type,
            subscriber_count=raw.subscriber_count,
            item_count=raw.item_count,
            total_views=raw.total_views,
            last_active_at=raw.last_active_at,
            relevance_score=raw.relevance_score,
            ai_reason=(
                "Already in your Sources catalog"
                if in_catalog
                else (raw.ai_reason or "Matched platform search")
            ),
            status="promoted" if in_catalog else "suggested",
            created_at=datetime.now(timezone.utc),
        )
        _CANDIDATES[cid] = cand
        candidates.append(cand)

    # Also surface catalog name matches even if providers miss them
    pattern = f"%{q}%"
    catalog_rows = (
        await db.scalars(
            select(Source)
            .where(or_(Source.name.ilike(pattern), Source.source_url.ilike(pattern)))
            .order_by(Source.updated_at.desc())
            .limit(10)
        )
    ).all()
    seen_urls = {(c.url or "").rstrip("/").lower() for c in candidates}
    for s in catalog_rows:
        key = s.source_url.rstrip("/").lower()
        if key in seen_urls:
            continue
        cid = str(uuid.uuid4())
        cand = ResearchCandidateOut(
            id=cid,
            query=q,
            platform=s.platform.value if hasattr(s.platform, "value") else str(s.platform),
            name=s.name,
            url=s.source_url,
            description=s.description,
            suggested_source_type=s.source_type.value
            if hasattr(s.source_type, "value")
            else str(s.source_type),
            relevance_score=95.0,
            ai_reason="Already in your Sources catalog",
            status="promoted",
            created_at=datetime.now(timezone.utc),
        )
        _CANDIDATES[cid] = cand
        candidates.append(cand)

    notices = list(result.notices or [])
    notices.append("research: external providers + catalog match")
    return ResearchResponse(
        query=q,
        total=len(candidates),
        candidates=candidates,
        notices=notices,
    )


@router.post("/candidates/{candidate_id}/promote")
async def promote_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.source import Platform, SourceStatus

    cand = _CANDIDATES.get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    existing = await db.scalar(select(Source).where(Source.source_url == cand.url.rstrip("/")))
    if existing:
        cand.status = "promoted"
        return {"candidate_id": candidate_id, "source_id": str(existing.id), "created": False}

    try:
        platform = Platform(cand.platform)
    except ValueError:
        platform = Platform.website

    from app.models.source_stream import SourceStream
    from app.services.source_streams import default_streams_for_platform

    default_types = {
        Platform.facebook: SourceType.facebook_reels,
        Platform.youtube: SourceType.youtube_videos,
        Platform.instagram: SourceType.instagram_reels,
        Platform.tiktok: SourceType.tiktok_videos,
        Platform.x: SourceType.x_posts,
        Platform.podcast: SourceType.rss_feed,
        Platform.rss: SourceType.rss_feed,
        Platform.website: SourceType.sitemap,
    }
    source_type = default_types.get(platform, SourceType.profile)
    from app.services.catalog_ids import allocate_catalog_id

    source = Source(
        domain="media",
        catalog_id=await allocate_catalog_id(db, "media"),
        platform=platform,
        source_type=source_type,
        source_url=cand.url,
        name=cand.name,
        description=cand.description,
        status=SourceStatus.active,
    )
    db.add(source)
    await db.flush()
    for stream_type, enabled, stream_url in default_streams_for_platform(
        platform, source_type, source_url=cand.url
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
    cand.status = "promoted"
    return {"candidate_id": candidate_id, "source_id": str(source.id), "created": True}


@router.post("/candidates/{candidate_id}/dismiss")
async def dismiss_candidate(candidate_id: str):
    cand = _CANDIDATES.get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    cand.status = "dismissed"
    return {"candidate_id": candidate_id, "status": "dismissed"}
