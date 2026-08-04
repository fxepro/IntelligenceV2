"""One-off: outline Alison ODT for import planning."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ODT = Path(__file__).resolve().parents[2] / "docs/Domains/Courses/SOC2/Essentials of the SOC 2 Cybersecurity Framework - Alison.odt"


def para_text(el: ET.Element) -> str:
    chunks: list[str] = []
    for node in el.iter():
        if node.text:
            chunks.append(node.text)
        if node.tail:
            chunks.append(node.tail)
    return "".join(chunks).strip()


def main() -> None:
    with zipfile.ZipFile(ODT) as z:
        content = ET.fromstring(z.read("content.xml"))

    items: list[dict] = []
    for el in content.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ("h", "p"):
            continue
        style = el.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", "")
        outline = el.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level", "")
        txt = para_text(el)
        if txt:
            items.append({"tag": tag, "style": style, "outline": outline, "text": txt})

    headings = [it for it in items if it["tag"] == "h"]
    print("HEADINGS", len(headings))
    for it in headings:
        lvl = int(it["outline"] or 1)
        print("  " * (lvl - 1) + f"[{lvl}] {it['text']}")

    modules = [
        it for it in headings if it["outline"] == "2" and it["style"] in ("P4", "P6")
    ]
    print("\nMODULES", len(modules))
    for m in modules:
        print("-", m["text"])

    quizzes = [it for it in headings if it["text"].strip() == "Quiz"]
    print("QUIZZES", len(quizzes))


if __name__ == "__main__":
    main()
