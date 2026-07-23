"""
Build government_sources.seed.json from the Gov catalog CSV.

Mapped fields only (see product mapping). Run from v2/api:

  python scripts/build_government_seed.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # v2/
CSV_PATH = ROOT / "docs" / "Domains" / "Government_Intelligence_Source_Catalog_Upload.csv"
OUT_PATH = ROOT / "docs" / "Domains" / "government_sources.seed.json"

PRIORITY_MAP = {
    "P1": "urgent",
    "P2": "high",
    "P3": "normal",
}


def _slug_tag(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def map_priority(raw: str) -> str:
    key = (raw or "").strip().upper()
    if key in PRIORITY_MAP:
        return PRIORITY_MAP[key]
    # P4, P5, …
    if key.startswith("P") and key[1:].isdigit() and int(key[1:]) >= 4:
        return "low"
    return "normal"


def map_platform_and_type(access_method: str) -> tuple[str, str]:
    am = (access_method or "").lower()
    if "rss" in am and "api" not in am.split("rss")[0]:
        # "HTML / RSS", "RSS"
        if "rss" in am:
            return "rss", "rss_feed"
    if re.search(r"\brss\b", am):
        return "rss", "rss_feed"
    # REST / bulk / portal / API → website spine for now
    return "website", "sitemap"


def build_description(notes: str, data_available: str) -> str | None:
    notes = (notes or "").strip()
    data = (data_available or "").strip()
    if notes and data:
        text = f"{notes} — {data}"
    else:
        text = notes or data
    if not text:
        return None
    # Short text only
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1000] if len(text) > 1000 else text


def build_secondary_tags(secondary: str) -> list[str]:
    tags: list[str] = []
    for part in re.split(r"[,;|/]", secondary or ""):
        sec = _slug_tag(part)
        if sec:
            tags.append(f"secondary:{sec}")
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def row_to_seed(row: dict) -> dict | None:
    catalog_id = (row.get("Source ID") or "").strip().upper()
    name = (row.get("Source Name") or "").strip()
    url = (row.get("Access Link") or "").strip().rstrip("/")
    if not catalog_id or not name or not url:
        return None
    platform, source_type = map_platform_and_type(row.get("Access Method") or "")
    category = _slug_tag(row.get("Category") or "") or None
    return {
        "catalog_id": catalog_id,
        "domain": "government",
        "name": name[:512],
        "source_url": url[:2048],
        "priority": map_priority(row.get("Priority") or ""),
        "description": build_description(
            row.get("Notes") or "",
            row.get("Data Available") or "",
        ),
        "category": category,
        "tags": build_secondary_tags(row.get("Secondary Domains") or ""),
        "platform": platform,
        "source_type": source_type,
        "status": "active",
        "autorun": False,
        "auto_transcribe": False,
    }


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"CSV not found: {CSV_PATH}")
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    seeds = []
    seen_urls: set[str] = set()
    for row in rows:
        item = row_to_seed(row)
        if not item:
            continue
        key = item["source_url"].lower()
        if key in seen_urls:
            print(f"skip duplicate url {item['catalog_id']}: {item['source_url']}")
            continue
        seen_urls.add(key)
        seeds.append(item)

    payload = {
        "domain": "government",
        "version": 1,
        "source": str(CSV_PATH.relative_to(ROOT)).replace("\\", "/"),
        "count": len(seeds),
        "items": seeds,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(seeds)} items -> {OUT_PATH}")


if __name__ == "__main__":
    main()
