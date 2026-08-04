"""Legacy entrypoint — delegates to page-type article_hub parser."""
from __future__ import annotations

from app.services.course_parsers.registry import discover_curriculum
from app.services.course_parsers.types import CourseLesson

DEFAULT_URL = "https://drata.com/learn/soc-2"


def fetch_and_parse_drata(url: str | None = None) -> list[CourseLesson]:
    target = (url or DEFAULT_URL).strip()
    result = discover_curriculum(target, "article_hub", id_prefix="article-hub")
    if not result.lessons:
        msg = ", ".join(result.anomalies) or "COURSE_NO_LESSONS"
        raise RuntimeError(f"Article hub parse failed: {msg}")
    return result.lessons
