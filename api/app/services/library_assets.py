"""Resolve library record → on-disk file with path traversal guard."""
from __future__ import annotations

from pathlib import Path

from app.models.record import Record
from app.models.source import Source
from app.services.library_paths import path_from_source_url


def resolve_record_file(record: Record, source: Source) -> Path | None:
    """Return absolute file path if still present and under the source root."""
    fields = record.fields or {}
    raw = fields.get("absolute_path")
    if not raw:
        return None
    try:
        file_path = Path(str(raw)).resolve()
    except (OSError, ValueError):
        return None
    if not file_path.is_file():
        return None
    try:
        root = path_from_source_url(source.source_url)
    except ValueError:
        return None
    try:
        file_path.relative_to(root)
    except ValueError:
        return None
    return file_path
