"""Ensure library course sources have destination ID + connector before discover."""
from __future__ import annotations

from sqlalchemy.orm.attributes import flag_modified

from app.models.source import Source
from app.services.library_course_paths import (
    course_id_from_tags,
    course_id_tag,
    ensure_course_data_dir,
    infer_connector,
    normalize_connector,
    slugify_course_id,
)


def curriculum_url_for_source(source: Source) -> str:
    url = (source.source_url or "").strip()
    vanity = (source.vanity_url or "").strip()
    if url.startswith("mi://") and vanity.startswith("http"):
        return vanity.rstrip("/")
    return url.rstrip("/")


def ensure_library_course_ready(source: Source) -> tuple[str, str, str]:
    """
    Backfill missing course_id tag and infer connector from URL when possible.
    Mutates source in-place; caller should commit the session.
    Returns (course_id, connector, curriculum_url).
    """
    course_id = course_id_from_tags(source.tags)
    if not course_id:
        course_id = slugify_course_id(source.name or "")
        if not course_id or course_id == "course":
            raise ValueError(
                "Course name is required — destination folder is derived from the name automatically."
            )
        tags = [t for t in (source.tags or []) if not str(t).lower().startswith("course_id:")]
        tags.insert(0, course_id_tag(course_id))
        source.tags = tags
        flag_modified(source, "tags")
        ensure_course_data_dir(course_id)

    curriculum_url = curriculum_url_for_source(source)
    connector = normalize_connector(source.connector or "")
    if not source.connector or connector in ("manual", ""):
        if curriculum_url.startswith("http"):
            connector = normalize_connector(infer_connector(curriculum_url))
            source.connector = connector
        elif not source.connector:
            source.connector = "manual"

    return course_id, normalize_connector(source.connector or connector), curriculum_url


def repair_library_sources(sources: list[Source]) -> int:
    """Fix courses rows missing course_id tag or connector. Returns count repaired."""
    from app.domain_keys import is_courses_domain

    repaired = 0
    for source in sources:
        if not is_courses_domain(source.domain):
            continue
        from app.services.library_course_paths import course_id_from_tags

        needs = not course_id_from_tags(source.tags) or not source.connector
        if not needs:
            continue
        try:
            ensure_library_course_ready(source)
            repaired += 1
        except ValueError:
            continue
    return repaired
