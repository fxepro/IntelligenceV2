"""Shared types for course curriculum discovery."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CourseLesson:
    id: str
    title: str
    category: str
    kind: str  # video | text | quiz
    has_video: bool
    video_url: str | None = None
    url: str | None = None
    description: str | None = None
    order_index: int = 0
    duration_seconds: int | None = None


@dataclass
class ParseAttempt:
    parser_key: str
    fetch_mode: str
    http_status: int | None = None
    error: str | None = None
    lessons_found: int = 0


@dataclass
class ParseResult:
    lessons: list[CourseLesson] = field(default_factory=list)
    parser_key: str = ""
    fetch_mode: str = ""
    quality_score: int = 0
    anomalies: list[str] = field(default_factory=list)
    attempts: list[ParseAttempt] = field(default_factory=list)
    course_title: str | None = None

    @property
    def ok(self) -> bool:
        return len(self.lessons) > 0 and self.quality_score >= 50
