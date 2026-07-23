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


class LessonDetail(LessonSummary):
    body: str = ""
    assets: list[LessonAsset] = Field(default_factory=list)
    fetched_at: str | None = None
    lock_reason: str | None = None


class CourseSummary(BaseModel):
    id: str
    name: str
    lesson_count: int = 0
    kinds: dict[str, int] = Field(default_factory=dict)
    modules: list[str] = Field(default_factory=list)


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
    stem = Path(file_rel).stem
    return f"scy-{index:03d}-{stem[:40]}"


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
        title = _clean_title(label, url=url, fallback=Path(file_rel).stem)
        # Category from raw label + URL (outline numbers) so Module N stays correct.
        category = _category_from_label(label, title, url=url)
        course_id, course_name = _course_from_source(url=url, page_title=_doc_title or row.get("title") or "")
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
                content_status="locked" if locked else ("empty" if not body and kind != "video" else "ready"),
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
    rows = json.loads(DRATA_MANIFEST.read_text(encoding="utf-8"))
    out: list[LessonDetail] = []
    for row in rows:
        if not row.get("ok"):
            continue
        file_rel = row.get("file") or ""
        path = ROOT / file_rel
        if not path.is_file():
            continue
        _doc_title, body, meta = _read_markdown(path)
        title = (
            meta.get("title")
            or row.get("title")
            or _doc_title
            or _clean_title(row.get("label") or "", url=row.get("url") or "", fallback=Path(file_rel).stem)
        )
        category = meta.get("category") or row.get("category") or "Drata"
        url = row.get("url") or meta.get("url") or ""
        course_id, course_name = "drata-soc-2", "Drata SOC 2"
        if meta.get("course"):
            course_name = meta["course"]
        lid = f"dra-{int(row.get('index') or 0):03d}-{Path(file_rel).stem[:40]}"
        out.append(
            LessonDetail(
                id=lid,
                title=title,
                course_id=course_id,
                course=course_name,
                category=category,
                kind="text",
                label=row.get("label") or title,
                source_url=url or None,
                chars=len(body),
                has_text=bool(body),
                has_video=False,
                has_pdf=False,
                content_status="ready" if body else "empty",
                body=body,
                assets=[LessonAsset(kind="text", url=url or None, file=file_rel.replace("\\", "/"))],
                fetched_at=meta.get("fetched_at"),
            )
        )
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


def _all_lessons() -> list[LessonDetail]:
    return _load_scytale() + _load_drata() + _load_parsed()


def list_lessons(
    *,
    course: str | None = None,
    kind: str | None = None,
    category: str | None = None,
    q: str | None = None,
) -> tuple[list[LessonSummary], dict[str, int], list[str]]:
    items = _all_lessons()

    course_key = (course or "").strip().lower()
    kind_key = (kind or "").strip().lower()
    cat_key = (category or "").strip()
    query = (q or "").strip().lower()

    scoped: list[LessonDetail] = []
    for item in items:
        if course_key and item.course_id.lower() != course_key and item.course.lower() != course_key:
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
        )
        for i in filtered
    ]
    return summaries, kinds, sorted(categories)


def list_courses() -> list[CourseSummary]:
    by_id: dict[str, CourseSummary] = {}
    for item in _all_lessons():
        row = by_id.get(item.course_id)
        if not row:
            row = CourseSummary(id=item.course_id, name=item.course)
            by_id[item.course_id] = row
        row.lesson_count += 1
        row.kinds[item.kind] = row.kinds.get(item.kind, 0) + 1
        if item.category and item.category not in row.modules:
            row.modules.append(item.category)
    for row in by_id.values():
        row.modules = sorted(row.modules)
    return sorted(by_id.values(), key=lambda c: c.name.lower())


def get_lesson(lesson_id: str) -> LessonDetail | None:
    for item in _all_lessons():
        if item.id == lesson_id:
            return item
    return None


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
