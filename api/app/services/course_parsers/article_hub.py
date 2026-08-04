"""Article hub — index page linking to child articles."""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup, Tag

from app.services.course_parsers.types import CourseLesson
from app.services.library_lesson_metadata import split_hub_label


def normalize_hub_url(url: str, path_prefix: str) -> str:
    raw = (url or "").split("#")[0].split("?")[0].rstrip("/")
    if not raw:
        return ""
    parsed = urlparse(raw)
    path = parsed.path or ""
    if path_prefix and not path.startswith(path_prefix):
        return ""
    hub = path_prefix.rstrip("/")
    if path.rstrip("/") == hub:
        return ""
    return urlunparse((parsed.scheme or "https", parsed.netloc, path.rstrip("/"), "", "", ""))


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1] or "item"
    return re.sub(r"[^\w\-]+", "-", name).strip("-").lower()[:120] or "item"


def _title_from_link(text: str, url: str) -> str:
    t = (text or "").strip()
    if len(t) >= 3:
        return t[:256]
    slug = _slug_from_url(url).replace("-", " ").strip()
    return slug[:1].upper() + slug[1:] if slug else "Untitled"


def _links_from_next_data(html: str, hub_url: str, path_prefix: str) -> list[tuple[str, str, str]]:
    """Pull article URLs from Next.js __NEXT_DATA__ when DOM is sparse."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []

    found: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def walk(node, category: str = "General"):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("href", "url", "slug", "path") and isinstance(v, str):
                    full = v if v.startswith("http") else urljoin(hub_url, v)
                    norm = normalize_hub_url(full, path_prefix)
                    if norm and norm not in seen:
                        seen.add(norm)
                        title = str(node.get("title") or node.get("name") or node.get("label") or "")
                        cat = str(node.get("category") or node.get("topic") or category)
                        found.append((cat, _title_from_link(title, norm), norm))
                walk(v, category)
        elif isinstance(node, list):
            for item in node:
                walk(item, category)

    walk(data)
    return found


def parse_article_hub_html(
    html: str,
    *,
    hub_url: str,
    path_prefix: str | None = None,
    id_prefix: str = "hub",
) -> tuple[list[CourseLesson], str | None]:
    prefix = path_prefix or urlparse(hub_url).path.rstrip("/") or "/"
    soup = BeautifulSoup(html, "html.parser")
    course_title = None
    h1 = soup.find("h1")
    if h1:
        course_title = h1.get_text(" ", strip=True)

    current_category = "General"
    seen: set[str] = set()
    ordered: list[tuple[str, str, str]] = []

    # Headings + card links
    for el in soup.find_all(["h2", "h3", "a"]):
        if el.name in ("h2", "h3"):
            text = el.get_text(" ", strip=True)
            if text and len(text) < 120:
                current_category = text
            continue
        if el.name != "a":
            continue
        href = el.get("href")
        if not href:
            continue
        absolute = urljoin(hub_url, href)
        norm = normalize_hub_url(absolute, prefix)
        if not norm or norm in seen:
            continue
        title_raw = el.get_text(" ", strip=True)
        section, title_part = split_hub_label(title_raw)
        if section:
            current_category = section
            title = _title_from_link(title_part, norm)
        else:
            title = _title_from_link(title_raw, norm)
        seen.add(norm)
        ordered.append((current_category, title, norm))

    for cat, title, link in _links_from_next_data(html, hub_url, prefix):
        if link not in seen:
            seen.add(link)
            section, title_part = split_hub_label(title)
            ordered.append((section or cat, _title_from_link(title_part or title, link), link))

    lessons: list[CourseLesson] = []
    for i, (category, title, link) in enumerate(ordered, start=1):
        slug = _slug_from_url(link)
        lessons.append(
            CourseLesson(
                id=f"{id_prefix}-art-{i:03d}-{slug}"[:140],
                title=title,
                category=category,
                kind="text",
                has_video=False,
                url=link,
                video_url=None,
                description=f"Article: {title}",
                order_index=i,
            )
        )
    return lessons, course_title
