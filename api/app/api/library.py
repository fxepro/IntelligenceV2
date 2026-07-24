"""Library / Lessons API — file-backed catalog under data/ (+ optional Docling parse)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobType
from app.schemas import JobOut
from app.services.jobs import enqueue_job
from app.services.library_catalog import (
    DATA_ROOT,
    CourseSummary,
    LessonDetail,
    LessonSummary,
    create_lesson,
    get_lesson,
    list_courses,
    list_lessons,
    parse_document_to_lesson,
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


class ParseDocumentRequest(BaseModel):
    """Parse a local PDF/DOCX/TXT under data/ into a Library lesson (Docling)."""

    path: str = Field(..., min_length=1, max_length=1024)
    title: str | None = Field(default=None, max_length=512)
    category: str | None = Field(default=None, max_length=128)


class LessonBodyUpdate(BaseModel):
    body: str = Field(..., max_length=2_000_000)
    course: str | None = Field(default=None, max_length=512)
    title: str | None = Field(default=None, max_length=512)


REFRESHABLE = {
    "soc-2-compliance": "Scytale SOC 2 Academy (authenticated scrape)",
    "drata-soc-2": "Drata SOC 2 Learn (public scrape)",
}


@router.get("/courses", response_model=CourseListOut)
async def library_courses():
    items = list_courses()
    return CourseListOut(items=items, total=len(items))


@router.post("/sources/ensure")
async def library_ensure_sources(db: AsyncSession = Depends(get_db)):
    """
    Sync file-backed courses into domain=library sources (one source per course).
    Idempotent — safe to call when opening Courses → Sources.
    """
    rows = await ensure_library_sources(db)
    await db.commit()
    return {"ok": True, "total": len(rows)}


@router.get("/files/{file_path:path}")
async def library_file(file_path: str):
    """Serve scraped lesson assets (images) under v2/data/."""
    path = resolve_library_file(file_path)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@router.post("/courses/{course_id}/lessons", response_model=LessonDetail)
async def library_create_lesson(course_id: str, payload: LessonCreate):
    """
    Manually add a lesson to any Library course (TOC, notes, etc.).
    Survives Refresh — stored under data/library/manual/.
    """
    courses = {c.id.lower(): c for c in list_courses()}
    # Allow creating into a known course, or first-time course id
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
async def library_update_course_publish(course_id: str, payload: CoursePublishUpdate):
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
async def library_export_course_docx(course_id: str):
    """
    Export all published lessons for a course to a formatted DOCX.
    Per-lesson Publish Off rows (e.g. videos) are skipped.
    """
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
async def library_refresh_course(course_id: str, db: AsyncSession = Depends(get_db)):
    """
    Enqueue a Celery acquire job to re-download a Library course.
    Use after gating quizzes unlock later modules (e.g. Scytale SOC 2).
    """
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
            domain="library",
            payload={"action": "library_refresh", "course_id": key},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return job


@router.get("/lessons", response_model=LessonListOut)
async def library_lessons(
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
async def library_lesson(lesson_id: str):
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.patch("/lessons/{lesson_id}/publish", response_model=LessonSummary)
async def library_update_lesson_publish(lesson_id: str, payload: LessonPublishUpdate):
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
async def library_update_lesson(lesson_id: str, payload: LessonBodyUpdate):
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


@router.post("/parse-document", response_model=LessonDetail)
async def library_parse_document(payload: ParseDocumentRequest):
    """
    Parse a book/material file with Docling into a text lesson under data/library/parsed/.
    Long Docling runs belong in workers later — this is a control-plane convenience for local files.
    """
    raw = Path(payload.path)
    path = raw if raw.is_absolute() else (DATA_ROOT / raw).resolve()
    try:
        path.relative_to(DATA_ROOT.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Path must be under v2/data/") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        return parse_document_to_lesson(
            path,
            title=payload.title,
            category=payload.category,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc
