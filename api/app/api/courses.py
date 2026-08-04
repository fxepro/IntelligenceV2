"""Courses API — file-backed lesson catalog under v2/data/."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain_keys import COURSES_DOMAIN, is_courses_domain
from app.models.job import JobType
from app.schemas import JobOut
from app.services.jobs import enqueue_job
from app.services.library_catalog import (
    CourseSummary,
    LessonDetail,
    LessonSummary,
    create_lesson,
    get_lesson,
    list_courses,
    list_lessons,
    update_lesson,
)
from app.services.library_export_docx import build_course_docx
from app.services.library_media import resolve_library_file
from app.services.library_publish import (
    update_course_publish_settings,
    update_lesson_publish_settings,
)
from app.services.library_sources import ensure_library_sources

router = APIRouter()


class LessonListOut(BaseModel):
    items: list[LessonSummary]
    total: int
    kinds: dict[str, int]
    categories: list[str]


class CourseListOut(BaseModel):
    items: list[CourseSummary]
    total: int


class CoursePublishUpdate(BaseModel):
    published: bool


class LessonPublishUpdate(BaseModel):
    published: bool


class LessonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    category: str | None = Field(default="Overview", max_length=256)
    kind: str | None = Field(default="text", max_length=32)
    body: str | None = Field(default="", max_length=2_000_000)
    place: str | None = Field(
        default="end",
        description="start = top of course (e.g. TOC); end = after scraped lessons",
    )


class LessonBodyUpdate(BaseModel):
    body: str = Field(..., max_length=2_000_000)
    course: str | None = Field(default=None, max_length=512)
    title: str | None = Field(default=None, max_length=512)


class ManualYoutubeImport(BaseModel):
    """Paste YouTube links — one per line, or Section | Title | URL."""

    text: str = Field(..., min_length=1, max_length=500_000)
    default_category: str = Field(default="General", max_length=128)


class ManualImportOut(BaseModel):
    course_id: str
    data_dir: str
    imported: int
    skipped: int
    message: str | None = None


REFRESHABLE = {
    "soc-2-compliance": "Scytale SOC 2 Academy (authenticated scrape)",
    "drata-soc-2": "Drata SOC 2 Learn (public scrape)",
}


@router.get("/courses", response_model=CourseListOut)
async def courses_list():
    items = list_courses()
    return CourseListOut(items=items, total=len(items))


@router.post("/sources/ensure")
async def courses_ensure_sources(db: AsyncSession = Depends(get_db)):
    """
    Sync file-backed courses into domain=courses sources (one source per course).
    Idempotent — safe to call when opening Courses → Sources.
    """
    rows = await ensure_library_sources(db)
    await db.commit()
    return {"ok": True, "total": len(rows)}


@router.get("/sources/{source_id}/lessons", response_model=LessonListOut)
async def courses_source_lessons(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Lesson detail rows for this source (library_source_lessons + v2/data bodies)."""
    from sqlalchemy import select

    from app.models.library_source_lesson import LibrarySourceLesson
    from app.models.source import Source
    from app.services.library_course_paths import course_id_from_tags
    from app.services.library_source_lessons import sync_lessons_from_disk

    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if not is_courses_domain(source.domain):
        raise HTTPException(status_code=400, detail="Not a courses source")

    course_id = course_id_from_tags(source.tags)
    if not course_id:
        return LessonListOut(items=[], total=0, kinds={}, categories=[])

    rows = (
        await db.scalars(
            select(LibrarySourceLesson)
            .where(LibrarySourceLesson.source_id == source_id)
            .order_by(LibrarySourceLesson.sort_index.asc())
        )
    ).all()

    if not rows:
        synced = await db.run_sync(
            lambda sync_session: sync_lessons_from_disk(
                sync_session, source_id=source_id, course_id=course_id
            )
        )
        if synced:
            await db.commit()
            rows = (
                await db.scalars(
                    select(LibrarySourceLesson)
                    .where(LibrarySourceLesson.source_id == source_id)
                    .order_by(LibrarySourceLesson.sort_index.asc())
                )
            ).all()

    if not rows:
        catalog_items, kinds, categories = list_lessons(course=course_id)
        if catalog_items:
            return LessonListOut(
                items=catalog_items,
                total=len(catalog_items),
                kinds=kinds,
                categories=categories,
            )

    kinds: dict[str, int] = {}
    categories: set[str] = set()
    items: list[LessonSummary] = []
    for row in rows:
        kinds[row.kind] = kinds.get(row.kind, 0) + 1
        categories.add(row.category)
        items.append(
            LessonSummary(
                id=row.lesson_key,
                title=row.title,
                course_id=course_id,
                course=source.name or course_id,
                category=row.category,
                kind=row.kind,
                label=row.title,
                source_url=row.source_url,
                chars=row.chars,
                has_text=row.content_status in ("ready", "stub", "index") and row.chars > 0,
                has_video=row.kind == "video",
                has_pdf=row.kind == "pdf",
                content_status=row.content_status,
                published=row.published,
            )
        )

    return LessonListOut(
        items=items,
        total=len(items),
        kinds=kinds,
        categories=sorted(categories),
    )


@router.post("/sources/{source_id}/acquire", response_model=JobOut)
async def courses_source_acquire(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 for article_hub sources: fetch full article bodies into v2/data/{destination-id}/.

    Step 1 is Discover (index: titles + URLs). This enqueues an acquire job — not a second discover.
    """
    from app.models.source import Source, SourceStatus
    from app.services.library_course_paths import course_id_from_tags, normalize_connector

    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status != SourceStatus.active:
        raise HTTPException(
            status_code=409,
            detail="Source is off — turn it on before fetching bodies",
        )
    if not is_courses_domain(source.domain):
        raise HTTPException(status_code=400, detail="Not a courses source")

    course_id = course_id_from_tags(source.tags)
    if not course_id:
        raise HTTPException(status_code=400, detail="Source missing Destination ID (course_id tag)")

    connector = normalize_connector(source.connector or "manual")
    if connector != "article_hub":
        raise HTTPException(
            status_code=400,
            detail=f"Acquire bodies is for Article hub sources only (connector={connector!r})",
        )

    try:
        job = await enqueue_job(
            db,
            job_type=JobType.acquire,
            domain=COURSES_DOMAIN,
            source_id=source.id,
            payload={
                "action": "library_acquire_articles",
                "source_id": str(source.id),
                "course_id": course_id,
            },
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return job


@router.post("/sources/{source_id}/lessons/manual-import", response_model=ManualImportOut)
async def courses_manual_import_youtube(
    source_id: uuid.UUID,
    payload: ManualYoutubeImport,
    db: AsyncSession = Depends(get_db),
):
    """
    Append YouTube lessons by hand into the course destination folder (v2/data/{course_id}/).
    Does not require Discover. Lines marked manual: true are preserved on re-import/discover.
    """
    from app.models.source import Source
    from app.services.library_course_paths import course_id_from_tags, import_manual_youtube_lessons

    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if not is_courses_domain(source.domain):
        raise HTTPException(status_code=400, detail="Manual import is for courses sources only")

    course_id = course_id_from_tags(source.tags)
    if not course_id:
        raise HTTPException(
            status_code=400,
            detail="Source has no course_id tag — set Destination ID on the source first",
        )

    course_name = (source.name or course_id).strip()
    try:
        result = import_manual_youtube_lessons(
            course_id=course_id,
            course_name=course_name,
            text=payload.text,
            default_category=payload.default_category or "General",
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write lessons: {exc}") from exc

    return ManualImportOut(
        course_id=result["course_id"],
        data_dir=result["data_dir"],
        imported=int(result.get("imported") or 0),
        skipped=int(result.get("skipped") or 0),
        message=result.get("message"),
    )


@router.get("/files/{file_path:path}")
async def courses_file(file_path: str):
    """Serve scraped lesson assets (images) under v2/data/."""
    path = resolve_library_file(file_path)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@router.post("/courses/{course_id}/lessons", response_model=LessonDetail)
async def courses_create_lesson(course_id: str, payload: LessonCreate):
    """Manually add a lesson to a course (TOC, notes, etc.)."""
    courses = {c.id.lower(): c for c in list_courses()}
    row = courses.get((course_id or "").strip().lower())
    cid = row.id if row else (course_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="course_id is required")
    try:
        return create_lesson(
            cid,
            title=payload.title,
            category=payload.category or "Overview",
            kind=payload.kind or "text",
            body=payload.body or "",
            place=payload.place or "end",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write lesson: {exc}") from exc


@router.patch("/courses/{course_id}/publish", response_model=CourseSummary)
async def courses_update_course_publish(course_id: str, payload: CoursePublishUpdate):
    """Toggle whether a course is live for DOCX export."""
    courses = {c.id.lower(): c for c in list_courses()}
    row = courses.get((course_id or "").strip().lower())
    if not row:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")
    try:
        update_course_publish_settings(row.id, published=payload.published)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    refreshed = {c.id.lower(): c for c in list_courses()}
    out = refreshed.get(row.id.lower())
    if not out:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")
    return out


@router.get("/courses/{course_id}/export.docx")
async def courses_export_course_docx(course_id: str):
    """Export all published lessons for a course to a formatted DOCX."""
    courses = {c.id.lower(): c for c in list_courses()}
    row = courses.get((course_id or "").strip().lower())
    if not row:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")
    if not row.published:
        raise HTTPException(
            status_code=400,
            detail="Course is unpublished. Turn Publish on to export.",
        )
    try:
        data, filename = build_course_docx(row.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/courses/{course_id}/refresh", response_model=JobOut)
async def courses_refresh_course(course_id: str, db: AsyncSession = Depends(get_db)):
    """Enqueue a Celery acquire job to re-download a refreshable course."""
    key = (course_id or "").strip().lower()
    if key not in REFRESHABLE:
        raise HTTPException(
            status_code=400,
            detail=f"Course {course_id!r} is not refreshable. Supported: {', '.join(sorted(REFRESHABLE))}",
        )
    try:
        job = await enqueue_job(
            db,
            job_type=JobType.acquire,
            domain=COURSES_DOMAIN,
            payload={"action": "library_refresh", "course_id": key},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return job


@router.get("/lessons", response_model=LessonListOut)
async def courses_lessons(
    course: str | None = Query(None, description="Course id or name"),
    kind: str | None = Query(None, description="text | video | pdf | quiz"),
    category: str | None = None,
    q: str | None = None,
):
    items, kinds, categories = list_lessons(
        course=course, kind=kind, category=category, q=q
    )
    return LessonListOut(items=items, total=len(items), kinds=kinds, categories=categories)


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def courses_lesson(lesson_id: str):
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.patch("/lessons/{lesson_id}/publish", response_model=LessonSummary)
async def courses_update_lesson_publish(lesson_id: str, payload: LessonPublishUpdate):
    """Turn an individual lesson On/Off for reading, nav, and DOCX export."""
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    try:
        update_lesson_publish_settings(lesson.id, published=payload.published)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    refreshed = get_lesson(lesson_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonSummary(
        id=refreshed.id,
        title=refreshed.title,
        course_id=refreshed.course_id,
        course=refreshed.course,
        category=refreshed.category,
        kind=refreshed.kind,
        label=refreshed.label,
        source_url=refreshed.source_url,
        chars=refreshed.chars,
        has_text=refreshed.has_text,
        has_video=refreshed.has_video,
        has_pdf=refreshed.has_pdf,
        content_status=refreshed.content_status,
        published=refreshed.published,
    )


@router.patch("/lessons/{lesson_id}", response_model=LessonDetail)
async def courses_update_lesson(lesson_id: str, payload: LessonBodyUpdate):
    """Update lesson body / title / course name on disk."""
    try:
        return update_lesson(
            lesson_id,
            body=payload.body,
            course=payload.course,
            title=payload.title,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write lesson: {exc}") from exc


@router.get("/available-sources")
async def courses_available_sources():
    """List available course sources that can be added."""
    from app.services.course_sources import get_available_course_sources

    sources = get_available_course_sources()
    return {"items": sources}


@router.post("/sources/add-course/{source_id}", response_model=JobOut)
async def courses_add_course_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Add and discover a preset course source (e.g. StrongDM SOC2)."""
    from app.services.course_sources import ensure_course_source

    try:
        source = await ensure_course_source(db, source_id)
        await db.commit()

        job = await enqueue_job(
            db,
            job_type=JobType.discover,
            domain=COURSES_DOMAIN,
            source_id=source.id,
            payload={"source_id": str(source.id)},
        )
        return job
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
