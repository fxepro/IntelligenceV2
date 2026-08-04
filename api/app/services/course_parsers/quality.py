"""Quality scoring for course manifest extraction."""
from __future__ import annotations

from app.services.course_parsers.types import CourseLesson


def score_youtube_curriculum(lessons: list[CourseLesson]) -> tuple[int, list[str]]:
    anomalies: list[str] = []
    score = 0
    if not lessons:
        anomalies.append("COURSE_NO_LESSONS")
        return 0, anomalies

    score += 15  # lessons exist
    with_url = [l for l in lessons if l.video_url or l.url]
    if with_url:
        score += 20
    else:
        anomalies.append("COURSE_LESSON_URL_MISSING")

    sections = {l.category for l in lessons if l.category}
    if sections:
        score += 15
    else:
        anomalies.append("COURSE_NO_SECTIONS")

    with_duration = [l for l in lessons if l.duration_seconds]
    if with_duration:
        score += 5

    if len(lessons) >= 3:
        score += 15
    ordered = sorted(l.order_index for l in lessons)
    if ordered == list(range(1, len(lessons) + 1)) or ordered == sorted(set(ordered)):
        score += 10

    titles = [l.title.strip().lower() for l in lessons if l.title]
    if len(titles) == len(set(titles)):
        score += 5

    score = min(100, score)
    if score < 50:
        anomalies.append("QUALITY_BELOW_THRESHOLD")
    return score, anomalies


def score_article_hub(lessons: list[CourseLesson]) -> tuple[int, list[str]]:
    anomalies: list[str] = []
    if not lessons:
        return 0, ["COURSE_NO_LESSONS"]

    score = 20
    with_url = [l for l in lessons if l.url]
    score += 25 if with_url else 0
    if not with_url:
        anomalies.append("COURSE_LESSON_URL_MISSING")
    if len(lessons) >= 5:
        score += 20
    sections = {l.category for l in lessons if l.category}
    if sections:
        score += 15
    score = min(100, score)
    if score < 50:
        anomalies.append("QUALITY_BELOW_THRESHOLD")
    return score, anomalies
