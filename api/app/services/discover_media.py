"""
Media discovery connectors — extraction only (no DB / FastAPI).

Ported from v1 api/discover.py. Persist records in the Celery worker.
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import yt_dlp


@dataclass
class DiscoveredItem:
    external_id: str
    canonical_url: str
    title: str | None
    thumbnail_url: str | None = None
    channel_name: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    published_at: str | None = None
    content_type: str = "video"  # video | short
    description: str | None = None
    enclosure_url: str | None = None
    file_size_bytes: int | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _entries(info: dict | None) -> list[dict]:
    if not info:
        return []
    if "entries" in info:
        return [e for e in info["entries"] if e]
    return [info]


def _ydl_opts(url: str, **extra) -> dict:
    from app.services.platform_sessions import apply_cookies_to_ydl_opts

    opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        **extra,
    }
    return apply_cookies_to_ydl_opts(opts, url)


def _flat_entries(url: str, max_items: int) -> list[dict]:
    opts = _ydl_opts(url, extract_flat="in_playlist", playlistend=max_items)
    with yt_dlp.YoutubeDL(opts) as ydl:
        return _entries(ydl.extract_info(url, download=False))


_YT_TABS = ("/videos", "/shorts", "/streams", "/live", "/featured", "/playlists", "/community")
_PLAYLIST_ID_PREFIXES = ("PL", "UU", "FL", "RD", "OL", "LL")


def _yt_channel_base(url: str) -> str | None:
    base = url.rstrip("/")
    low = base.lower()
    for tab in _YT_TABS:
        if low.endswith(tab):
            base = base[: -len(tab)]
            break
    low = base.lower()
    if "youtube.com" in low and any(seg in low for seg in ("/@", "/channel/", "/c/", "/user/")):
        return base
    return None


def _videos_tab_url(original_url: str, entries: list[dict]) -> str | None:
    for e in entries:
        u = e.get("url") or e.get("webpage_url")
        title = (e.get("title") or "").lower()
        if u and (u.lower().endswith("/videos") or title.endswith("videos")):
            return u
    for e in entries:
        cid = e.get("channel_id") or e.get("id")
        if cid and cid.startswith("UC") and len(cid) == 24:
            return f"https://www.youtube.com/channel/{cid}/videos"
    base = original_url.rstrip("/")
    for suffix in ("/videos", "/shorts", "/streams", "/featured"):
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
            break
    if "youtube.com" in base and ("/@" in base or "/channel/" in base or "/c/" in base or "/user/" in base):
        return f"{base}/videos"
    return None


def _ytdlp_fetch(url: str, max_items: int) -> list[dict]:
    ydl_opts = _ydl_opts(url, extract_flat="in_playlist", playlistend=max_items)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        entries = _entries(ydl.extract_info(url, download=False))
        if any(_is_video_entry(e) for e in entries):
            return entries
        videos_url = _videos_tab_url(url, entries)
        if videos_url:
            return _entries(ydl.extract_info(videos_url, download=False))
        return entries


def _parse_date(upload_date: str | None) -> str | None:
    if not upload_date:
        return None
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return None


def _published_at(entry: dict) -> str | None:
    parsed = _parse_date(entry.get("upload_date"))
    if parsed:
        return parsed
    for key in ("timestamp", "release_timestamp", "modified_timestamp"):
        raw = entry.get(key)
        if raw is None:
            continue
        try:
            return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError, OverflowError):
            continue
    return None


def _estimate_bitrate_kbps(info: dict) -> float | None:
    """Rough kbps by resolution when the extractor omits tbr (typical H.264)."""
    height = info.get("height")
    width = info.get("width")
    if not height:
        for fmt in reversed(info.get("formats") or []):
            if fmt.get("height"):
                height = fmt.get("height")
                width = fmt.get("width")
                break
    if not height:
        return 2500.0  # unknown: assume ~720p vertical reel
    h = int(height)
    if h >= 2000:
        return 8000.0
    if h >= 1080:
        return 4500.0
    if h >= 720:
        return 2500.0
    if h >= 480:
        return 1200.0
    return 700.0


def _file_size_bytes(info: dict) -> int | None:
    """Exact size when known; otherwise estimate from bitrate × duration.

    Always returns a value when duration is known (estimate flagged by caller).
    """
    for key in ("filesize", "filesize_approx"):
        raw = info.get(key)
        if raw:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    duration = info.get("duration")
    tbr = info.get("tbr")
    if tbr is None:
        for fmt in reversed(info.get("formats") or []):
            approx = fmt.get("filesize") or fmt.get("filesize_approx")
            if approx:
                try:
                    return int(approx)
                except (TypeError, ValueError):
                    pass
            if fmt.get("tbr"):
                tbr = fmt["tbr"]
                break
    if duration is None:
        return None
    if tbr is None:
        tbr = _estimate_bitrate_kbps(info)
    try:
        # tbr is kilobits/sec → bytes
        return max(1, int(float(tbr) * float(duration) * 1000 / 8))
    except (TypeError, ValueError):
        return None


def _is_video_entry(entry: dict) -> bool:
    if entry.get("_type") == "playlist":
        return False
    ie_key = entry.get("ie_key") or entry.get("extractor_key") or ""
    if any(tok in ie_key for tok in ("Tab", "Playlist", "Channel")):
        return False
    vid = entry.get("id") or ""
    if not vid:
        return False
    if len(vid) == 24 and vid.startswith("UC"):
        return False
    if len(vid) > 12 and vid.startswith(_PLAYLIST_ID_PREFIXES):
        return False
    return True


def _youtube_thumbnail(entry: dict, video_id: str) -> str | None:
    thumb = entry.get("thumbnail")
    if isinstance(thumb, str) and thumb.strip():
        return thumb.strip()
    thumbs = entry.get("thumbnails") or []
    if isinstance(thumbs, list) and thumbs:
        # Prefer the last (usually largest) URL yt-dlp lists.
        for t in reversed(thumbs):
            if isinstance(t, dict) and t.get("url"):
                return str(t["url"])
            if isinstance(t, str) and t.strip():
                return t.strip()
    if video_id and re.fullmatch(r"[\w-]{6,}", video_id):
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return None


def _build_item(entry: dict) -> DiscoveredItem:
    video_id = entry.get("id") or ""
    url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
    if video_id and "youtube" in url and "watch" not in url:
        url = f"https://www.youtube.com/watch?v={video_id}"
    return DiscoveredItem(
        external_id=video_id,
        canonical_url=url,
        title=entry.get("title"),
        thumbnail_url=_youtube_thumbnail(entry, video_id),
        channel_name=entry.get("channel") or entry.get("uploader") or entry.get("channel_id"),
        duration_seconds=int(entry["duration"]) if entry.get("duration") else None,
        view_count=int(entry["view_count"]) if entry.get("view_count") else None,
        published_at=_published_at(entry),
        file_size_bytes=_file_size_bytes(entry),
    )


def _dedupe_videos(entries: list[dict]) -> list[DiscoveredItem]:
    seen: set[str] = set()
    items: list[DiscoveredItem] = []
    for e in entries:
        if not _is_video_entry(e):
            continue
        vid = e["id"]
        if vid in seen:
            continue
        seen.add(vid)
        items.append(_build_item(e))
    return items


def youtube_tab_items(url: str, max_items: int, content_type: str) -> list[DiscoveredItem]:
    """Scrape exactly one YouTube tab URL (videos or shorts)."""
    clean = (url or "").rstrip("/")
    low = clean.lower()
    if content_type == "short":
        target = clean if low.endswith("/shorts") else f"{_yt_channel_base(clean) or clean}/shorts"
    else:
        target = clean if low.endswith("/videos") else f"{_yt_channel_base(clean) or clean}/videos"
    items: list[DiscoveredItem] = []
    seen: set[str] = set()
    try:
        entries = _flat_entries(target, max_items)
    except Exception:
        return []
    for e in entries:
        if not _is_video_entry(e):
            continue
        vid = e.get("id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        item = _build_item(e)
        item.content_type = content_type
        items.append(item)
    return items


def youtube_items(url: str, max_items: int) -> list[DiscoveredItem]:
    """Legacy: both tabs. Prefer youtube_tab_items when stream_type is known."""
    base = _yt_channel_base(url)
    if not base:
        return _dedupe_videos(_ytdlp_fetch(url, max_items))
    items: list[DiscoveredItem] = []
    seen: set[str] = set()
    for tab, content_type in (("videos", "video"), ("shorts", "short")):
        for item in youtube_tab_items(f"{base}/{tab}", max_items, content_type):
            if item.external_id in seen:
                continue
            seen.add(item.external_id)
            items.append(item)
    return items


def _parse_rfc_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return None


def _itunes_duration_seconds(value) -> int | None:
    if not value:
        return None
    try:
        s = str(value)
        if ":" in s:
            parts = [int(p) for p in s.split(":")]
            while len(parts) < 3:
                parts.insert(0, 0)
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _build_feed_item(entry: dict) -> DiscoveredItem:
    link = entry.get("link") or entry.get("id") or ""
    thumb = None
    if isinstance(entry.get("image"), dict):
        thumb = entry["image"].get("href")
    if not thumb and entry.get("media_thumbnail"):
        thumb = entry["media_thumbnail"][0].get("url")
    enclosure = None
    for enc in entry.get("enclosures") or []:
        if enc.get("href"):
            enclosure = enc["href"]
            break
    return DiscoveredItem(
        external_id=entry.get("id") or link,
        canonical_url=link,
        title=entry.get("title"),
        description=(entry.get("summary") or entry.get("description") or "")[:4000] or None,
        thumbnail_url=thumb,
        channel_name=entry.get("author"),
        duration_seconds=_itunes_duration_seconds(entry.get("itunes_duration")),
        view_count=None,
        published_at=_parse_rfc_date(entry.get("published")),
        enclosure_url=enclosure,
    )


def feed_fetch(url: str, max_items: int) -> list[DiscoveredItem]:
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        raise ValueError(f"Could not parse feed: {getattr(feed, 'bozo_exception', 'unknown error')}")
    items: list[DiscoveredItem] = []
    seen: set[str] = set()
    for e in feed.entries[:max_items]:
        link = e.get("link") or e.get("id")
        if not link or link in seen:
            continue
        seen.add(link)
        items.append(_build_feed_item(e))
    return items


def website_fetch(url: str, max_items: int) -> list[DiscoveredItem]:
    base = url.rstrip("/")
    for candidate in (url, f"{base}/feed", f"{base}/rss", f"{base}/feed.xml", f"{base}/rss.xml"):
        try:
            items = feed_fetch(candidate, max_items)
            if items:
                return items
        except Exception:
            continue
    videos = _dedupe_videos(_ytdlp_fetch(url, max_items))
    if videos:
        return videos
    raise ValueError("No RSS feed or extractable media found for this website")


def _facebook_channel_name(resolved_page: str) -> str | None:
    from app.services.facebook_reels import extract_facebook_profile_id

    channel = resolved_page.rsplit("/", 1)[-1] or None
    if "profile.php" in resolved_page:
        pid = extract_facebook_profile_id(resolved_page)
        channel = f"id={pid}" if pid else resolved_page
    return channel


def _facebook_rows_to_items(
    rows: list[dict],
    *,
    channel: str | None,
    content_type: str,
    title_fallback: str,
) -> list[DiscoveredItem]:
    from app.services.facebook_reels import clean_reel_title, parse_view_count

    items: list[DiscoveredItem] = []
    for row in rows:
        thumb = (row.get("thumbnail_url") or "").strip() or None
        if not thumb:
            continue
        title = clean_reel_title(row.get("title")) or f"{title_fallback} {row['id']}"
        duration = row.get("duration_seconds")
        try:
            duration_i = int(duration) if duration is not None else None
        except (TypeError, ValueError):
            duration_i = None
        size = None
        if duration_i and duration_i > 0:
            size = max(1, int(1200.0 * float(duration_i) * 1000 / 8))
        items.append(
            DiscoveredItem(
                external_id=row["id"],
                canonical_url=row["url"],
                title=title,
                thumbnail_url=thumb,
                channel_name=channel,
                duration_seconds=duration_i,
                file_size_bytes=size,
                view_count=parse_view_count(row.get("view_count_raw")),
                published_at=None,
                content_type=content_type,
            )
        )
    return items


def facebook_items(url: str, max_items: int) -> tuple[list[DiscoveredItem], str]:
    from app.services.facebook_reels import (
        normalize_facebook_page_url,
        scrape_facebook_reels_sync,
    )

    limit = max(max_items, 150)
    # Deep FB catalogs need many scrolls — grid is virtualized and soft-caps ~70.
    scrolls = min(280, max(100, limit // 2))
    idle = 16 if limit >= 200 else 12
    rows, resolved_reels = scrape_facebook_reels_sync(
        url, max_items=limit, max_scrolls=scrolls, idle_rounds=idle
    )
    resolved_page = normalize_facebook_page_url(resolved_reels)
    items = _facebook_rows_to_items(
        rows,
        channel=_facebook_channel_name(resolved_page),
        content_type="short",
        title_fallback="Reel",
    )
    # Duration/size: scrape first; parallel yt-dlp fills gaps (not serial hours).
    return enrich_missing_duration_parallel(items), resolved_page


def facebook_video_items(url: str, max_items: int) -> tuple[list[DiscoveredItem], str]:
    """Discover non-reel Videos-tab items via Playwright (yt-dlp cannot list /videos)."""
    from app.services.facebook_reels import normalize_facebook_page_url
    from app.services.facebook_videos import scrape_facebook_videos_sync

    limit = max(max_items, 100)
    scrolls = min(280, max(80, limit // 2))
    idle = 16 if limit >= 200 else 12
    rows, resolved_videos = scrape_facebook_videos_sync(
        url, max_items=limit, max_scrolls=scrolls, idle_rounds=idle
    )
    resolved_page = normalize_facebook_page_url(resolved_videos)
    items = _facebook_rows_to_items(
        rows,
        channel=_facebook_channel_name(resolved_page),
        content_type="video",
        title_fallback="Video",
    )
    return enrich_missing_duration_parallel(items), resolved_page


def enrich_missing_duration_parallel(
    items: list[DiscoveredItem],
    *,
    workers: int = 16,
) -> list[DiscoveredItem]:
    """Fill duration/size for items missing duration — parallel, bounded workers."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import tempfile
    from pathlib import Path

    need = [it for it in items if it.duration_seconds is None and it.canonical_url]
    if not need:
        return items

    base_opts = _ydl_opts(need[0].canonical_url, skip_download=True)

    def _one(url: str) -> dict | None:
        import yt_dlp

        local = {**base_opts, "quiet": True, "no_warnings": True}
        cookie = local.get("cookiefile")
        tmp = None
        if cookie and Path(cookie).is_file():
            raw = Path(cookie).read_text(encoding="utf-8", errors="ignore")
            if "Netscape" in raw or raw.startswith("#"):
                fd, tmp = tempfile.mkstemp(prefix="mi-ydl-", suffix=".txt")
                os.close(fd)
                Path(tmp).write_text(raw, encoding="utf-8")
                local["cookiefile"] = tmp
            else:
                local.pop("cookiefile", None)
        try:
            with yt_dlp.YoutubeDL(local) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            return None
        finally:
            if tmp:
                try:
                    Path(tmp).unlink(missing_ok=True)
                except Exception:
                    pass

    # Index by url for merge
    by_url = {it.canonical_url: it for it in need}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(need)))) as pool:
        futs = {pool.submit(_one, url): url for url in by_url}
        for fut in as_completed(futs):
            url = futs[fut]
            info = fut.result()
            if not info or not info.get("duration"):
                continue
            it = by_url[url]
            try:
                it.duration_seconds = int(float(info["duration"]))
            except (TypeError, ValueError):
                continue
            size = _file_size_bytes(info)
            if size:
                it.file_size_bytes = size
            elif it.duration_seconds:
                it.file_size_bytes = max(
                    1, int(1200.0 * float(it.duration_seconds) * 1000 / 8)
                )
            if it.view_count is None and info.get("view_count") is not None:
                try:
                    it.view_count = int(info["view_count"])
                except (TypeError, ValueError):
                    pass
            if not it.published_at:
                it.published_at = _published_at(info)
    return items


def _is_placeholder_title(title: str | None) -> bool:
    text = " ".join(str(title or "").split()).strip().lower()
    if not text:
        return True
    if "tile preview" in text:
        return True
    if text.startswith("reel ") and text[5:].isdigit():
        return True
    if text.startswith("facebook video #"):
        return True
    return text in {"preview", "reels", "facebook reel", "reel tile preview"}


def _clean_facebook_info_title(info: dict) -> str | None:
    """FB yt-dlp titles often look like '63K views · … | caption | Page'."""
    from app.services.facebook_reels import clean_reel_title

    raw = (info.get("title") or "").strip()
    desc = (info.get("description") or "").strip().split("\n")[0].strip()
    if raw and "|" in raw and "view" in raw.lower():
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        for part in parts[1:]:
            low = part.lower()
            if "view" in low or "reaction" in low:
                continue
            # Skip bare page/uploader name if we have a longer caption.
            if desc and part.lower() == (info.get("uploader") or "").lower():
                continue
            cleaned = clean_reel_title(part)
            if cleaned and not _is_placeholder_title(cleaned):
                return cleaned[:240]
    cleaned_desc = clean_reel_title(desc)
    if cleaned_desc and not _is_placeholder_title(cleaned_desc):
        return cleaned_desc[:240]
    cleaned_raw = clean_reel_title(raw)
    if cleaned_raw and not _is_placeholder_title(cleaned_raw):
        return cleaned_raw[:240]
    return None


def _needs_metadata_enrichment(item: DiscoveredItem) -> bool:
    return (
        item.duration_seconds is None
        or not item.published_at
        or item.view_count is None
        or item.file_size_bytes is None
        or _is_placeholder_title(item.title)
        or not item.thumbnail_url
    )


def _enrich_missing_metadata(
    items: list[DiscoveredItem],
    *,
    limit: int = 40,
) -> list[DiscoveredItem]:
    """Fill duration/published/title gaps (YouTube flat lists + Facebook reels)."""
    need_all = [it for it in items if _needs_metadata_enrichment(it)]
    # Prefer duration/size gaps next — thumbs alone leave the grid half-empty.
    need_all.sort(
        key=lambda it: (
            0 if not it.thumbnail_url else 1,
            0 if it.duration_seconds is None else 1,
            0 if it.file_size_bytes is None else 1,
            0 if _is_placeholder_title(it.title) else 1,
        )
    )
    need = need_all[:limit]
    if not need:
        return items
    # Cookiefile is chosen from the first URL; enrich passes may mix platforms rarely.
    sample_url = need[0].canonical_url if need else ""
    opts = _ydl_opts(sample_url, skip_download=True)
    with yt_dlp.YoutubeDL(opts) as ydl:
        for it in need:
            try:
                info = ydl.extract_info(it.canonical_url, download=False)
            except Exception:
                continue
            if not info:
                continue
            if it.duration_seconds is None and info.get("duration"):
                it.duration_seconds = int(float(info["duration"]))
            if not it.published_at:
                it.published_at = _published_at(info)
            if it.file_size_bytes is None:
                it.file_size_bytes = _file_size_bytes(info)
            if not it.thumbnail_url and info.get("thumbnail"):
                it.thumbnail_url = info.get("thumbnail")
            if it.view_count is None and info.get("view_count") is not None:
                it.view_count = int(info["view_count"])
            if "facebook.com" in (it.canonical_url or ""):
                cleaned = _clean_facebook_info_title(info)
                if cleaned:
                    it.title = cleaned[:240]
            else:
                info_title = (info.get("title") or "").strip()
                if info_title and _is_placeholder_title(it.title):
                    it.title = info_title[:240]
            if not it.description and info.get("description"):
                it.description = str(info.get("description"))[:4000]
            if not it.channel_name:
                it.channel_name = (
                    info.get("uploader")
                    or info.get("channel")
                    or info.get("creator")
                )
    return items


def extract_items(
    platform: str,
    url: str,
    max_items: int,
    source_type: str | None = None,
) -> list[DiscoveredItem]:
    platform = (platform or "").lower()
    source_type = (source_type or "").lower()
    if platform in ("podcast", "rss"):
        return feed_fetch(url, max_items)
    if platform == "website":
        return website_fetch(url, max_items)
    if platform == "youtube":
        if source_type == "youtube_shorts":
            return _enrich_missing_metadata(
                youtube_tab_items(url, max_items, "short"),
                limit=max_items,
            )
        if source_type == "youtube_videos":
            return _enrich_missing_metadata(
                youtube_tab_items(url, max_items, "video"),
                limit=max_items,
            )
        return youtube_items(url, max_items)
    if platform == "facebook":
        if source_type == "facebook_videos":
            items, _resolved = facebook_video_items(url, max_items)
            return items
        items, _resolved = facebook_items(url, max_items)
        return items
    return _dedupe_videos(_ytdlp_fetch(url, max_items))
