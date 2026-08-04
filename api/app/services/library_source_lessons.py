"""DB detail rows for library course lessons + sync from v2/data/."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.library_source_lesson import LibrarySourceLesson
from app.services.library_course_paths import ROOT, resolved_course_data_dir
from app.services.library_lesson_metadata import normalize_lesson_title_category


def _normalize_kind(raw: str) -> str:
    kind = (raw or "text").lower()
    if kind == "lesson":
        return "video"
    return kind


def _lesson_key_from_row(row: dict) -> str:
    if row.get("lesson_id"):
        return str(row["lesson_id"])
    if row.get("id"):
        return str(row["id"])
    index = int(row.get("index") or 0)
    file_rel = str(row.get("file") or "").replace("\\", "/")
    if "scytale-soc2" in file_rel:
        stem = Path(file_rel).stem if file_rel else f"lesson-{index}"
        return f"scy-{index:03d}-{stem[:40]}"
    if "drata-soc2" in file_rel and not file_rel.startswith("data/drata-soc-2-learn"):
        stem = Path(file_rel).stem if file_rel else f"lesson-{index}"
        return f"dra-{index:03d}-{stem[:40]}"
    return f"lesson-{index}"


def _infer_content_status(*, chars: int, body_preview: str, kind: str) -> str:
    low = (body_preview or "").lower()
    if kind == "video":
        return "skipped"
    if "content not fetched yet" in low or low.startswith("article:"):
        return "stub" if chars < 400 else "index"
    if chars > 400:
        return "ready"
    return "stub"


def _read_body_preview(body_file: str | None) -> tuple[int, str]:
    if not body_file:
        return 0, ""
    path = ROOT / body_file.replace("\\", "/")
    if not path.is_file():
        return 0, ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if "---" in text:
        text = text.split("---", 1)[-1].strip()
    return len(text), text[:500]


def sync_lessons_from_disk(
    session: Session,
    *,
    source_id: uuid.UUID,
    course_id: str,
) -> int:
    """Upsert library_source_lessons from manifest.json on disk."""
    manifest_path = resolved_course_data_dir(course_id) / "manifest.json"
    if not manifest_path.is_file():
        return 0

    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        return 0

    existing = {
        r.lesson_key: r
        for r in session.scalars(
            select(LibrarySourceLesson).where(LibrarySourceLesson.source_id == source_id)
        ).all()
    }

    written = 0
    for row in rows:
        if not row.get("ok"):
            continue
        lesson_key = _lesson_key_from_row(row)
        file_rel = str(row.get("file") or "").replace("\\", "/")
        kind = _normalize_kind(str(row.get("kind") or "text"))
        chars = int(row.get("chars") or 0)
        body_chars, preview = _read_body_preview(file_rel or None)
        if body_chars > chars:
            chars = body_chars
        manual = False
        is_manual_import = False
        if file_rel:
            path = ROOT / file_rel
            if path.is_file():
                raw = path.read_text(encoding="utf-8", errors="replace")
                if "- manual: true" in raw.lower():
                    manual = True
                    is_manual_import = True

        content_status = _infer_content_status(chars=chars, body_preview=preview, kind=kind)
        if is_manual_import and chars > 0 and kind != "video":
            content_status = "ready"
        elif manual:
            content_status = "ready"
        meta = _read_frontmatter_fields(file_rel or None)
        title, category = normalize_lesson_title_category(row=row, meta=meta, file_rel=file_rel)

        payload = {
            "sort_index": int(row.get("index") or 0),
            "title": title,
            "category": category,
            "kind": kind[:32],
            "source_url": (row.get("url") or None),
            "content_status": content_status,
            "body_file": file_rel or None,
            "chars": chars,
            "manual": manual,
        }

        current = existing.get(lesson_key)
        if current:
            if current.manual and not manual:
                continue
            for key, val in payload.items():
                setattr(current, key, val)
        else:
            session.add(
                LibrarySourceLesson(
                    source_id=source_id,
                    lesson_key=lesson_key[:160],
                    **payload,
                )
            )
        written += 1

    session.flush()
    return written


def _read_frontmatter_fields(body_file: str | None) -> dict[str, str]:
    if not body_file:
        return {}
    path = ROOT / body_file.replace("\\", "/")
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("#") and not text.startswith("-"):
        return {}
    block = text.split("---", 1)[0]
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, val = line[2:].split(":", 1)
        meta[key.strip()] = val.strip()
    return meta


def list_lesson_rows(session: Session, source_id: uuid.UUID) -> list[LibrarySourceLesson]:
    return list(
        session.scalars(
            select(LibrarySourceLesson)
            .where(LibrarySourceLesson.source_id == source_id)
            .order_by(LibrarySourceLesson.sort_index.asc(), LibrarySourceLesson.lesson_key.asc())
        ).all()
    )
