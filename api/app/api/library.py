"""Library / Lessons API — file-backed catalog under data/ (+ optional Docling parse)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.library_catalog import (
    DATA_ROOT,
    CourseSummary,
    LessonDetail,
    LessonSummary,
    get_lesson,
    list_courses,
    list_lessons,
    parse_document_to_lesson,
)

router = APIRouter()


class LessonListOut(BaseModel):
    items: list[LessonSummary]
    total: int
    kinds: dict[str, int]
    categories: list[str]


class CourseListOut(BaseModel):
    items: list[CourseSummary]
    total: int


class ParseDocumentRequest(BaseModel):
    """Parse a local PDF/DOCX/TXT under data/ into a Library lesson (Docling)."""

    path: str = Field(..., min_length=1, max_length=1024)
    title: str | None = Field(default=None, max_length=512)
    category: str | None = Field(default=None, max_length=128)


@router.get("/courses", response_model=CourseListOut)
async def library_courses():
    items = list_courses()
    return CourseListOut(items=items, total=len(items))


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
