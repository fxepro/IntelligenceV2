"""Manage course sources (courses domain)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain_keys import COURSES_DOMAIN
from app.models.source import Platform, Source, SourcePriority, SourceStatus, SourceType
from app.services.catalog_ids import allocate_catalog_id
from app.services.library_course_paths import course_id_tag, ensure_course_data_dir


DOMAIN = COURSES_DOMAIN

# Known course sources
COURSE_SOURCES = {
    "strongdm-soc2": {
        "name": "StrongDM SOC2 Curriculum",
        "url": "https://www.strongdm.com/soc2/course/curriculum",
        "description": "StrongDM's SOC2 compliance curriculum",
        "connector": "youtube_curriculum",
    },
    "drata-soc2": {
        "name": "Drata SOC 2 Learn",
        "url": "https://drata.com/learn/soc-2",
        "description": "Drata's SOC 2 compliance learning center (47 articles)",
        "connector": "article_hub",
    },
}


async def ensure_course_source(
    db: AsyncSession,
    source_id: str,
    name: str | None = None,
    url: str | None = None,
    description: str | None = None,
    connector: str | None = None,
) -> Source:
    """Create or update a course source."""
    if source_id not in COURSE_SOURCES and not url:
        raise ValueError(f"Unknown course source: {source_id}")

    preset = COURSE_SOURCES.get(source_id, {})
    name = name or preset.get("name", source_id)
    url = url or preset.get("url")
    description = description or preset.get("description")
    connector = connector or preset.get("connector", "unknown")

    if not url:
        raise ValueError(f"Course source {source_id} has no URL")

    source_url = url.rstrip("/")

    existing = await db.scalar(
        select(Source).where(
            Source.domain == DOMAIN,
            Source.source_url == source_url,
        )
    )

    if existing:
        existing.name = name
        existing.description = description
        existing.connector = connector
        existing.category = "course"
        existing.tags = [course_id_tag(source_id)]
        ensure_course_data_dir(source_id)
        return existing

    ensure_course_data_dir(source_id)
    catalog_id = await allocate_catalog_id(db, DOMAIN)
    source = Source(
        domain=DOMAIN,
        catalog_id=catalog_id,
        platform=Platform.website,
        source_type=SourceType.website,
        source_url=source_url,
        name=name,
        description=description,
        category="course",
        tags=[course_id_tag(source_id)],
        priority=SourcePriority.normal,
        autorun=False,
        auto_transcribe=False,
        status=SourceStatus.active,
        connector=connector,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


def get_available_course_sources() -> list[dict]:
    """Return list of available course sources to add."""
    return [
        {
            "id": source_id,
            "name": data["name"],
            "description": data.get("description"),
            "url": data["url"],
            "connector": data.get("connector"),
        }
        for source_id, data in COURSE_SOURCES.items()
    ]


async def discover_course_source(source_id: str, db: AsyncSession) -> str:
    from app.services.jobs import enqueue_job
    from app.models.job import JobType

    if source_id in COURSE_SOURCES:
        # We need the real DB ID
        source_url = COURSE_SOURCES[source_id]["url"]
        row = await db.scalar(select(Source).where(Source.domain == DOMAIN, Source.source_url == source_url))
        if not row:
            raise ValueError(f"Source not added yet: {source_id}")
        db_id = row.id
    else:
        # Treat source_id as the UUID
        db_id = source_id

    # Add the celery job
    job = await enqueue_job(db, JobType.discover, source_id=db_id, payload={"max_items": 100})
    await db.commit()
    return str(job.id)
