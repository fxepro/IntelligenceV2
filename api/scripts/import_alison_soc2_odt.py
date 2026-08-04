"""Parse Alison ODT into course lessons and import to v2/data/."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ODT_DEFAULT = ROOT / "docs/Domains/Courses/SOC2/Essentials of the SOC 2 Cybersecurity Framework - Alison.odt"
COURSE_ID = "alison-soc2-essentials"
COURSE_NAME = "Essentials of the SOC 2 Cybersecurity Framework"
SOURCE_URL = "https://alison.com/course/essentials-of-the-soc-2-cybersecurity-framework"

MODULE_MAP = {
    "introduction to soc 2": "Module 1: Introduction to SOC 2",
    "soc 2 scope": "Module 2: SOC 2 Scope",
    "implementation of soc2": "Module 3: Implementation of SOC 2",
    "implementation of soc 2": "Module 3: Implementation of SOC 2",
    "soc 2 policies": "Module 4: SOC 2 Policies",
    "soc 2 audit": "Module 5: SOC 2 Audit",
    "soc 2 compliance automation": "Module 6: SOC 2 Compliance Automation",
}

INSTRUCTION_RE = re.compile(
    r"^(choose (?:one|two|three|four|five|\d+) answers?|choose true or false|true / false|"
    r"assign a number to each step|single response|fill in the blank|question \d+ of \d+)$",
    re.I,
)


@dataclass
class Block:
    tag: str
    style: str = ""
    outline: str = ""
    text: str = ""
    table_rows: list[list[str]] = field(default_factory=list)


def para_text(el: ET.Element) -> str:
    chunks: list[str] = []
    for node in el.iter():
        if node.text:
            chunks.append(node.text)
        if node.tail:
            chunks.append(node.tail)
    return re.sub(r"\s+", " ", "".join(chunks)).strip()


def table_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    norm = [r + [""] * (width - len(r)) for r in rows]
    lines = [
        "| " + " | ".join(c.replace("|", "\\|") for c in norm[0]) + " |",
        "| " + " | ".join("---" for _ in norm[0]) + " |",
    ]
    for row in norm[1:]:
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in row) + " |")
    return "\n".join(lines)


def parse_odt(path: Path) -> list[Block]:
    with zipfile.ZipFile(path) as z:
        content = ET.fromstring(z.read("content.xml"))

    text_el = next(el for el in content.iter() if el.tag.endswith("}text"))
    blocks: list[Block] = []
    for child in text_el:
        tag = child.tag.split("}")[-1]
        if tag == "h":
            title = para_text(child)
            if not title:
                continue
            blocks.append(
                Block(
                    tag="h",
                    style=child.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", ""),
                    outline=child.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level", ""),
                    text=title,
                )
            )
        elif tag == "p":
            t = para_text(child)
            if t:
                blocks.append(
                    Block(
                        tag="p",
                        style=child.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", ""),
                        text=t,
                    )
                )
        elif tag == "table":
            rows: list[list[str]] = []
            for row in child.iter():
                if not row.tag.endswith("}table-row"):
                    continue
                cells = []
                for cell in row:
                    if not cell.tag.endswith("}table-cell"):
                        continue
                    parts = [para_text(p) for p in cell.iter() if p.tag.endswith("}p")]
                    cells.append(" ".join(p for p in parts if p).strip())
                if any(cells):
                    rows.append(cells)
            blocks.append(Block(tag="table", table_rows=rows))
    return blocks


def module_label(h2: str) -> str | None:
    return MODULE_MAP.get(h2.strip().lower())


def module_num(label: str) -> str:
    m = re.search(r"Module\s+(\d+)", label)
    return m.group(1) if m else "0"


def is_quiz_marker(text: str) -> bool:
    return text.strip().lower() == "quiz"


def is_instruction(text: str) -> bool:
    return bool(INSTRUCTION_RE.match(text.strip()))


def looks_like_question(text: str) -> bool:
    t = text.strip()
    if not t or is_instruction(t) or is_quiz_marker(t):
        return False
    if t.endswith("?"):
        return True
    if "______" in t:
        return True
    if re.search(r"\bwhich of the following\b", t, re.I):
        return True
    if re.search(r"\barrange the steps\b", t, re.I):
        return True
    if re.search(r"\btrue or false\b", t, re.I) and "?" not in t:
        return False
    return False


def looks_like_option(text: str, *, after_question: bool) -> bool:
    t = text.strip()
    if not after_question or not t:
        return False
    if is_instruction(t) or looks_like_question(t):
        return False
    if t.lower() in {"true", "false"}:
        return True
    if re.match(r"^[a-d][\).:\-]\s", t, re.I):
        return True
    if re.match(r"^\d+\s+\S", t):
        return True
    # Short answer options / fill-blank answers
    if len(t.split()) <= 6 and t[0].isupper() and "?" not in t:
        return True
    # Long policy-style distractors in Alison quizzes
    if after_question and not t.endswith("?"):
        return True
    return False


INTRO_MARKERS = (
    "SOC 2, or Service Organization",
    "SOC 2 is a compliance framework",
    "For an organization to become compliant",
)


def parse_quiz_lines(lines: list[str], *, title: str) -> str:
    """Turn flat Alison quiz paragraphs into numbered questions + option lists."""
    out = [f"# {title}", ""]
    q_num = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or is_quiz_marker(line):
            continue
        if is_instruction(line):
            continue

        # Look-ahead: stem then instruction on next line
        instruction: str | None = None
        if i < len(lines) and is_instruction(lines[i].strip()):
            instruction = lines[i].strip()
            i += 1

        q_num += 1
        out.extend(["", f"### Question {q_num}", ""])
        if instruction:
            out.append(f"*{instruction}*")
            out.append("")
        out.append(line)

        options: list[str] = []
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or is_quiz_marker(nxt):
                i += 1 if not nxt else 0
                break
            if is_instruction(nxt):
                break
            # Next question: ends with ? or blank-fill, or "which/arrange", or statement before choose-* 
            nxt_instruction = i + 1 < len(lines) and is_instruction(lines[i + 1].strip())
            if (
                nxt.endswith("?")
                or "______" in nxt
                or re.search(r"\bwhich of the following\b", nxt, re.I)
                or re.search(r"\barrange the steps\b", nxt, re.I)
                or nxt_instruction
            ):
                break
            if nxt.lower() in {"true", "false"}:
                options.append(f"- **{nxt.title()}**")
            elif re.match(r"^[a-d][\).:\-]\s", nxt, re.I):
                letter = nxt[0].upper()
                rest = nxt[2:].lstrip(").:- ")
                options.append(f"- **{letter}.** {rest}")
            else:
                options.append(f"- {nxt}")
            i += 1

        if options:
            out.append("")
            out.extend(options)

    return "\n".join(out).strip() + "\n"


def format_quiz_markdown(lines: list[str], *, title: str) -> str:
    return parse_quiz_lines(lines, title=title)


def body_from_buffer(buffer: list[str | Block]) -> str:
    parts: list[str] = []
    for item in buffer:
        if isinstance(item, str):
            parts.append(item)
        elif item.tag == "table":
            parts.append(table_to_markdown(item.table_rows))
    return "\n\n".join(p for p in parts if p).strip()


@dataclass
class LessonDraft:
    title: str
    category: str
    kind: str
    body: str


def build_lessons(blocks: list[Block]) -> list[LessonDraft]:
    lessons: list[LessonDraft] = []
    current_module: str | None = None
    module_intro: list[str | Block] = []
    section_title: str | None = None
    section_kind: str = "text"
    buffer: list[str | Block] = []

    def flush() -> None:
        nonlocal buffer, section_title, section_kind
        if not current_module or not section_title:
            buffer = []
            return
        if section_kind == "quiz":
            lines = [b if isinstance(b, str) else b.text for b in buffer]
            body = format_quiz_markdown(lines, title=section_title)
        else:
            body = body_from_buffer(buffer)
        if body.strip():
            lessons.append(
                LessonDraft(
                    title=section_title,
                    category=current_module,
                    kind=section_kind,
                    body=body,
                )
            )
        buffer = []

    def start_section(title: str, kind: str = "text") -> None:
        nonlocal section_title, section_kind, buffer
        flush()
        section_title = title
        section_kind = kind
        buffer = []

    for block in blocks:
        if block.tag == "h":
            lvl = int(block.outline or "1")
            title = block.text.strip()
            low = title.lower()

            if lvl == 2:
                flush()
                current_module = module_label(title)
                module_intro = []
                section_title = None
                continue

            if lvl == 3 and current_module:
                if low == "quiz":
                    start_section(f"Module {module_num(current_module)} Quiz", "quiz")
                    continue
                if low == "bibliography":
                    start_section("Bibliography", "text")
                    continue
                if low == "lesson summary":
                    start_section("Lesson Summary", "text")
                    continue
                if low == "learning outcomes":
                    start_section("Learning Outcomes", "text")
                    continue
                start_section(title, "text")
                continue

            if lvl >= 4 and section_title:
                buffer.append(f"## {title}")
                continue

        if not current_module:
            continue

        if block.tag == "p":
            if is_quiz_marker(block.text):
                start_section(f"Module {module_num(current_module)} Quiz", "quiz")
                continue

            if section_title is None:
                module_intro.append(block.text)
                continue

            if section_title == "Learning Outcomes" and any(
                block.text.startswith(m) for m in INTRO_MARKERS
            ):
                flush()
                start_section("Introduction to SOC 2", "text")
                buffer.append(block.text)
                continue

            buffer.append(block.text)
        elif block.tag == "table":
            if section_title is None:
                module_intro.append(block)
            else:
                buffer.append(block)

    flush()

    # Module intro paragraphs → prepend as Introduction lesson when not already added
    # (handled inline for module 1; other modules merge into first lesson if needed)
    return lessons


def merge_module_intros(lessons: list[LessonDraft], blocks: list[Block]) -> list[LessonDraft]:
    """Attach leading module paragraphs to first lesson when doc has no h3 yet."""
    # Second pass: module 2/3 intro paras before first h3
    out: list[LessonDraft] = []
    current_module: str | None = None
    pending_intro: list[str] = []

    block_idx = 0
    modules_order: list[str] = []
    for b in blocks:
        if b.tag == "h" and b.outline == "2" and module_label(b.text):
            modules_order.append(module_label(b.text) or "")

    intro_by_module: dict[str, list[str]] = {m: [] for m in modules_order if m}
    current = None
    seen_h3 = False
    for b in blocks:
        if b.tag == "h" and b.outline == "2":
            current = module_label(b.text)
            seen_h3 = False
            continue
        if b.tag == "h" and b.outline == "3" and current:
            seen_h3 = True
            continue
        if b.tag == "p" and current and not seen_h3:
            intro_by_module.setdefault(current, []).append(b.text)

    for lesson in lessons:
        if lesson.title == intro_by_module.get(lesson.category, []) and False:
            pass
        out.append(lesson)

    # Prepend intro to first lesson of each module if not Introduction to SOC 2
    first_seen: set[str] = set()
    final: list[LessonDraft] = []
    for lesson in lessons:
        mod = lesson.category
        if mod not in first_seen:
            first_seen.add(mod)
            intro = intro_by_module.get(mod, [])
            if intro and lesson.title != "Introduction to SOC 2":
                merged = "\n\n".join(intro + [lesson.body]).strip()
                final.append(
                    LessonDraft(
                        title=lesson.title,
                        category=lesson.category,
                        kind=lesson.kind,
                        body=merged,
                    )
                )
                intro_by_module[mod] = []
                continue
        final.append(lesson)
    return final


def post_process(lessons: list[LessonDraft], blocks: list[Block]) -> list[LessonDraft]:
    lessons = merge_module_intros(lessons, blocks)

    # Split Module 6: after Lesson Summary, remaining quiz → Course Review Quiz
    final: list[LessonDraft] = []
    review_lines: list[str] = []
    in_review = False
    for lesson in lessons:
        if lesson.category.startswith("Module 6") and lesson.title == "Lesson Summary":
            # body may contain trailing quiz — split on first question pattern
            lines = lesson.body.splitlines()
            summary_lines: list[str] = []
            for ln in lines:
                if looks_like_question(ln) or is_instruction(ln):
                    in_review = True
                if in_review:
                    review_lines.append(ln)
                else:
                    summary_lines.append(ln)
            body = "\n".join(summary_lines).strip()
            if body:
                final.append(
                    LessonDraft(
                        title=lesson.title,
                        category=lesson.category,
                        kind=lesson.kind,
                        body=body + "\n",
                    )
                )
            continue
        if in_review and lesson.kind == "quiz":
            review_lines.extend(lesson.body.splitlines())
            continue
        final.append(lesson)

    if review_lines:
        final.append(
            LessonDraft(
                title="Course Review Quiz",
                category="Module 6: SOC 2 Compliance Automation",
                kind="quiz",
                body=format_quiz_markdown(review_lines, title="Course Review Quiz"),
            )
        )
    return final


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "lesson"


def write_course(lessons: list[LessonDraft], *, dry_run: bool = False) -> dict:
    from datetime import datetime, timezone

    from app.services.library_course_paths import ROOT, ensure_course_data_dir, slugify_course_id

    cid = slugify_course_id(COURSE_ID)
    out_dir = ensure_course_data_dir(cid)
    pages_dir = out_dir / "pages"
    if not dry_run:
        pages_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for idx, lesson in enumerate(lessons, start=1):
        slug = slugify(f"{lesson.kind}-{lesson.title}")
        filename = f"{idx:03d}-{slug}.md"
        rel_file = f"data/{cid}/pages/{filename}"
        frontmatter = [
            f"- kind: {lesson.kind}",
            f"- title: {lesson.title}",
            f"- category: {lesson.category}",
            f"- course: {COURSE_NAME}",
            f"- course_id: {cid}",
            f"- order: {idx}",
            f"- url: {SOURCE_URL}",
            "- manual: true",
            f"- fetched_at: {now}",
        ]
        content = f"# {lesson.title}\n\n" + "\n".join(frontmatter) + "\n\n---\n\n" + lesson.body
        if not dry_run:
            (pages_dir / filename).write_text(content, encoding="utf-8")
        manifest.append(
            {
                "index": idx,
                "kind": lesson.kind,
                "label": lesson.title,
                "title": lesson.title,
                "category": lesson.category,
                "url": SOURCE_URL,
                "file": rel_file,
                "chars": len(lesson.body),
                "ok": True,
            }
        )

    if not dry_run:
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"course_id": cid, "lessons": len(manifest)}


def ensure_source(*, dry_run: bool = False) -> str | None:
    from sqlalchemy import select

    from app.models.source import Platform, Source, SourcePriority, SourceStatus, SourceType
    from app.services.catalog_ids import _next_number_sync, catalog_prefix, format_catalog_id
    from app.services.library_course_paths import course_id_tag
    from db import session_scope

    with session_scope() as session:
        row = session.scalar(
            select(Source).where(
                Source.domain == "courses",
                Source.source_url == SOURCE_URL.rstrip("/"),
            )
        )
        if row:
            row.name = COURSE_NAME
            row.connector = "manual"
            row.category = "course"
            row.tags = [course_id_tag(COURSE_ID)]
            if not dry_run:
                session.commit()
            return str(row.id)

        if dry_run:
            return None

        prefix = catalog_prefix("courses")
        n = _next_number_sync(session, "courses", prefix)
        source = Source(
            domain="courses",
            catalog_id=format_catalog_id(prefix, n),
            platform=Platform.website,
            source_type=SourceType.website,
            source_url=SOURCE_URL.rstrip("/"),
            name=COURSE_NAME,
            description="Alison free course — manual import from curated ODT",
            category="course",
            tags=[course_id_tag(COURSE_ID)],
            priority=SourcePriority.normal,
            autorun=False,
            auto_transcribe=False,
            status=SourceStatus.active,
            connector="manual",
        )
        session.add(source)
        session.flush()
        sid = str(source.id)
        session.commit()
        return sid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--odt", type=Path, default=ODT_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--outline", action="store_true")
    args = parser.parse_args()

    blocks = parse_odt(args.odt)
    lessons = post_process(build_lessons(blocks), blocks)

    if args.outline:
        from collections import Counter

        for i, l in enumerate(lessons, 1):
            print(f"{i:3} [{l.kind:4}] {l.category} :: {l.title} ({len(l.body)} chars)")
        print("TOTAL", len(lessons), Counter(l.kind for l in lessons))
        return

    result = write_course(lessons, dry_run=args.dry_run)
    print("WROTE", result["course_id"], result["lessons"], "lessons")
    if args.dry_run:
        return

    source_id = ensure_source()
    if source_id:
        from db import session_scope
        from app.services.library_source_lessons import sync_lessons_from_disk

        with session_scope() as session:
            synced = sync_lessons_from_disk(session, source_id=source_id, course_id=result["course_id"])
            session.commit()
        print("SOURCE", source_id, "DB_SYNCED", synced)


if __name__ == "__main__":
    main()
