"""Video curriculum — sections (h3) + YouTube lesson links; playlist via yt-dlp."""
from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, urljoin, urlparse

import yt_dlp
from bs4 import BeautifulSoup, Tag

from app.services.course_parsers.types import CourseLesson
from app.services.discover_media import _entries, _ydl_opts

DURATION_RE = re.compile(r"^(.*?)\s*\((\d{1,2}):(\d{2})\)\s*$")
YOUTUBE_HOSTS = ("youtube.com", "youtu.be")


def parse_duration(text: str) -> tuple[str, int | None]:
    match = DURATION_RE.match((text or "").strip())
    if not match:
        return (text or "").strip(), None
    title = match.group(1).strip()
    seconds = int(match.group(2)) * 60 + int(match.group(3))
    return title, seconds


def _is_youtube(href: str) -> bool:
    low = (href or "").lower()
    return any(h in low for h in YOUTUBE_HOSTS)


def _lesson_id(prefix: str, n: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", prefix.lower()).strip("-")[:40] or "course"
    return f"{slug}-yt-{n:03d}"


_PLAYLIST_ID_PREFIXES = ("PL", "UU", "FL", "RD", "OL", "LL")


def is_youtube_playlist_url(url: str) -> bool:
    """True when URL targets a YouTube playlist (not a lone watch link)."""
    u = (url or "").strip().lower()
    if "youtube.com/playlist" in u:
        return True
    if "youtube.com" not in u and "youtu.be" not in u:
        return False
    parsed = urlparse(url)
    list_ids = parse_qs(parsed.query).get("list") or []
    for list_id in list_ids:
        if list_id and list_id.startswith(_PLAYLIST_ID_PREFIXES):
            return True
    return False


def parse_youtube_playlist_ytdlp(
    url: str,
    *,
    id_prefix: str = "course",
) -> tuple[list[CourseLesson], str | None]:
    """Extract every video in a YouTube playlist via yt-dlp (flat, no download)."""
    opts = _ydl_opts(url, extract_flat="in_playlist")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return [], None

    course_title = info.get("title")
    lessons: list[CourseLesson] = []
    for i, entry in enumerate(_entries(info), 1):
        vid = entry.get("id")
        title = (entry.get("title") or f"Lesson {i}").strip()
        watch = entry.get("url") or entry.get("webpage_url")
        if not watch and vid:
            watch = f"https://www.youtube.com/watch?v={vid}"
        if not watch:
            continue
        duration = entry.get("duration")
        duration_seconds = int(duration) if isinstance(duration, (int, float)) and duration > 0 else None
        lessons.append(
            CourseLesson(
                id=_lesson_id(id_prefix, i),
                title=title[:256],
                category="Playlist",
                kind="video",
                has_video=True,
                video_url=watch,
                url=watch,
                order_index=i,
                duration_seconds=duration_seconds,
            )
        )
    return lessons, course_title


def parse_youtube_curriculum_html(
    html: str,
    *,
    url: str,
    id_prefix: str = "course",
) -> tuple[list[CourseLesson], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    course_title = None
    h1 = soup.find("h1")
    if h1:
        course_title = h1.get_text(" ", strip=True)

    curriculum_heading = None
    for heading in soup.find_all(["h1", "h2"]):
        if "course curriculum" in heading.get_text(" ", strip=True).lower():
            curriculum_heading = heading
            break
        if "curriculum" in heading.get_text(" ", strip=True).lower() and curriculum_heading is None:
            curriculum_heading = heading

    if curriculum_heading is None:
        # Fallback: any page with h3 + youtube links
        return _parse_youtube_sections_fallback(soup, url=url, id_prefix=id_prefix, course_title=course_title)

    lessons: list[CourseLesson] = []
    current_section: str | None = None
    overall = 0
    skip_sections = {"soc 2 course", "sign up", "signup", "register"}

    for element in curriculum_heading.find_all_next():
        if not isinstance(element, Tag):
            continue
        if element.name == "h2" and element is not curriculum_heading:
            break
        if element.name == "h3":
            section_title = element.get_text(" ", strip=True)
            if section_title.lower() in skip_sections:
                current_section = None
                continue
            current_section = section_title
            continue
        if element.name != "a" or not current_section:
            continue
        href = element.get("href")
        text = element.get_text(" ", strip=True)
        if not href or not text:
            continue
        absolute = urljoin(url, href)
        if not _is_youtube(absolute):
            continue
        title, duration = parse_duration(text)
        overall += 1
        lessons.append(
            CourseLesson(
                id=_lesson_id(id_prefix, overall),
                title=title[:256],
                category=current_section,
                kind="video",
                has_video=True,
                video_url=absolute,
                url=absolute,
                order_index=overall,
                duration_seconds=duration,
            )
        )

    if not lessons:
        return _parse_youtube_sections_fallback(soup, url=url, id_prefix=id_prefix, course_title=course_title)
    return lessons, course_title


def _parse_youtube_sections_fallback(
    soup: BeautifulSoup,
    *,
    url: str,
    id_prefix: str,
    course_title: str | None,
) -> tuple[list[CourseLesson], str | None]:
    """Looser pass: collect youtube anchors grouped by nearest preceding h2/h3."""
    lessons: list[CourseLesson] = []
    headings = soup.find_all(["h2", "h3"])
    for h in headings:
        title = h.get_text(" ", strip=True)
        if not title or "curriculum" in title.lower():
            continue
        for a in h.find_all_next("a", href=True):
            if a.find_previous(["h2", "h3"]) is not h:
                break
            overall = _append_youtube(a, url, title[:128], id_prefix, lessons, len(lessons))
    if not lessons:
        overall = _parse_youtube_iframes(soup, url=url, id_prefix=id_prefix, lessons=lessons, overall=0)
        for a in soup.find_all("a", href=True):
            overall = _append_youtube(a, url, "General", id_prefix, lessons, overall)
    return lessons, course_title


def _youtube_watch_url(src: str, base_url: str) -> str | None:
    from urllib.parse import parse_qs, urljoin, urlparse

    absolute = urljoin(base_url, src or "")
    low = absolute.lower()
    if not any(h in low for h in YOUTUBE_HOSTS):
        return None
    parsed = urlparse(absolute)
    if "youtu.be" in parsed.netloc.lower():
        vid = parsed.path.strip("/").split("/")[0]
        return f"https://www.youtube.com/watch?v={vid}" if vid else absolute
    if "youtube.com" in parsed.netloc.lower():
        qs = parse_qs(parsed.query)
        if qs.get("v"):
            return f"https://www.youtube.com/watch?v={qs['v'][0]}"
    return absolute


def _parse_youtube_iframes(
    soup: BeautifulSoup,
    *,
    url: str,
    id_prefix: str,
    lessons: list[CourseLesson],
    overall: int,
) -> int:
    seen = {(l.video_url or l.url or "").rstrip("/").lower() for l in lessons}
    for iframe in soup.find_all("iframe", src=True):
        watch = _youtube_watch_url(str(iframe.get("src") or ""), url)
        if not watch:
            continue
        key = watch.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        overall += 1
        title = f"Lesson {overall}"
        parent = iframe.find_parent(["h3", "h4", "li", "div"])
        if parent:
            heading = parent.find(["h3", "h4", "strong"])
            if heading:
                title = heading.get_text(" ", strip=True)[:256] or title
        lessons.append(
            CourseLesson(
                id=_lesson_id(id_prefix, overall),
                title=title,
                category="General",
                kind="video",
                has_video=True,
                video_url=watch,
                url=watch,
                order_index=overall,
            )
        )
    return overall


def _append_youtube(
    anchor: Tag,
    base_url: str,
    section: str,
    id_prefix: str,
    lessons: list[CourseLesson],
    overall: int,
) -> int:
    href = anchor.get("href")
    text = anchor.get_text(" ", strip=True)
    if not href or not text:
        return overall
    absolute = urljoin(base_url, href)
    if not _is_youtube(absolute):
        return overall
    title, duration = parse_duration(text)
    overall += 1
    lessons.append(
        CourseLesson(
            id=_lesson_id(id_prefix, overall),
            title=title[:256],
            category=section,
            kind="video",
            has_video=True,
            video_url=absolute,
            url=absolute,
            order_index=overall,
            duration_seconds=duration,
        )
    )
    return overall


def parse_youtube_curriculum_json_ld(html: str, *, url: str, id_prefix: str) -> list[CourseLesson]:
    """Extract ItemList / VideoObject entries when present."""
    soup = BeautifulSoup(html, "html.parser")
    lessons: list[CourseLesson] = []
    idx = 0
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for block in items:
            if not isinstance(block, dict):
                continue
            if block.get("@type") == "ItemList":
                for entry in block.get("itemListElement") or []:
                    if not isinstance(entry, dict):
                        continue
                    item = entry.get("item") or entry
                    if isinstance(item, str):
                        if _is_youtube(item):
                            idx += 1
                            lessons.append(
                                CourseLesson(
                                    id=_lesson_id(id_prefix, idx),
                                    title=f"Lesson {idx}",
                                    category="General",
                                    kind="video",
                                    has_video=True,
                                    video_url=item,
                                    url=item,
                                    order_index=idx,
                                )
                            )
                    elif isinstance(item, dict):
                        link = item.get("url") or item.get("@id") or ""
                        name = item.get("name") or f"Lesson {idx + 1}"
                        if _is_youtube(str(link)):
                            idx += 1
                            lessons.append(
                                CourseLesson(
                                    id=_lesson_id(id_prefix, idx),
                                    title=str(name)[:256],
                                    category="General",
                                    kind="video",
                                    has_video=True,
                                    video_url=str(link),
                                    url=str(link),
                                    order_index=idx,
                                )
                            )
    return lessons
