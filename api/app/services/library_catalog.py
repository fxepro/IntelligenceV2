"""File-backed Library catalog (Scytale dump + Docling-parsed materials)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[3]  # v2/
DATA_ROOT = ROOT / "data"
SCYTALE_DIR = DATA_ROOT / "scytale-soc2"
DRATA_DIR = DATA_ROOT / "drata-soc2"
PARSED_DIR = DATA_ROOT / "library" / "parsed"
MANUAL_DIR = DATA_ROOT / "library" / "manual"
MANIFEST = SCYTALE_DIR / "manifest.json"
DRATA_MANIFEST = DRATA_DIR / "manifest.json"

_KIND_MAP = {
    "lesson": "video",
    "text": "text",
    "quiz": "quiz",
    "video": "video",
    "pdf": "pdf",
}


class LessonAsset(BaseModel):
    kind: str
    url: str | None = None
    file: str | None = None


class LessonSummary(BaseModel):
    id: str
    title: str
    course_id: str = "general"
    course: str = "General"
    category: str
    kind: str
    label: str
    source_url: str | None = None
    chars: int = 0
    has_text: bool = False
    has_video: bool = False
    has_pdf: bool = False
    # ready = real content captured; locked = Thinkific prerequisite gate scraped instead
    content_status: str = "ready"
    # Per-lesson publish (videos default off). Off = hidden from read/nav/export.
    published: bool = True


class LessonDetail(LessonSummary):
    body: str = ""
    assets: list[LessonAsset] = Field(default_factory=list)
    fetched_at: str | None = None
    lock_reason: str | None = None
    prev_id: str | None = None
    prev_title: str | None = None
    next_id: str | None = None
    next_title: str | None = None


class CourseSummary(BaseModel):
    id: str
    name: str
    lesson_count: int = 0
    kinds: dict[str, int] = Field(default_factory=dict)
    modules: list[str] = Field(default_factory=list)
    published: bool = True
    unpublished_count: int = 0


def _is_prerequisite_gate(body: str) -> bool:
    """True when scrape captured Thinkific's lock dialog instead of lesson text."""
    low = (body or "").lower()
    if "have not yet been completed" in low:
        return True
    if "prerequisite" in low and "ok, got it" in low:
        return True
    return False


def _lock_reason(body: str) -> str | None:
    if not _is_prerequisite_gate(body):
        return None
    m = re.search(
        r"complete all prerequisites in ([^\n]+)",
        body or "",
        re.I,
    )
    if m:
        return f"Locked on source — complete prerequisites in {m.group(1).strip()}"
    return "Locked on source — prerequisites were not completed when this page was downloaded"


def _course_from_source(url: str = "", page_title: str = "") -> tuple[str, str]:
    """Return (course_id, course_name). Course sits above lesson in the Library hierarchy."""
    low_url = (url or "").lower()
    if "drata.com/learn/soc-2" in low_url:
        return "drata-soc-2", "Drata SOC 2"

    m = re.search(r"/courses/take/([^/]+)", url or "", re.I)
    slug = (m.group(1) if m else "").strip()
    if slug:
        low = slug.lower().replace("_", "-")
        # Scytale Academy course — product name the user expects.
        if "soc-2" in low or "soc2" in low:
            return "soc-2-compliance", "SOC 2 Compliance"
        name = _title_case_slug(re.sub(r"^(scytale|course)[-_]+", "", slug, flags=re.I))
        cid = re.sub(r"[^\w\-]+", "-", (name or slug).lower()).strip("-")[:80] or "course"
        return cid, name or "Course"

    title = (page_title or "").strip()
    if " - " in title:
        title = title.split(" - ", 1)[0].strip()
    if title and "soc 2" in title.lower():
        return "soc-2-compliance", "SOC 2 Compliance"
    if title:
        cid = re.sub(r"[^\w\-]+", "-", title.lower()).strip("-")[:80] or "course"
        return cid, title
    return "general", "General"


def _category_from_label(label: str, title: str, url: str = "") -> str:
    # Prefer numbered title; labels may be chrome like "Skip to main content".
    for text in (title, label, url):
        text = (text or "").strip()
        if not text or text.lower().startswith("skip to"):
            continue
        low = text.lower()

        if "final exam" in low:
            return "Final Exam"
        if "glossary" in low:
            return "Glossary"
        if "preface" in low or "instructor" in low or "overview" in low:
            return "Overview"

        mq = re.search(r"module\s+(\d+)\s*quiz", low)
        if mq:
            return f"Module {mq.group(1)}"

        m = re.match(r"^(\d+)(?:\.\d+)?\b", text)
        if m:
            return f"Module {m.group(1)}"

        mq2 = re.search(r"module\s+(\d+)", low)
        if mq2:
            return f"Module {mq2.group(1)}"

        # Thinkific slug: …/35009308-1-introduction or …/33653592-1-1-what-is-…
        slug = text.rstrip("/").split("/")[-1]
        ms = re.match(r"^\d+-(\d+)(?:\.\d+)?-", slug)
        if ms:
            return f"Module {ms.group(1)}"

    return "General"


def _title_case_slug(rest: str) -> str:
    rest = rest.replace("-", " ").strip()
    if not rest:
        return ""
    # Prefer readable title case from URL slugs.
    small = {"a", "an", "the", "and", "or", "of", "to", "for", "in", "on"}
    words = rest.split()
    out: list[str] = []
    for i, w in enumerate(words):
        low = w.lower()
        if low in ("soc", "aicpa", "coso", "tsc", "it"):
            out.append(low.upper())
        elif i > 0 and low in small:
            out.append(low)
        else:
            out.append(low[:1].upper() + low[1:] if low else w)
    return " ".join(out)


def _clean_title(label: str, url: str = "", fallback: str = "") -> str:
    """Lesson display name — e.g. 'SOC 2 Compliance', not module chrome or TOC labels."""
    text = (label or "").strip()
    if text.lower() in ("skip to main content", "skip to content", ""):
        text = ""

    # Preserve "Module N Quiz" before stripping kind suffixes.
    quiz_keep = re.match(r"^(Module\s+\d+)\s+Quiz\b", text, re.I)
    if quiz_keep:
        return f"{quiz_keep.group(1)} Quiz"

    for noise in (
        " TEXT",
        " Text",
        " VIDEO",
        " Video",
        " QUIZ",
        " Quiz",
        " · PREREQUISITE",
        " PREREQUISITE",
    ):
        text = text.replace(noise, "")
    text = re.sub(r"\s*[·•].*$", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()

    # Drop leading outline numbers: "1.1 What is SOC 2 Compliance?" → "What is SOC 2 Compliance?"
    text = re.sub(r"^\d+(?:\.\d+)*\s+", "", text).strip()
    # "1. Introduction to SOC 2" after partial clean
    text = re.sub(r"^\d+\.\s+", "", text).strip()

    if text:
        # Title-case tiny all-lowercase leftovers from slugs
        if text == text.lower() and " " in text:
            text = text.title()
        return text

    if url:
        slug = url.rstrip("/").split("/")[-1]
        # Thinkific: 33653592-1-1-what-is-soc-2-compliance
        m = re.match(r"^\d+-\d+(?:\.\d+)*-(.+)$", slug)
        if m:
            titled = _title_case_slug(m.group(1))
            if titled:
                return titled
        m2 = re.match(r"^\d+-(.+)$", slug)
        if m2:
            titled = _title_case_slug(m2.group(1))
            if titled:
                return titled
        slug = _title_case_slug(slug)
        if slug:
            return slug
    return fallback or "Untitled lesson"


def _strip_course_chrome(body: str, title: str = "") -> str:
    """Remove Thinkific sidebar TOC that was scraped into every page body."""
    text = (body or "").strip()
    if not text:
        return ""

    # Curriculum nav ends at this marker; real lesson content follows.
    for marker in ("Opens in a new window", "Open in a new window"):
        idx = text.find(marker)
        if idx >= 0:
            text = text[idx + len(marker) :].strip()
            break
    else:
        # Fallback: drop leading chrome until a blank line after "Completed" blocks
        lines = text.splitlines()
        cut = 0
        for i, line in enumerate(lines):
            low = line.strip().lower()
            if low in ("completed", "search by lesson title", "go to dashboard"):
                cut = i + 1
            if re.match(r"^module\s+\d+:", low) or low in ("overview", "glossary", "final exam"):
                cut = i + 1
        if cut > 0 and cut < len(lines):
            text = "\n".join(lines[cut:]).strip()

    drop_exact = {
        "enable fullscreen",
        "complete & continue",
        "mark incomplete",
        "continue",
        "skip to main content",
        "go to dashboard",
        "video",
        "text",
        "quiz",
        "prerequisite",
    }
    cleaned: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        if s.lower() in drop_exact:
            continue
        if re.match(r"^[·•\s]+$", s):
            continue
        if re.match(r"^\d+\s*/\s*\d+$", s):
            continue
        if re.match(r"^<?\s*\d+\s*min\b", s, re.I):
            continue
        if re.match(r"^\d+\s+questions?\b", s, re.I):
            continue
        cleaned.append(s)
    text = "\n".join(cleaned).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Leading duplicate of the lesson name (often repeated after the TOC cut).
    if title:
        t = title.strip()
        if text.lower().startswith(t.lower()):
            text = text[len(t) :].lstrip(" \n:-").strip()
        # Numbered form still present in some dumps
        m = re.match(rf"^\d+(?:\.\d+)*\s+{re.escape(t)}\s*", text, re.I)
        if m:
            text = text[m.end() :].strip()

    return text.strip()


def _read_markdown(path: Path) -> tuple[str, str, dict[str, str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta: dict[str, str] = {}
    body = raw
    if raw.startswith("#"):
        parts = raw.split("\n---\n", 1)
        header = parts[0]
        body = parts[1] if len(parts) > 1 else raw
        for line in header.splitlines():
            line = line.strip()
            if line.startswith("- ") and ":" in line:
                key, _, val = line[2:].partition(":")
                meta[key.strip()] = val.strip()
            elif line.startswith("# "):
                meta["doc_title"] = line[2:].strip()
    return meta.get("doc_title") or "", body.strip(), meta


def _lesson_id(index: int, file_rel: str) -> str:
    rel = (file_rel or "").replace("\\", "/")
    stem = Path(rel).stem if rel else f"lesson-{index:03d}"
    if "scytale-soc2" in rel:
        return f"scy-{index:03d}-{stem[:40]}"
    if "drata-soc2" in rel and "drata-soc-2-learn" not in rel:
        return f"dra-{index:03d}-{stem[:40]}"
    return f"lesson-{index}"


def _load_scytale() -> list[LessonDetail]:
    if not MANIFEST.is_file():
        return []
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out: list[LessonDetail] = []
    for row in rows:
        if not row.get("ok"):
            continue
        file_rel = row.get("file") or ""
        path = ROOT / file_rel
        if not path.is_file():
            continue
        _doc_title, raw_body, meta = _read_markdown(path)
        raw_kind = (row.get("kind") or "text").lower()
        kind = _KIND_MAP.get(raw_kind, raw_kind if raw_kind in ("text", "video", "pdf", "quiz") else "text")
        label = row.get("label") or ""
        url = row.get("url") or meta.get("url") or ""
        title = (
            meta.get("title")
            or _clean_title(label, url=url, fallback=Path(file_rel).stem)
        )
        # Category from raw label + URL (outline numbers) so Module N stays correct.
        category = meta.get("category") or _category_from_label(label, title, url=url)
        course_id, course_name = _course_from_source(url=url, page_title=_doc_title or row.get("title") or "")
        if meta.get("course"):
            course_name = meta["course"].strip() or course_name
            # Keep course_id aligned when frontmatter sets the SOC 2 course name.
            if "soc 2" in course_name.lower():
                course_id = "soc-2-compliance"
        body = _strip_course_chrome(raw_body, title=title)
        locked = _is_prerequisite_gate(body) or _is_prerequisite_gate(raw_body)
        lock_reason = _lock_reason(body) or _lock_reason(raw_body) if locked else None
        if locked:
            body = ""
        lid = _lesson_id(int(row.get("index") or 0), file_rel)
        assets: list[LessonAsset] = [
            LessonAsset(kind=kind, url=url or None, file=file_rel.replace("\\", "/")),
        ]
        out.append(
            LessonDetail(
                id=lid,
                title=title,
                course_id=course_id,
                course=course_name,
                category=category,
                kind=kind,
                label=label or title,
                source_url=url or None,
                chars=len(body),
                has_text=bool(body) and not locked,
                has_video=kind == "video",
                has_pdf=kind == "pdf",
                content_status=(
                    "skipped"
                    if kind == "video"
                    else ("locked" if locked else ("empty" if not body else "ready"))
                ),
                body=body,
                assets=assets,
                fetched_at=meta.get("fetched_at"),
                lock_reason=lock_reason,
            )
        )
    return out


def _load_drata() -> list[LessonDetail]:
    if not DRATA_MANIFEST.is_file():
        return []
    return _load_manifest_course(DRATA_MANIFEST, "drata-soc-2", "Drata SOC 2")


def _load_manifest_course(manifest_path: Path, course_id: str, course_name: str) -> list[LessonDetail]:
    if not manifest_path.is_file():
        return []
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    out: list[LessonDetail] = []
    for row in rows:
        if not row.get("ok"):
            continue
        file_rel = row.get("file") or ""
        path = ROOT / file_rel
        body = ""
        meta: dict = {}
        if path.is_file():
            _doc_title, body, meta = _read_markdown(path)
        elif not row.get("url"):
            continue
        title = (
            meta.get("title")
            or row.get("title")
            or _doc_title
            or _clean_title(row.get("label") or "", url=row.get("url") or "", fallback=Path(file_rel).stem)
        )
        category = meta.get("category") or row.get("category") or "General"
        url = row.get("url") or meta.get("url") or ""
        cname = meta.get("course") or course_name
        cid = meta.get("course_id") or course_id
        raw_kind = (row.get("kind") or meta.get("kind") or "text").lower()
        kind = _KIND_MAP.get(raw_kind, raw_kind if raw_kind in ("text", "video", "pdf", "quiz") else "text")
        lid = row.get("lesson_id") or _lesson_id(int(row.get("index") or 0), file_rel)
        out.append(
            LessonDetail(
                id=lid,
                title=title,
                course_id=cid,
                course=cname,
                category=category,
                kind=kind,
                label=row.get("label") or title,
                source_url=url or None,
                chars=len(body),
                has_text=bool(body),
                has_video=kind == "video" or bool(meta.get("has_video")),
                has_pdf=kind == "pdf",
                content_status="ready" if body else "empty",
                body=body,
                assets=[LessonAsset(kind=kind, url=url or None, file=file_rel.replace("\\", "/"))],
                fetched_at=meta.get("fetched_at"),
            )
        )
    return out


def _load_discovered() -> list[LessonDetail]:
    """Courses under v2/data/{slug}/ with manifest.json (excluding scytale/drata)."""
    from app.services.library_course_paths import KNOWN_MANIFEST_DIRS

    out: list[LessonDetail] = []
    if not DATA_ROOT.is_dir():
        return out
    for child in sorted(DATA_ROOT.iterdir()):
        if not child.is_dir() or child.name in KNOWN_MANIFEST_DIRS:
            continue
        manifest = child / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            rows = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not rows:
            continue
        course_name = child.name.replace("-", " ").title()
        out.extend(_load_manifest_course(manifest, child.name, course_name))
    return out


def _load_parsed() -> list[LessonDetail]:
    if not PARSED_DIR.is_dir():
        return []
    out: list[LessonDetail] = []
    for path in sorted(PARSED_DIR.glob("*.md")):
        _doc_title, body, meta = _read_markdown(path)
        title = meta.get("title") or _doc_title or path.stem.replace("-", " ")
        category = meta.get("category") or "Parsed materials"
        kind = meta.get("kind") or "pdf"
        if kind not in ("text", "video", "pdf", "quiz"):
            kind = "pdf"
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        lid = f"doc-{path.stem[:80]}"
        out.append(
            LessonDetail(
                id=lid,
                title=title,
                course_id="parsed-materials",
                course=meta.get("course") or "Parsed materials",
                category=category,
                kind=kind,
                label=title,
                source_url=meta.get("source") or None,
                chars=len(body),
                has_text=True,
                has_video=False,
                has_pdf=kind == "pdf",
                body=body,
                assets=[LessonAsset(kind=kind, file=rel)],
                fetched_at=meta.get("fetched_at"),
            )
        )
    return out


def _load_manual() -> list[LessonDetail]:
    """Hand-authored lessons under data/library/manual/{course_id}/ — survive Refresh."""
    if not MANUAL_DIR.is_dir():
        return []
    out: list[LessonDetail] = []
    for course_dir in sorted(MANUAL_DIR.iterdir()):
        if not course_dir.is_dir():
            continue
        course_id = course_dir.name
        pages = course_dir / "pages"
        scan = pages if pages.is_dir() else course_dir
        for path in sorted(scan.glob("*.md")):
            _doc_title, body, meta = _read_markdown(path)
            title = meta.get("title") or _doc_title or path.stem.replace("-", " ")
            category = meta.get("category") or "Manual"
            kind = (meta.get("kind") or "text").lower()
            if kind not in ("text", "video", "pdf", "quiz"):
                kind = "text"
            course_name = meta.get("course") or course_id.replace("-", " ").title()
            # Prefer explicit order; else parse leading NNN from filename
            order_raw = meta.get("order") or ""
            try:
                order = int(str(order_raw).strip())
            except ValueError:
                m = re.match(r"^(\d+)", path.stem)
                order = int(m.group(1)) if m else 9_000
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            stem = path.stem[:80]
            lid = f"man-{course_id}-{stem}"[:140]
            out.append(
                LessonDetail(
                    id=lid,
                    title=title,
                    course_id=course_id,
                    course=course_name,
                    category=category,
                    kind=kind,
                    label=meta.get("label") or title,
                    source_url=meta.get("url") or None,
                    chars=len(body),
                    has_text=bool(body),
                    has_video=kind == "video",
                    has_pdf=kind == "pdf",
                    content_status="ready" if body else "empty",
                    body=body,
                    assets=[LessonAsset(kind=kind, file=rel)],
                    fetched_at=meta.get("fetched_at"),
                )
            )
            # stash order on object for sort (dynamic attr ok for in-process)
            setattr(out[-1], "_manual_order", order)
    return out


def _all_lessons() -> list[LessonDetail]:
    return _load_scytale() + _load_drata() + _load_discovered() + _load_parsed() + _load_manual()


def _lesson_published_flag(item: LessonSummary | LessonDetail) -> bool:
    from app.services.library_publish import is_lesson_published

    return is_lesson_published(item.id, item.kind)


def _is_publishable(item: LessonSummary | LessonDetail) -> bool:
    """Included in read / next-prev / DOCX when per-lesson Publish is On."""
    return _lesson_published_flag(item)


def _module_sort_key(category: str) -> tuple:
    """Natural module order: Overview → Module 1…N → Glossary → Final Exam → other."""
    raw = (category or "").strip()
    low = raw.lower()
    if low == "overview":
        return (0, 0, raw.lower())
    m = re.match(r"^module\s+(\d+)\b", low)
    if m:
        return (1, int(m.group(1)), raw.lower())
    if low == "glossary":
        return (2, 0, raw.lower())
    if low == "final exam":
        return (3, 0, raw.lower())
    if low in ("manual", "table of contents", "toc"):
        return (-1, 0, raw.lower())  # before Overview
    if low in ("general", ""):
        return (5, 0, raw.lower())
    return (4, 0, raw.lower())


def _lesson_sort_key(item: LessonSummary | LessonDetail) -> tuple:
    manual_order = getattr(item, "_manual_order", None)
    if manual_order is not None:
        idx = int(manual_order)
    else:
        m = re.match(r"^(?:scy|dra)-(\d+)", item.id or "")
        if m:
            idx = int(m.group(1))
        else:
            m_lesson = re.match(r"^lesson-(\d+)$", item.id or "")
            if m_lesson:
                idx = int(m_lesson.group(1))
            else:
                m2 = re.search(r"-(\d{3})-", item.id or "")
                idx = int(m2.group(1)) if m2 else 10_000
    return (_module_sort_key(item.category), idx, (item.title or "").lower())


def _course_query_keys(course_key: str) -> frozenset[str]:
    """Map destination ids to all disk/catalog course_id values (legacy folder names)."""
    aliases: dict[str, frozenset[str]] = {
        "soc-2-compliance": frozenset({"soc-2-compliance", "scytale-soc2", "scytale-soc-2"}),
        "scytale-soc2": frozenset({"soc-2-compliance", "scytale-soc2", "scytale-soc-2"}),
        "scytale-soc-2": frozenset({"soc-2-compliance", "scytale-soc2", "scytale-soc-2"}),
        "drata-soc-2": frozenset({"drata-soc-2", "drata-soc2"}),
        "drata-soc2": frozenset({"drata-soc-2", "drata-soc2"}),
    }
    return aliases.get(course_key, frozenset({course_key}))


def list_lessons(
    *,
    course: str | None = None,
    kind: str | None = None,
    category: str | None = None,
    q: str | None = None,
    published_only: bool = False,
) -> tuple[list[LessonSummary], dict[str, int], list[str]]:
    """
    List lessons for the Library UI.

    By default includes unpublished rows (so Publish can be toggled on the lessons page).
    Pass published_only=True for export / public reading sets.
    """
    items = _all_lessons()

    course_key = (course or "").strip().lower()
    kind_key = (kind or "").strip().lower()
    cat_key = (category or "").strip()
    query = (q or "").strip().lower()

    scoped: list[LessonDetail] = []
    course_keys = _course_query_keys(course_key) if course_key else frozenset()
    for item in items:
        if course_key and item.course_id.lower() not in course_keys and item.course.lower() != course_key:
            continue
        if published_only and not _is_publishable(item):
            continue
        scoped.append(item)

    kinds: dict[str, int] = {}
    categories: set[str] = set()
    for item in scoped:
        kinds[item.kind] = kinds.get(item.kind, 0) + 1
        categories.add(item.category)

    filtered: list[LessonDetail] = []
    for item in scoped:
        if kind_key and item.kind != kind_key:
            continue
        if cat_key and item.category != cat_key:
            continue
        if query:
            hay = f"{item.title} {item.label} {item.category} {item.course}".lower()
            if query not in hay:
                continue
        filtered.append(item)

    summaries = [
        LessonSummary(
            id=i.id,
            title=i.title,
            course_id=i.course_id,
            course=i.course,
            category=i.category,
            kind=i.kind,
            label=i.label,
            source_url=i.source_url,
            chars=i.chars,
            has_text=i.has_text,
            has_video=i.has_video,
            has_pdf=i.has_pdf,
            content_status=i.content_status,
            published=_lesson_published_flag(i),
        )
        for i in filtered
    ]
    summaries.sort(key=_lesson_sort_key)
    return summaries, kinds, sorted(categories, key=_module_sort_key)


def list_courses() -> list[CourseSummary]:
    """All Library courses (Scytale, Drata, parsed, …) with publish settings."""
    from app.services.library_publish import get_course_publish_settings

    by_id: dict[str, CourseSummary] = {}
    for item in _all_lessons():
        row = by_id.get(item.course_id)
        if not row:
            settings = get_course_publish_settings(item.course_id)
            row = CourseSummary(
                id=item.course_id,
                name=item.course,
                published=settings.published,
            )
            by_id[item.course_id] = row
        if not _is_publishable(item):
            row.unpublished_count += 1
            continue
        row.lesson_count += 1
        row.kinds[item.kind] = row.kinds.get(item.kind, 0) + 1
        if item.category and item.category not in row.modules:
            row.modules.append(item.category)
    for row in by_id.values():
        row.modules = sorted(row.modules, key=_module_sort_key)
    return sorted(by_id.values(), key=lambda c: c.name.lower())


def get_lesson(lesson_id: str) -> LessonDetail | None:
    items = _all_lessons()
    by_id = {item.id: item for item in items}
    lesson = by_id.get(lesson_id)
    if not lesson:
        return None

    lesson.published = _lesson_published_flag(lesson)

    # Next/Prev only among publishable lessons (skip unpublished, e.g. videos off).
    course_items = sorted(
        [i for i in items if i.course_id == lesson.course_id and _is_publishable(i)],
        key=_lesson_sort_key,
    )
    # If current lesson is unpublished, still allow opening it, but nav skips to neighbors.
    nav_items = course_items
    if not _is_publishable(lesson):
        # Place in sort order among all lessons to find nearest publishable neighbors.
        all_course = sorted(
            [i for i in items if i.course_id == lesson.course_id],
            key=_lesson_sort_key,
        )
        idx_all = next((i for i, row in enumerate(all_course) if row.id == lesson.id), -1)
        prev = next(
            (all_course[j] for j in range(idx_all - 1, -1, -1) if _is_publishable(all_course[j])),
            None,
        )
        nxt = next(
            (all_course[j] for j in range(idx_all + 1, len(all_course)) if _is_publishable(all_course[j])),
            None,
        )
        if prev:
            lesson.prev_id = prev.id
            lesson.prev_title = prev.title
        if nxt:
            lesson.next_id = nxt.id
            lesson.next_title = nxt.title
        return lesson

    idx = next((i for i, row in enumerate(nav_items) if row.id == lesson.id), -1)
    if idx >= 0:
        if idx > 0:
            prev = nav_items[idx - 1]
            lesson.prev_id = prev.id
            lesson.prev_title = prev.title
        if idx + 1 < len(nav_items):
            nxt = nav_items[idx + 1]
            lesson.next_id = nxt.id
            lesson.next_title = nxt.title
    return lesson


def _upsert_frontmatter_key(header: str, key: str, value: str) -> str:
    """Set `- key: value` in the markdown header block; replace existing key if present."""
    lines = header.replace("\r\n", "\n").split("\n")
    prefix = f"- {key}:"
    replaced = False
    out: list[str] = []
    for line in lines:
        if line.strip().startswith(prefix):
            if not replaced:
                out.append(f"- {key}: {value}")
                replaced = True
            continue
        out.append(line)
    if not replaced:
        # Insert after first heading line when present, else at end.
        insert_at = 0
        for i, line in enumerate(out):
            if line.startswith("# "):
                insert_at = i + 1
                break
        # Skip a blank line after the heading when inserting.
        while insert_at < len(out) and not out[insert_at].strip():
            insert_at += 1
        out.insert(insert_at, f"- {key}: {value}")
    return "\n".join(out).rstrip()


def _write_lesson_markdown(
    path: Path,
    *,
    body: str | None = None,
    course: str | None = None,
    title: str | None = None,
) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if "\n---\n" in raw:
        header, old_body = raw.split("\n---\n", 1)
        current_body = old_body
    elif raw.startswith("#"):
        header, current_body = raw, ""
    else:
        header, current_body = "", raw

    if course is not None:
        header = _upsert_frontmatter_key(header or "# Lesson", "course", course.strip())
    if title is not None:
        t = title.strip()
        header = _upsert_frontmatter_key(header or "# Lesson", "title", t)
        # Keep the H1 in sync when present.
        lines = header.split("\n")
        if lines and lines[0].startswith("# "):
            lines[0] = f"# {t}"
            header = "\n".join(lines)

    new_body = current_body if body is None else (body or "").replace("\r\n", "\n").strip()
    if header.strip():
        updated = f"{header.rstrip()}\n\n---\n\n{new_body.strip()}\n"
    else:
        updated = f"{new_body.strip()}\n"
    path.write_text(updated, encoding="utf-8")


def create_lesson(
    course_id: str,
    *,
    title: str,
    category: str = "Overview",
    kind: str = "text",
    body: str = "",
    place: str = "end",
) -> LessonDetail:
    """
    Create a hand-authored lesson for any Library course.

    Stored under data/library/manual/{course_id}/pages/ so Refresh scrape
    does not wipe it.
    """
    cid = (course_id or "").strip()
    if not cid:
        raise ValueError("course_id is required")
    title_name = (title or "").strip()
    if not title_name:
        raise ValueError("title is required")
    cat = (category or "Overview").strip() or "Overview"
    kind_key = (kind or "text").strip().lower()
    if kind_key not in ("text", "video", "pdf", "quiz"):
        kind_key = "text"
    place_key = (place or "end").strip().lower()
    if place_key not in ("start", "end"):
        place_key = "end"

    # Display name from existing course lessons when possible
    course_name = cid.replace("-", " ").title()
    for item in _all_lessons():
        if item.course_id == cid:
            course_name = item.course or course_name
            break

    pages_dir = MANUAL_DIR / cid / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    existing_orders: list[int] = []
    for path in pages_dir.glob("*.md"):
        _d, _b, meta = _read_markdown(path)
        try:
            existing_orders.append(int(str(meta.get("order") or "").strip()))
            continue
        except ValueError:
            pass
        m = re.match(r"^(\d+)", path.stem)
        if m:
            existing_orders.append(int(m.group(1)))

    if place_key == "start":
        order = (min(existing_orders) - 1) if existing_orders else 0
        if order < 0:
            order = 0
            # Shift: still ok — same order sorts by title
    else:
        order = (max(existing_orders) + 1) if existing_orders else 9000

    stem = re.sub(r"[^\w\-]+", "-", title_name.lower()).strip("-")[:60] or "lesson"
    filename = f"{order:03d}-{stem}.md"
    # Avoid collisions
    out_path = pages_dir / filename
    n = 2
    while out_path.exists():
        out_path = pages_dir / f"{order:03d}-{stem}-{n}.md"
        n += 1

    fetched = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body_text = (body or "").replace("\r\n", "\n").strip()
    if not body_text:
        body_text = f"# {title_name}\n\n(Add content here.)"
    md = (
        f"# {title_name}\n\n"
        f"- kind: {kind_key}\n"
        f"- title: {title_name}\n"
        f"- category: {cat}\n"
        f"- course: {course_name}\n"
        f"- order: {order}\n"
        f"- manual: true\n"
        f"- fetched_at: {fetched}\n\n"
        f"---\n\n{body_text}\n"
    )
    out_path.write_text(md, encoding="utf-8")

    expected_id = f"man-{cid}-{out_path.stem[:80]}"[:140]
    lesson = get_lesson(expected_id)
    if not lesson:
        for item in _load_manual():
            if item.course_id == cid and any(
                (a.file or "").endswith(out_path.name) for a in item.assets
            ):
                return item
        raise RuntimeError("Created lesson but could not reload it")
    return lesson


def update_lesson(
    lesson_id: str,
    *,
    body: str | None = None,
    course: str | None = None,
    title: str | None = None,
) -> LessonDetail:
    """
    Update lesson markdown on disk.

    - body / title: this lesson file only
    - course: written to every lesson file in the same course_id (display name override)
    """
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise FileNotFoundError(f"Lesson not found: {lesson_id}")

    rel = next((a.file for a in lesson.assets if a.file), None)
    if not rel:
        raise ValueError("Lesson has no markdown file to update")

    path = (ROOT / rel).resolve()
    try:
        path.relative_to(DATA_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Lesson file path is outside v2/data/") from exc
    if not path.is_file():
        raise FileNotFoundError(f"Lesson file missing: {rel}")

    course_name = course.strip() if isinstance(course, str) else None
    title_name = title.strip() if isinstance(title, str) else None
    if course_name == "":
        raise ValueError("Course name cannot be empty")
    if title_name == "":
        raise ValueError("Lesson title cannot be empty")

    # Only rewrite siblings when the display name actually changes.
    rename_course = (
        course_name is not None
        and course_name != (lesson.course or "").strip()
    )

    _write_lesson_markdown(path, body=body, course=course_name, title=title_name)

    if rename_course and course_name is not None:
        siblings = [i for i in _all_lessons() if i.course_id == lesson.course_id]
        for sib in siblings:
            if sib.id == lesson.id:
                continue
            sib_rel = next((a.file for a in sib.assets if a.file), None)
            if not sib_rel:
                continue
            sib_path = (ROOT / sib_rel).resolve()
            try:
                sib_path.relative_to(DATA_ROOT.resolve())
            except ValueError:
                continue
            if sib_path.is_file():
                _write_lesson_markdown(sib_path, course=course_name)

    refreshed = get_lesson(lesson_id)
    if not refreshed:
        raise RuntimeError("Lesson disappeared after write")
    return refreshed


def update_lesson_body(lesson_id: str, body: str) -> LessonDetail:
    """Backward-compatible body-only update."""
    return update_lesson(lesson_id, body=body)


def parse_document_to_lesson(
    path: Path,
    *,
    title: str | None = None,
    category: str | None = None,
) -> LessonDetail:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError(
            "Docling is not installed. Run: pip install docling"
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(str(path))
    body = result.document.export_to_markdown()
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^\w\-]+", "-", path.stem).strip("-").lower()[:80] or "document"
    out_path = PARSED_DIR / f"{stem}.md"
    lesson_title = (title or path.stem).strip()
    lesson_category = (category or "Parsed materials").strip()
    fetched = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    md = (
        f"# {lesson_title}\n\n"
        f"- kind: pdf\n"
        f"- title: {lesson_title}\n"
        f"- category: {lesson_category}\n"
        f"- course: Parsed materials\n"
        f"- source: {path.name}\n"
        f"- fetched_at: {fetched}\n\n"
        f"---\n\n{body}\n"
    )
    out_path.write_text(md, encoding="utf-8")
    rel = str(out_path.relative_to(ROOT)).replace("\\", "/")
    return LessonDetail(
        id=f"doc-{stem}",
        title=lesson_title,
        course_id="parsed-materials",
        course="Parsed materials",
        category=lesson_category,
        kind="pdf",
        label=lesson_title,
        source_url=None,
        chars=len(body),
        has_text=True,
        has_video=False,
        has_pdf=True,
        body=body,
        assets=[LessonAsset(kind="pdf", file=rel)],
        fetched_at=fetched,
    )
