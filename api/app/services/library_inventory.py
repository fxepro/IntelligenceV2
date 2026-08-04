"""Filesystem inventory scan for Library sources — metadata only, no parsing."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.services.library_paths import file_uri_for_path, path_from_source_url

SKIP_DIR_NAMES = {
    ".git",
    ".svn",
    "__pycache__",
    "__MACOSX",
    "node_modules",
    "$recycle.bin",
    "system volume information",
}

SKIP_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".tgz",
    ".tbz2",
    ".cab",
    ".iso",
}

MEDIA_TYPE_BY_EXT: dict[str, str] = {
    ".mp4": "video",
    ".mkv": "video",
    ".avi": "video",
    ".mov": "video",
    ".webm": "video",
    ".m4v": "video",
    ".wmv": "video",
    ".pdf": "pdf",
    ".epub": "epub",
    ".mobi": "ebook",
    ".azw": "ebook",
    ".azw3": "ebook",
    ".fb2": "ebook",
    ".docx": "document",
    ".doc": "document",
    ".odt": "document",
    ".txt": "document",
    ".md": "document",
    ".rtf": "document",
    ".mp3": "audio",
    ".m4a": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".aac": "audio",
    ".ogg": "audio",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".bmp": "image",
}


@dataclass(frozen=True)
class InventoryFile:
    absolute_path: Path
    relative_path: str
    media_type: str
    extension: str
    size_bytes: int
    modified_at: datetime
    canonical_url: str
    title: str


def classify_extension(ext: str) -> str:
    return MEDIA_TYPE_BY_EXT.get((ext or "").lower(), "other")


def _should_skip_dir(name: str) -> bool:
    return name.lower() in SKIP_DIR_NAMES or name.startswith(".")


def _should_skip_file(path: Path) -> bool:
    if not path.is_file():
        return True
    name = path.name.lower()
    if name in {"thumbs.db", "desktop.ini", ".ds_store"}:
        return True
    if name == "cover.jpg" or name.startswith("cover."):
        return True
    ext = path.suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return True
    return False


def scan_folder(root: Path) -> list[InventoryFile]:
    """Catalog immediate children of root — one row per top-level file or subfolder."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Source folder not found: {root}")

    items: list[InventoryFile] = []
    try:
        children = sorted(root.iterdir(), key=lambda p: p.name.casefold())
    except OSError as exc:
        raise ValueError(f"Cannot read folder: {root}") from exc

    for path in children:
        if path.is_dir():
            if _should_skip_dir(path.name):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            items.append(
                InventoryFile(
                    absolute_path=path.resolve(),
                    relative_path=path.name,
                    media_type="folder",
                    extension="",
                    size_bytes=0,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    canonical_url=file_uri_for_path(path),
                    title=path.name,
                )
            )
            continue

        if not path.is_file() or _should_skip_file(path):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        ext = path.suffix.lower()
        items.append(
            InventoryFile(
                absolute_path=path.resolve(),
                relative_path=path.name,
                media_type=classify_extension(ext),
                extension=ext or "",
                size_bytes=int(stat.st_size),
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                canonical_url=file_uri_for_path(path),
                title=path.name,
            )
        )
    return items


def scan_source_folder(source_url: str) -> list[InventoryFile]:
    return scan_folder(path_from_source_url(source_url))
