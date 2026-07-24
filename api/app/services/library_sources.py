"""Ensure Courses (library) domain sources mirror file-backed courses."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Platform, Source, SourcePriority, SourceStatus, SourceType
from app.services.catalog_ids import allocate_catalog_id
from app.services.library_catalog import list_courses
from app.services.source_streams import default_streams_for_platform
from app.models.source_stream import SourceStream

DOMAIN = "library"
COURSE_TAG_PREFIX = "course_id:"


def course_source_url(course_id: str) -> str:
    return f"mi://library/courses/{course_id}"


def course_id_from_tags(tags: list | None) -> str | None:
    for tag in tags or []:
        raw = str(tag or "").strip()
        if raw.lower().startswith(COURSE_TAG_PREFIX):
            cid = raw[len(COURSE_TAG_PREFIX) :].strip()
            if cid:
                return cid
    return None


async def ensure_library_sources(db: AsyncSession) -> list[Source]:
    """
    Upsert one source per file-backed course (name = course name).
    Idempotent by source_url mi://library/courses/{course_id}.
    """
    courses = list_courses()
    out: list[Source] = []

    for course in courses:
        cid = (course.id or "").strip()
        if not cid:
            continue
        url = course_source_url(cid)
        existing = await db.scalar(select(Source).where(Source.source_url == url))
        tags = [f"{COURSE_TAG_PREFIX}{cid}"]
        desc = f"{course.lesson_count} lesson{'s' if course.lesson_count != 1 else ''}"
        if course.unpublished_count:
            desc += f" · {course.unpublished_count} unpublished"

        if existing:
            existing.domain = DOMAIN
            existing.name = course.name or cid
            existing.description = desc
            existing.category = "Course"
            existing.tags = tags
            existing.platform = Platform.website
            existing.source_type = SourceType.website
            if not existing.catalog_id:
                existing.catalog_id = await allocate_catalog_id(db, DOMAIN)
            out.append(existing)
            continue

        catalog_id = await allocate_catalog_id(db, DOMAIN)
        source = Source(
            domain=DOMAIN,
            catalog_id=catalog_id,
            platform=Platform.website,
            source_type=SourceType.website,
            source_url=url,
            name=course.name or cid,
            description=desc,
            category="Course",
            tags=tags,
            priority=SourcePriority.normal,
            autorun=False,
            auto_transcribe=False,
            status=SourceStatus.active,
        )
        db.add(source)
        await db.flush()
        for stream_type, enabled, stream_url in default_streams_for_platform(
            Platform.website,
            SourceType.website,
            source_url=url,
            stream_urls={},
        ):
            db.add(
                SourceStream(
                    source_id=source.id,
                    stream_type=stream_type,
                    stream_url=stream_url,
                    enabled=enabled,
                )
            )
        out.append(source)

    await db.flush()
    for source in out:
        await db.refresh(source)
    return out
