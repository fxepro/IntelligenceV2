"""Normalize local folder paths ↔ file:// source URLs for Library domain."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, unquote, urlparse


def file_uri_to_path(uri: str) -> Path:
    """Resolve a file:// URI to an absolute path."""
    parsed = urlparse((uri or "").strip())
    if parsed.scheme and parsed.scheme.lower() != "file":
        raise ValueError(f"Expected file:// URI, got {parsed.scheme!r}")
    raw = unquote(parsed.path or "")
    if not raw:
        raise ValueError("Empty file path in URI")
    # file:///D:/foo on Windows → /D:/foo
    if raw.startswith("/") and len(raw) >= 3 and raw[2] == ":":
        raw = raw[1:]
    return Path(raw)


def path_to_file_uri(path: Path) -> str:
    """Canonical file:// identity stored in sources.source_url."""
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"Not a directory: {resolved}")
    posix = resolved.as_posix()
    if len(posix) >= 2 and posix[1] == ":":
        return f"file:///{quote(posix, safe='/:')}"
    return f"file://{quote(posix, safe='/:')}"


def normalize_folder_source_url(raw: str) -> str:
    """Accept pasted Windows path or file:// URI; return canonical file:// URI."""
    text = (raw or "").strip().strip('"').strip("'")
    if not text:
        raise ValueError("Folder path is required")
    if text.lower().startswith("file:"):
        path = file_uri_to_path(text)
    else:
        path = Path(text)
    return path_to_file_uri(path)


def path_from_source_url(source_url: str) -> Path:
    return file_uri_to_path(source_url).resolve()


def file_uri_for_path(path: Path) -> str:
    """Canonical per-file URI for records.canonical_url / dedup_key."""
    resolved = path.resolve()
    posix = resolved.as_posix()
    if len(posix) >= 2 and posix[1] == ":":
        return f"file:///{quote(posix, safe='/:')}"
    return f"file://{quote(posix, safe='/:')}"
