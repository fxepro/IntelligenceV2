"""Canonical domain string keys for the v2 control plane."""

# Online curricula: YouTube, article hubs, LMS discover/acquire.
COURSES_DOMAIN = "courses"

# Personal local folders: videos, PDFs, ebooks on disk.
LIBRARY_DOMAIN = "library"


def course_source_url(course_id: str) -> str:
    cid = (course_id or "").strip()
    return f"mi://courses/{cid}"


def is_courses_domain(domain: str | None) -> bool:
    return (domain or "").strip().lower() == COURSES_DOMAIN


def is_library_domain(domain: str | None) -> bool:
    return (domain or "").strip().lower() == LIBRARY_DOMAIN
