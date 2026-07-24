"""Download lesson images into v2/data and rewrite markdown to local API URLs."""
from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

from app.services.library_catalog import DATA_ROOT

_IMG_MD = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_FILES_PREFIX = "/api/v1/library/files/"


def _ext_for(url: str, content_type: str | None) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}:
        return suffix if suffix != ".jpeg" else ".jpg"
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed == ".jpe":
            return ".jpg"
        if guessed:
            return guessed
    return ".png"


def _safe_name(index: int, ext: str) -> str:
    return f"{index:03d}{ext}"


def localize_markdown_images(
    md: str,
    *,
    disk_dir: Path,
    files_prefix: str,
    request_get=None,
) -> str:
    """
    Download remote / data: images referenced in markdown into disk_dir.
    Rewrite to /api/v1/library/files/{files_prefix}/NNN.ext

    request_get: callable(url) -> response with .ok, .headers, .body() / .content
                 (Playwright APIResponse) or None to use httpx.
    """
    if not md or "![" not in md:
        return md

    disk_dir.mkdir(parents=True, exist_ok=True)
    files_prefix = files_prefix.strip("/").replace("\\", "/")
    counter = 0
    cache: dict[str, str] = {}  # src -> local api url

    def fetch(url: str) -> tuple[bytes, str | None] | None:
        if request_get is not None:
            try:
                resp = request_get(url)
                if not getattr(resp, "ok", False):
                    return None
                headers = getattr(resp, "headers", {}) or {}
                ctype = headers.get("content-type") or headers.get("Content-Type")
                body = resp.body() if hasattr(resp, "body") else resp.content
                return body, ctype
            except Exception:
                return None
        try:
            import httpx

            with httpx.Client(follow_redirects=True, timeout=45.0) as client:
                resp = client.get(url)
                if resp.status_code >= 400:
                    return None
                return resp.content, resp.headers.get("content-type")
        except Exception:
            return None

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        alt = match.group(1) or ""
        src = (match.group(2) or "").strip().strip('"').strip("'")
        if not src:
            return match.group(0)
        if src.startswith(_FILES_PREFIX):
            return match.group(0)
        if src in cache:
            return f"![{alt}]({cache[src]})"

        data: bytes | None = None
        ctype: str | None = None
        ext = ".png"

        if src.startswith("data:"):
            # data:image/png;base64,....
            try:
                header, _, b64 = src.partition(",")
                mime = header[5:].split(";")[0] if header.startswith("data:") else "image/png"
                ctype = mime
                data = base64.b64decode(b64)
                ext = _ext_for("file.png", mime)
            except Exception:
                return match.group(0)
        else:
            # Skip tiny tracking pixels / svg placeholders often used as chrome
            low = src.lower()
            if "pixel" in low or "spacer" in low or "1x1" in low:
                return ""
            got = fetch(src)
            if not got:
                return match.group(0)
            data, ctype = got
            ext = _ext_for(src, ctype)

        if not data or len(data) < 32:
            return match.group(0)

        # Dedupe by content hash within this page
        digest = hashlib.sha1(data).hexdigest()[:12]
        existing = next(disk_dir.glob(f"*{digest}*"), None)
        if existing and existing.is_file():
            name = existing.name
        else:
            counter += 1
            name = f"{counter:03d}-{digest}{ext}"
            (disk_dir / name).write_bytes(data)

        local = f"{_FILES_PREFIX}{files_prefix}/{name}"
        cache[src] = local
        return f"![{alt}]({local})"

    return _IMG_MD.sub(replace, md)


def resolve_library_file(file_path: str) -> Path | None:
    """Map /api/v1/library/files/... relative path to a file under DATA_ROOT."""
    rel = (file_path or "").replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    path = (DATA_ROOT / rel).resolve()
    try:
        path.relative_to(DATA_ROOT.resolve())
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path
