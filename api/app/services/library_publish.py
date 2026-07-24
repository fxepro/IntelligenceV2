"""Library publish settings — per-course and per-lesson (file-backed)."""
from __future__ import annotations

import json
import threading
from pathlib import Path

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[3]  # v2/
SETTINGS_PATH = ROOT / "data" / "library" / "publish_settings.json"
_LOCK = threading.Lock()


class CoursePublishSettings(BaseModel):
    """Course-level: whether the course is live for export."""

    published: bool = True


class LessonPublishSettings(BaseModel):
    published: bool = True


class PublishSettingsFile(BaseModel):
    courses: dict[str, CoursePublishSettings] = Field(default_factory=dict)
    lessons: dict[str, LessonPublishSettings] = Field(default_factory=dict)


def _empty() -> PublishSettingsFile:
    return PublishSettingsFile()


def _read() -> PublishSettingsFile:
    if not SETTINGS_PATH.is_file():
        return _empty()
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()

    courses_raw = raw.get("courses") if isinstance(raw.get("courses"), dict) else {}
    # Legacy flat file had only course keys at top level
    if not courses_raw and "courses" not in raw and "lessons" not in raw:
        courses_raw = {
            k: v
            for k, v in raw.items()
            if isinstance(v, dict) and ("published" in v or "publish_videos" in v)
        }

    courses: dict[str, CoursePublishSettings] = {}
    for key, val in courses_raw.items():
        cid = str(key).strip().lower()
        if not cid or not isinstance(val, dict):
            continue
        courses[cid] = CoursePublishSettings(published=bool(val.get("published", True)))

    lessons_raw = raw.get("lessons") if isinstance(raw.get("lessons"), dict) else {}
    lessons: dict[str, LessonPublishSettings] = {}
    for key, val in lessons_raw.items():
        lid = str(key).strip()
        if not lid:
            continue
        if isinstance(val, dict):
            lessons[lid] = LessonPublishSettings(published=bool(val.get("published", True)))
        elif isinstance(val, bool):
            lessons[lid] = LessonPublishSettings(published=val)

    return PublishSettingsFile(courses=courses, lessons=lessons)


def _write(data: PublishSettingsFile) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "courses": {
            cid: s.model_dump() for cid, s in sorted(data.courses.items())
        },
        "lessons": {
            lid: s.model_dump() for lid, s in sorted(data.lessons.items())
        },
    }
    SETTINGS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_course_publish_settings(course_id: str) -> CoursePublishSettings:
    key = (course_id or "").strip().lower()
    with _LOCK:
        data = _read()
    return data.courses.get(key, CoursePublishSettings())


def update_course_publish_settings(
    course_id: str,
    *,
    published: bool | None = None,
) -> CoursePublishSettings:
    key = (course_id or "").strip().lower()
    if not key:
        raise ValueError("course_id is required")
    with _LOCK:
        data = _read()
        current = data.courses.get(key, CoursePublishSettings())
        if published is not None:
            current.published = bool(published)
        data.courses[key] = current
        _write(data)
        return current


def default_lesson_published(kind: str | None) -> bool:
    """Videos default off; text / quiz / pdf default on."""
    return (kind or "").lower() != "video"


def is_lesson_published(lesson_id: str, kind: str | None = None) -> bool:
    """Explicit per-lesson override, else kind default (videos off)."""
    key = (lesson_id or "").strip()
    with _LOCK:
        data = _read()
        if key in data.lessons:
            return bool(data.lessons[key].published)
    return default_lesson_published(kind)


def update_lesson_publish_settings(lesson_id: str, *, published: bool) -> LessonPublishSettings:
    key = (lesson_id or "").strip()
    if not key:
        raise ValueError("lesson_id is required")
    with _LOCK:
        data = _read()
        current = LessonPublishSettings(published=bool(published))
        data.lessons[key] = current
        _write(data)
        return current
