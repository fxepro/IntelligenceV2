"""Course curriculum parsers — page-type based discovery."""
from app.services.course_parsers.registry import discover_curriculum, lessons_to_dicts
from app.services.course_parsers.types import CourseLesson, ParseResult

__all__ = ["CourseLesson", "ParseResult", "discover_curriculum", "lessons_to_dicts"]
