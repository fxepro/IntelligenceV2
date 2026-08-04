"""Legacy entrypoint — delegates to page-type youtube_curriculum parser."""
from __future__ import annotations

from app.services.course_parsers.registry import discover_curriculum
from app.services.course_parsers.types import CourseLesson

DEFAULT_URL = "https://www.strongdm.com/soc2/course/curriculum"


def fetch_and_parse_strongdm(url: str | None = None) -> list[CourseLesson]:
    target = (url or DEFAULT_URL).strip()
    result = discover_curriculum(target, "youtube_curriculum", id_prefix="yt-curriculum")
    if not result.lessons:
        msg = ", ".join(result.anomalies) or "COURSE_NO_LESSONS"
        raise RuntimeError(f"Video curriculum parse failed: {msg}")
    return result.lessons
