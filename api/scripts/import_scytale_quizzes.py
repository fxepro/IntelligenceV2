"""
Import Module 1–9 quizzes + Final Exam from the Scytale quiz export TXT
into canonical scytale-soc2 quiz lesson markdown files.

Also writes Table of Contents into the manual TOC lesson.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
QUIZ_SRC = V2 / "docs" / "Domains" / "Courses" / "SOC2" / "SOC 2- Scytale.txt"
TOC_SRC = V2 / "docs" / "Domains" / "Courses" / "SOC2" / "Scytale Table of Contents.txt"
PAGES = V2 / "data" / "scytale-soc2" / "pages"
TOC_OUT = (
    V2 / "data" / "library" / "manual" / "soc-2-compliance" / "pages" / "000-table-of-contents.md"
)

TARGET_FILES = {
    "Module 1": PAGES / "010-quiz-34831709-module-1-quiz.md",
    "Module 2": PAGES / "019-quiz-34850988-module-2-quiz.md",
    "Module 3": PAGES / "035-quiz-34857641-module-3-quiz.md",
    "Module 4": PAGES / "040-quiz-34857889-module-4-quiz.md",
    "Module 5": PAGES / "058-quiz-34858537-module-5-quiz.md",
    "Module 6": PAGES / "065-quiz-34859139-module-6-quiz.md",
    "Module 7": PAGES / "070-quiz-34859230-module-7-quiz.md",
    "Module 8": PAGES / "076-quiz-34859511-module-8-quiz.md",
    "Module 9": PAGES / "086-quiz-34859617-module-9-quiz.md",
    "Final Exam": PAGES / "088-quiz-34819712-soc-2-academy-final-exam.md",
}

SECTION_RE = re.compile(r"(?m)^(Module\s+[1-9]|Final Exam)\s*$")
QUESTION_HEAD_RE = re.compile(r"(?mi)^Question\s+\d+\s+of\s+\d+\s*$")
CHOOSE_RE = re.compile(r"(?mi)^Choose only ONE best answer\.\s*$")
NOISE_RE = re.compile(r"(?mi)^(This answer is correct\.|Correct\.|Incorrect\.)\s*$")


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _split_sections(src: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(src))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        key = re.sub(r"\s+", " ", m.group(1)).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(src)
        if key not in sections:
            sections[key] = src[start:end].strip()
    return sections


def _as_choice_line(s: str, expect: str | None) -> tuple[str, str] | None:
    """
    Return (letter, inline_rest) if this line starts choice `expect`.

    Exact 'A' / 'B' / … counts when letter == expect.
    Inline 'A Every month' counts only for the expected letter and short rest.
    When expect is None (past D), never treat a line as a new choice — option
    text like 'A & C' must stay on the previous choice.
    """
    s = (s or "").strip()
    if not s or expect is None:
        return None
    if len(s) == 1 and s in "ABCD":
        if s != expect:
            return None
        return s, ""
    m = re.match(r"^([A-D])\s+(.+)$", s)
    if not m:
        return None
    letter, inline = m.group(1), m.group(2).strip()
    if letter != expect:
        return None
    if len(inline) > 120:
        return None
    return letter, inline


def _parse_choice_block(lines: list[str], start: int) -> tuple[list[tuple[str, str]], int]:
    """Parse A–D choices starting at `start`. Returns (choices, next_index)."""
    choices: list[tuple[str, str]] = []
    i = start
    expect = "A"
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if choices and j < len(lines) and not _as_choice_line(lines[j].strip(), expect):
                return choices, j
            continue
        if NOISE_RE.match(s):
            i += 1
            continue
        parsed = _as_choice_line(s, expect)
        if not parsed:
            return choices, i
        letter, inline = parsed
        i += 1
        parts: list[str] = []
        if inline:
            parts.append(inline)
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                i += 1
                break
            if NOISE_RE.match(nxt):
                i += 1
                continue
            nxt_expect = chr(ord(letter) + 1) if letter < "D" else None
            if _as_choice_line(nxt, nxt_expect) or QUESTION_HEAD_RE.match(nxt):
                break
            parts.append(nxt)
            i += 1
        text = " ".join(parts).strip()
        if text:
            choices.append((letter, text))
        if letter >= "D":
            while i < len(lines) and (
                not lines[i].strip() or NOISE_RE.match(lines[i].strip())
            ):
                i += 1
            return choices, i
        expect = chr(ord(letter) + 1)
    return choices, i


def _clean_question_text(text: str) -> str:
    lines: list[str] = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if QUESTION_HEAD_RE.match(s) or CHOOSE_RE.match(s) or NOISE_RE.match(s):
            continue
        lines.append(s)
    return " ".join(lines).strip()


def _parse_questions(block: str) -> list[dict]:
    parts = CHOOSE_RE.split(block)
    if len(parts) < 2:
        return []

    questions: list[dict] = []
    pending_q = _clean_question_text(parts[0])

    for part in parts[1:]:
        lines = part.splitlines()
        i = 0
        while i < len(lines) and not lines[i].strip():
            i += 1
        choices, i = _parse_choice_block(lines, i)
        rest = "\n".join(lines[i:])
        if pending_q and len(choices) >= 2:
            questions.append({"text": pending_q, "choices": choices})
        pending_q = _clean_question_text(rest)

    # Drop consecutive duplicates (source Final Exam repeats Question 23).
    deduped: list[dict] = []
    for q in questions:
        if deduped and deduped[-1]["text"] == q["text"] and deduped[-1]["choices"] == q["choices"]:
            continue
        deduped.append(q)

    total = len(deduped)
    return [
        {"n": i + 1, "total": total, "text": q["text"], "choices": q["choices"]}
        for i, q in enumerate(deduped)
    ]


def _format_body(title: str, questions: list[dict]) -> str:
    lines = [f"# {title}", ""]
    for q in questions:
        lines.append(f"### Question {q['n']} of {q['total']}")
        lines.append("")
        lines.append(q["text"])
        lines.append("")
        for letter, opt in q["choices"]:
            lines.append(f"- **{letter}.** {opt}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _upsert_body(path: Path, title: str, body: str) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if "\n---\n" in raw:
        header, _ = raw.split("\n---\n", 1)
    else:
        header = f"# {title}\n\n- kind: quiz\n- title: {title}\n"
    # Fix mojibake in labels if present
    header = header.replace("Quiz A� PREREQUISITE", "Quiz · PREREQUISITE")
    header = header.replace("Quiz Ã‚Â· PREREQUISITE", "Quiz · PREREQUISITE")
    if "- title:" not in header:
        header = header.rstrip() + f"\n- title: {title}\n"
    else:
        header = re.sub(r"(?m)^- title:.*$", f"- title: {title}", header)
    if "- kind:" not in header:
        header = header.rstrip() + "\n- kind: quiz\n"
    hlines = header.splitlines()
    if hlines and hlines[0].startswith("# "):
        hlines[0] = f"# {title}"
        header = "\n".join(hlines)
    fetched = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if "- fetched_at:" in header:
        header = re.sub(r"(?m)^- fetched_at:.*$", f"- fetched_at: {fetched}", header)
    else:
        header = header.rstrip() + f"\n- fetched_at: {fetched}\n"
    path.write_text(f"{header.rstrip()}\n\n---\n\n{body.rstrip()}\n", encoding="utf-8")


def _format_toc(raw: str) -> str:
    lines_out = ["# Table of Contents", ""]
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s in ("SOC 2 Academy", "100% complete"):
            continue
        if s in ("Overview", "Glossary", "Final Exam") or (
            s.startswith("Module ") and ":" in s and "Quiz" not in s
        ):
            lines_out += ["", f"## {s}", ""]
            continue
        if (s.startswith("Module ") and "Quiz" in s) or s.startswith("SOC 2 Academy Final Exam"):
            lines_out.append(f"- **{s}**")
            continue
        lines_out.append(f"- {s}")
    return "\n".join(lines_out).rstrip() + "\n"


def main() -> None:
    src = _read_text(QUIZ_SRC)
    sections = _split_sections(src)
    print("Sections found:", ", ".join(sections.keys()))

    for key, path in TARGET_FILES.items():
        block = sections.get(key)
        if not block:
            print(f"MISSING section: {key}")
            continue
        questions = _parse_questions(block)
        title = "SOC 2 Academy Final Exam" if key == "Final Exam" else f"{key} Quiz"
        if not questions:
            print(f"NO QUESTIONS: {key}")
            continue
        bad = [q["n"] for q in questions if len(q["choices"]) < 2]
        if bad:
            print(f"WARN {key}: thin choices on Q {bad}")
        body = _format_body(title, questions)
        if not path.is_file():
            print(f"FILE MISSING: {path}")
            continue
        _upsert_body(path, title, body)
        print(f"Wrote {key}: {len(questions)} questions -> {path.name}")

    toc_body = _format_toc(_read_text(TOC_SRC))
    fetched = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # First Scytale slot (formerly Preface) — visible to the live catalog immediately.
    pages_toc = PAGES / "001-text-34238780-preface.md"
    pages_toc.write_text(
        f"""# Table of Contents

- title: Table of Contents
- course: SOC 2 Compliance
- kind: text
- category: Overview
- label: Table of Contents
- url: https://academy.scytale.ai/courses/take/scytale-SOC-2-academy/texts/34238780-preface
- locked: false
- fetched_at: {fetched}

---

{toc_body}""",
        encoding="utf-8",
    )
    print(f"Wrote TOC lesson -> {pages_toc}")

    TOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    TOC_OUT.write_text(
        f"""# Table of Contents

- kind: text
- title: Table of Contents
- category: Overview
- course: SOC 2 Compliance
- order: 0
- manual: true
- fetched_at: {fetched}

---

{toc_body}""",
        encoding="utf-8",
    )
    print(f"Wrote TOC manual copy -> {TOC_OUT}")

    manifest_path = V2 / "data" / "scytale-soc2" / "manifest.json"
    if manifest_path.is_file():
        import json

        rows = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in rows:
            if str(row.get("file") or "").endswith("001-text-34238780-preface.md"):
                row["label"] = "Table of Contents"
                row["title"] = "Table of Contents"
                row["chars"] = len(toc_body)
                break
        manifest_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print("Updated manifest Preface slot → Table of Contents")


if __name__ == "__main__":
    main()
