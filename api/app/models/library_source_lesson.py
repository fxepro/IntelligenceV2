"""Per-lesson detail rows for library course sources (1:N with sources)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LibrarySourceLesson(Base):
    """
    Detail table for Courses — one row per discovered lesson/page/video.

    Thin `sources` row holds curriculum URL + connector; this table holds each
    child item (title, section, external URL, content status, disk body path).
    Full text lives under v2/data/{destination-id}/pages/*.md (body_file).
    """

    __tablename__ = "library_source_lessons"
    __table_args__ = (
        UniqueConstraint("source_id", "lesson_key", name="uq_library_source_lessons_source_lesson"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_key: Mapped[str] = mapped_column(String(160), nullable=False)
    sort_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    category: Mapped[str] = mapped_column(String(256), nullable=False, default="General")
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="text")
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    content_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="index"
    )  # index | stub | ready | locked | skipped
    body_file: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    chars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
