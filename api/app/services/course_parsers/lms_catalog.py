"""LMS catalog parsers — Coursera, Udemy (public syllabus; auth for full content)."""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.course_parsers.types import CourseLesson

LOGIN_MARKERS = (
    "log in",
    "sign in",
    "sign up",
    "enroll",
    "subscribe",
    "start free trial",
    "join for free",
)


def _looks_login_gated(html: str) -> bool:
    low = (html or "").lower()
    if "coursereader" in low and "syllabus" not in low and "module" not in low:
        return True
    hits = sum(1 for m in LOGIN_MARKERS if m in low)
    return hits >= 3 and "week" not in low[:8000]


def _lessons_from_json_ld(html: str, *, id_prefix: str, default_category: str) -> list[CourseLesson]:
    soup = BeautifulSoup(html, "html.parser")
    lessons: list[CourseLesson] = []
    idx = 0
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text() or "")
        except json.JSONDecodeError:
            continue
        blocks = data if isinstance(data, list) else [data]
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("@type") not in ("Course", "LearningResource", "ItemList"):
                continue
            parts = block.get("hasPart") or block.get("itemListElement") or []
            if isinstance(parts, dict):
                parts = [parts]
            for part in parts:
                if isinstance(part, dict) and "item" in part:
                    part = part["item"]
                if not isinstance(part, dict):
                    continue
                name = str(part.get("name") or part.get("title") or "").strip()
                url = str(part.get("url") or part.get("@id") or "").strip()
                if not name:
                    continue
                idx += 1
                lessons.append(
                    CourseLesson(
                        id=f"{id_prefix}-lms-{idx:03d}",
                        title=name[:256],
                        category=default_category,
                        kind="video" if "video" in str(part.get("@type", "")).lower() else "text",
                        has_video="video" in str(part.get("@type", "")).lower(),
                        url=url or None,
                        video_url=url if url and "youtube" in url else None,
                        order_index=idx,
                    )
                )
    return lessons


def _lessons_from_syllabus_dom(html: str, *, base_url: str, id_prefix: str) -> list[CourseLesson]:
    soup = BeautifulSoup(html, "html.parser")
    lessons: list[CourseLesson] = []
    idx = 0
    current_week = "Module 1"

    # Coursera-ish: week headings + item titles
    for el in soup.find_all(["h2", "h3", "h4", "span", "a", "button"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if re.match(r"^(week|module|section)\s+\d+", text, re.I):
            current_week = text[:128]
            continue
        if len(text) < 4 or len(text) > 200:
            continue
        if any(x in text.lower() for x in LOGIN_MARKERS):
            continue
        # Udemy curriculum lines often in accordion
        if el.name in ("a", "button", "span") and re.search(
            r"(video|reading|quiz|assignment|lecture|min)", text, re.I
        ):
            idx += 1
            href = el.get("href") if el.name == "a" else None
            url = urljoin(base_url, href) if href else None
            lessons.append(
                CourseLesson(
                    id=f"{id_prefix}-syll-{idx:03d}",
                    title=text[:256],
                    category=current_week,
                    kind="video" if re.search(r"video|lecture|min", text, re.I) else "text",
                    has_video=bool(re.search(r"video|lecture", text, re.I)),
                    url=url,
                    order_index=idx,
                )
            )
    return lessons


def parse_coursera_catalog_html(html: str, *, url: str, id_prefix: str = "coursera") -> tuple[list[CourseLesson], list[str]]:
    anomalies: list[str] = []
    if _looks_login_gated(html) and "syllabus" not in html.lower():
        anomalies.append("ACCESS_LOGIN_REQUIRED")

    lessons = _lessons_from_json_ld(html, id_prefix=id_prefix, default_category="Week")
    if not lessons:
        lessons = _lessons_from_syllabus_dom(html, base_url=url, id_prefix=id_prefix)

    if not lessons:
        anomalies.append("COURSE_NO_LESSONS")
        if "coursera.org" in url:
            anomalies.append("COURSE_AUTH_REQUIRED")
    return lessons, anomalies


def parse_udemy_catalog_html(html: str, *, url: str, id_prefix: str = "udemy") -> tuple[list[CourseLesson], list[str]]:
    anomalies: list[str] = []
    low = html.lower()
    if "udemy" in low and ("curriculum" not in low and "syllabus" not in low and "lecture" not in low):
        anomalies.append("ACCESS_LOGIN_REQUIRED")

    lessons = _lessons_from_json_ld(html, id_prefix=id_prefix, default_category="Section")
    if not lessons:
        lessons = _lessons_from_syllabus_dom(html, base_url=url, id_prefix=id_prefix)

    if not lessons:
        anomalies.append("COURSE_NO_LESSONS")
        anomalies.append("COURSE_AUTH_REQUIRED")
    return lessons, anomalies
