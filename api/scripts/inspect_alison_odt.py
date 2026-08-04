"""Inspect Alison ODT structure for import."""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ODT = Path(__file__).resolve().parents[2] / "docs/Domains/Courses/SOC2/Essentials of the SOC 2 Cybersecurity Framework - Alison.odt"
NS = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0", "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0"}


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

    body = content.find("text:body", NS)
    if body is None:
        print("no body")
        return

    idx = 0
    for child in body:
        tag = child.tag.split("}")[-1]
        if tag == "h":
            outline = child.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level", "?")
            style = child.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", "")
            print(f"H{outline} [{style}] {para_text(child)[:100]}")
        elif tag == "p":
            style = child.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", "")
            t = para_text(child)
            if t:
                print(f"  P [{style}] {t[:90]}")
        elif tag == "table":
            rows = child.findall(".//table:table-row", NS)
            print(f"TABLE rows={len(rows)}")
            for ri, row in enumerate(rows[:8]):
                cells = row.findall("table:table-cell", NS)
                vals = []
                for cell in cells:
                    ps = cell.findall(".//text:p", NS)
                    vals.append(" | ".join(para_text(p) for p in ps if para_text(p)))
                print(f"  R{ri}: {' || '.join(vals)[:120]}")
            if len(rows) > 8:
                print(f"  ... +{len(rows)-8} rows")
        idx += 1


if __name__ == "__main__":
    main()
