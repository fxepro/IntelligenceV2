"""Standard lesson metadata: category = module/section, title = lesson name only."""
from __future__ import annotations

import re

# Article-hub section names (Drata hub + generic). Longest first for prefix match.
ARTICLE_HUB_SECTIONS: tuple[str, ...] = (
    "Reporting and Documentation",
    "Additional Resources",
    "Explore SOC 2 Topics",
    "Featured Articles",
    "Getting Started",
    "Best Practices",
    "Linked articles",
)


def looks_like_section(name: str) -> bool:
    """True when value is a module/section bucket — not an article title."""
    n = (name or "").strip()
    if not n or n.lower() in ("general", ""):
        return False
    if len(n) > 64:
        return False
    low = n.lower()
    if low in ("overview", "glossary", "final exam"):
        return True
    if re.match(r"^module\s+\d+\b", low):
        return True
    if any(low == sec.lower() for sec in ARTICLE_HUB_SECTIONS):
        return True
    # Article titles wrongly stored as category (long, guide/checklist/compliance words).
    if len(n) > 36:
        return False
    if any(w in low for w in ("checklist", "compliance", "audit firm", "bridge letter", "certification")):
        return False
    return len(n.split()) <= 4


def split_hub_label(label: str) -> tuple[str | None, str]:
    """
    Drata hub cards embed section + title in one string:
    'Best Practices How to Choose the Right SOC 2 Audit Firm …'
    """
    text = (label or "").strip()
    if not text:
        return None, ""
    for section in sorted(ARTICLE_HUB_SECTIONS, key=len, reverse=True):
        if text.lower().startswith(section.lower() + " "):
            return section, text[len(section) :].strip()
        if text.lower() == section.lower():
            return section, text
    return None, text


def normalize_lesson_title_category(
    *,
    row: dict,
    meta: dict | None = None,
    file_rel: str = "",
) -> tuple[str, str]:
    """
    Single spine for sync + display.

    - Scytale (no section on disk): derive Module N / Overview from label + URL.
    - Article hub (Drata): section prefix in label, or valid manifest category.
    """
    from app.services.library_catalog import _category_from_label, _clean_title

    meta = meta or {}
    file_rel_norm = (file_rel or "").replace("\\", "/")
    label = str(row.get("label") or meta.get("label") or "")
    url = str(row.get("url") or meta.get("url") or "")
    raw_title = str(row.get("title") or label or "Untitled")
    raw_category = str(row.get("category") or meta.get("category") or "").strip()

    is_scytale = "scytale-soc2" in file_rel_norm
    section_from_label, title_part = split_hub_label(label)

    if is_scytale:
        if "soc 2 academy" in raw_title.lower() and label:
            raw_title = label
        title = _clean_title(label or raw_title, url=url, fallback=raw_title)
        if looks_like_section(raw_category):
            category = raw_category
        else:
            category = _category_from_label(label, title, url=url)
        return title[:1024], category[:256]

    # Article hub / Drata / generic hubs
    if section_from_label:
        category = section_from_label
        title = _clean_title(title_part or raw_title, url=url, fallback=title_part or raw_title)
    elif looks_like_section(raw_category):
        category = raw_category
        title = _clean_title(label or raw_title, url=url, fallback=raw_title)
    else:
        category = raw_category or "General"
        if not looks_like_section(category):
            category = "Explore SOC 2 Topics"
        title = _clean_title(label or raw_title, url=url, fallback=raw_title)

    return title[:1024], category[:256]
