"""Link library course sources (DB) to on-disk lesson trees under v2/data/."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # v2/
DATA_ROOT = ROOT / "data"

COURSE_TAG_PREFIX = "course_id:"
KNOWN_MANIFEST_DIRS = {"scytale-soc2", "drata-soc2"}

# Destination IDs in sources.tags may differ from legacy on-disk folder names.
LEGACY_DISK_ALIASES: dict[str, str] = {
    "soc-2-compliance": "scytale-soc2",
    "scytale-soc-2": "scytale-soc2",
    "drata-soc-2": "drata-soc2",
}


def slugify_course_id(name: str) -> str:
    raw = (name or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return slug[:80] or "course"


def course_id_from_tags(tags: list | None) -> str | None:
    for tag in tags or []:
        raw = str(tag or "").strip()
        if raw.lower().startswith(COURSE_TAG_PREFIX):
            cid = raw[len(COURSE_TAG_PREFIX) :].strip()
            if cid:
                return cid
    return None


def course_id_tag(course_id: str) -> str:
    return f"{COURSE_TAG_PREFIX}{course_id.strip()}"


def resolve_disk_course_id(course_id: str) -> str:
    """Map source destination id to the folder under v2/data/ (legacy aliases included)."""
    slug = slugify_course_id(course_id)
    return LEGACY_DISK_ALIASES.get(slug, slug)


def course_data_dir(course_id: str) -> Path:
    return DATA_ROOT / slugify_course_id(course_id)


def resolved_course_data_dir(course_id: str) -> Path:
    """On-disk folder for reading manifests (includes legacy folder aliases)."""
    return DATA_ROOT / resolve_disk_course_id(course_id)


def infer_connector(url: str) -> str:
    """Guess curriculum *shape* from URL path hints — not vendor brand."""
    from app.services.course_parsers.youtube_curriculum import is_youtube_playlist_url

    u = (url or "").lower()
    if is_youtube_playlist_url(url or ""):
        return "youtube_playlist"
    if "youtu.be" in u or "youtube.com" in u:
        return "youtube_curriculum"
    if "coursera.org" in u:
        return "coursera_catalog"
    if "udemy.com" in u:
        return "udemy_catalog"
    if "/learn/" in u or "/articles" in u or "/blog/" in u:
        return "article_hub"
    if "curriculum" in u or "/course/" in u or "/soc2/" in u or "/soc-2/" in u:
        return "youtube_curriculum"
    return "website"


def normalize_connector(connector: str | None) -> str:
    """Accept legacy vendor names saved before rename."""
    c = (connector or "manual").strip().lower()
    aliases = {
        "strongdm": "youtube_curriculum",
        "drata": "article_hub",
        "youtube": "youtube_curriculum",
        "coursera": "coursera_catalog",
        "udemy": "udemy_catalog",
    }
    return aliases.get(c, c or "manual")


def ensure_course_data_dir(course_id: str) -> Path:
    _migrate_legacy_api_data_dir(course_id)
    out = course_data_dir(course_id)
    (out / "pages").mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.json"
    if not manifest.is_file():
        manifest.write_text("[]", encoding="utf-8")
    return out


def _migrate_legacy_api_data_dir(course_id: str) -> None:
    """One-time fix: older builds wrote under v2/api/data instead of v2/data."""
    slug = slugify_course_id(course_id)
    legacy = Path(__file__).resolve().parents[2] / "data" / slug
    target = course_data_dir(slug)
    if not legacy.is_dir() or target.exists():
        return
    shutil.copytree(legacy, target)


def _read_frontmatter_manual(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "- manual: true" in text.lower()


def persist_course_lessons(
    *,
    course_id: str,
    course_name: str,
    lessons: list[dict],
) -> dict:
    """
    Write discovered lessons to v2/data/{course_id}/manifest.json + pages/*.md.
    Skips markdown files marked manual: true.
    """
    cid = slugify_course_id(course_id)
    out_dir = ensure_course_data_dir(cid)
    pages_dir = out_dir / "pages"
    manifest_path = out_dir / "manifest.json"

    existing_manifest: list[dict] = []
    if manifest_path.is_file():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_manifest = []

    manual_files: set[str] = set()
    for row in existing_manifest:
        file_rel = row.get("file")
        if not file_rel:
            continue
        path = ROOT / str(file_rel).replace("\\", "/")
        if _read_frontmatter_manual(path):
            manual_files.add(str(file_rel).replace("\\", "/"))

    manifest: list[dict] = []
    written = 0
    skipped_manual = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for idx, lesson in enumerate(lessons, start=1):
        lesson_id = str(lesson.get("id") or f"{cid}-{idx:03d}")
        slug = re.sub(r"[^a-z0-9]+", "-", lesson_id.lower()).strip("-")[:80] or f"lesson-{idx:03d}"
        filename = f"{idx:03d}-{slug}.md"
        rel_file = f"data/{cid}/pages/{filename}"
        abs_path = pages_dir / filename

        if rel_file in manual_files or _read_frontmatter_manual(abs_path):
            skipped_manual += 1
            prev = next((r for r in existing_manifest if r.get("file") == rel_file), None)
            if prev:
                manifest.append(prev)
            continue

        title = str(lesson.get("title") or f"Lesson {idx}").strip()
        category = str(lesson.get("category") or "General").strip()
        kind = str(lesson.get("kind") or ("video" if lesson.get("video_url") else "text")).strip()
        url = str(lesson.get("video_url") or lesson.get("url") or "").strip()
        description = str(lesson.get("description") or "").strip()
        body = description or ("*(Content not fetched yet — run refresh to pull article/video body.)*")

        frontmatter = [
            f"- kind: {kind}",
            f"- title: {title}",
            f"- category: {category}",
            f"- course: {course_name}",
            f"- course_id: {cid}",
            f"- order: {idx}",
        ]
        if url:
            frontmatter.append(f"- url: {url}")
        if lesson.get("has_video"):
            frontmatter.append("- has_video: true")
        frontmatter.append(f"- fetched_at: {now}")

        abs_path.write_text(
            f"# {title}\n\n" + "\n".join(frontmatter) + "\n\n---\n\n" + body + "\n",
            encoding="utf-8",
        )
        written += 1

        manifest.append(
            {
                "index": idx,
                "kind": kind,
                "label": title,
                "title": title,
                "category": category,
                "url": url or None,
                "file": rel_file,
                "chars": len(body),
                "ok": True,
                "lesson_id": lesson_id,
            }
        )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "course_id": cid,
        "data_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"),
        "lessons_total": len(lessons),
        "lessons_written": written,
        "lessons_skipped_manual": skipped_manual,
    }


_YOUTUBE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s\"']+|youtu\.be/[\w-]+)",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(r"^(.*?)\s*\((\d{1,2}):(\d{2})\)\s*$")


def _parse_duration_title(text: str) -> tuple[str, int | None]:
    match = _DURATION_RE.match((text or "").strip())
    if not match:
        return (text or "").strip(), None
    title = match.group(1).strip()
    seconds = int(match.group(2)) * 60 + int(match.group(3))
    return title, seconds


def _youtube_video_id(url: str) -> str | None:
    u = (url or "").strip()
    m = re.search(r"youtu\.be/([\w-]+)", u, re.I)
    if m:
        return m.group(1)
    m = re.search(r"[?&]v=([\w-]+)", u, re.I)
    return m.group(1) if m else None


def parse_manual_lesson_line(line: str, *, default_category: str) -> dict | None:
    """Parse one line: URL, Title | URL, or Section | Title | URL."""
    raw = (line or "").strip()
    if not raw or raw.startswith("#"):
        return None

    parts = [p.strip() for p in raw.split("|") if p.strip()]
    url: str | None = None
    for part in reversed(parts):
        if "youtu" in part.lower():
            url = part
            break
    if not url:
        found = _YOUTUBE_URL_RE.search(raw)
        url = found.group(0) if found else None
    if not url:
        return None

    if len(parts) >= 3:
        category, title = parts[0], parts[1]
    elif len(parts) == 2:
        category, title = default_category, parts[0]
    else:
        category = default_category
        vid = _youtube_video_id(url)
        title = f"YouTube {vid}" if vid else "YouTube lesson"

    title, duration_seconds = _parse_duration_title(title)
    if not title:
        vid = _youtube_video_id(url)
        title = f"YouTube {vid}" if vid else "YouTube lesson"

    vid = _youtube_video_id(url) or "video"
    return {
        "id": f"man-{slugify_course_id(category)}-{vid}"[:140],
        "title": title,
        "category": category or default_category,
        "kind": "video",
        "has_video": True,
        "video_url": url,
        "url": url,
        "duration_seconds": duration_seconds,
        "manual": True,
    }


def import_manual_youtube_lessons(
    *,
    course_id: str,
    course_name: str,
    text: str,
    default_category: str = "General",
) -> dict:
    """
    Append hand-entered YouTube lessons to the destination folder v2/data/{course_id}/.
    Each line: URL, Title | URL, or Section | Title | URL.
    """
    cid = slugify_course_id(course_id)
    out_dir = ensure_course_data_dir(cid)
    pages_dir = out_dir / "pages"
    manifest_path = out_dir / "manifest.json"

    existing_manifest: list[dict] = []
    if manifest_path.is_file():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_manifest = []

    existing_urls = {
        str(row.get("url") or "").rstrip("/").lower()
        for row in existing_manifest
        if row.get("url")
    }
    max_index = max((int(r.get("index") or 0) for r in existing_manifest), default=0)

    parsed: list[dict] = []
    skipped = 0
    for line in (text or "").splitlines():
        lesson = parse_manual_lesson_line(line, default_category=default_category)
        if not lesson:
            continue
        norm_url = str(lesson.get("url") or "").rstrip("/").lower()
        if norm_url in existing_urls:
            skipped += 1
            continue
        parsed.append(lesson)
        existing_urls.add(norm_url)

    if not parsed:
        return {
            "course_id": cid,
            "data_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"),
            "imported": 0,
            "skipped": skipped,
            "message": "No new YouTube URLs found in input",
        }

    manifest = list(existing_manifest)
    written = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for lesson in parsed:
        max_index += 1
        idx = max_index
        lesson_id = str(lesson["id"])
        slug = re.sub(r"[^a-z0-9]+", "-", lesson_id.lower()).strip("-")[:80] or f"lesson-{idx:03d}"
        filename = f"{idx:03d}-{slug}.md"
        rel_file = f"data/{cid}/pages/{filename}"
        abs_path = pages_dir / filename

        title = lesson["title"]
        category = lesson["category"]
        url = lesson["url"]
        body = f"Manual YouTube lesson.\n\nWatch: {url}\n"

        frontmatter = [
            f"- kind: video",
            f"- title: {title}",
            f"- category: {category}",
            f"- course: {course_name}",
            f"- course_id: {cid}",
            f"- order: {idx}",
            f"- url: {url}",
            "- has_video: true",
            "- manual: true",
            f"- fetched_at: {now}",
        ]
        if lesson.get("duration_seconds"):
            frontmatter.append(f"- duration_seconds: {lesson['duration_seconds']}")

        abs_path.write_text(
            f"# {title}\n\n" + "\n".join(frontmatter) + "\n\n---\n\n" + body + "\n",
            encoding="utf-8",
        )
        written += 1
        manifest.append(
            {
                "index": idx,
                "kind": "video",
                "label": title,
                "title": title,
                "category": category,
                "url": url,
                "file": rel_file,
                "chars": len(body),
                "ok": True,
                "lesson_id": lesson_id,
                "manual": True,
            }
        )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "course_id": cid,
        "data_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"),
        "imported": written,
        "skipped": skipped,
    }
