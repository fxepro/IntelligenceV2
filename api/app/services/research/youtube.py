"""
YouTube source discovery — keyless, via yt-dlp's `ytsearch`.

We search for videos matching the intent, then *aggregate them into channels*
(a channel that owns several top-ranked videos for the query is a strong
candidate). For the top channels we do a light metadata pass to pull
subscriber/video counts and the most recent upload date (recency).

No YouTube Data API key or quota required.
"""
import asyncio
from datetime import datetime, timezone

import yt_dlp

from app.services.research.types import RawCandidate

# how many channels to enrich with a follow-up metadata fetch
_ENRICH_TOP_N = 8


def _parse_upload_date(value) -> datetime | None:
    if not value:
        return None
    # yt-dlp gives YYYYMMDD strings or unix timestamps
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return datetime.strptime(str(value), "%Y%m%d").replace(tzinfo=timezone.utc)
    except (ValueError, OSError):
        return None


def _search_videos(query: str, limit: int) -> list[dict]:
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
    }
    # search a few more videos than channels requested, so aggregation has signal
    n = max(limit * 3, 15)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
    if not info:
        return []
    return [e for e in info.get("entries", []) if e]


def _enrich_channel(channel_url: str) -> dict:
    """Best-effort: pull channel-level stats + most recent upload date."""
    opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "playlistend": 1,  # we only need the channel header + newest item
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
    except Exception:
        return {}
    if not info:
        return {}
    entries = info.get("entries") or []
    newest = entries[0] if entries else {}
    return {
        "subscriber_count": info.get("channel_follower_count"),
        "item_count": info.get("playlist_count"),
        "description": (info.get("description") or "")[:600] or None,
        "last_active_at": _parse_upload_date(
            newest.get("upload_date") or newest.get("timestamp")
        ),
        "thumbnail": (info.get("thumbnails") or [{}])[-1].get("url") if info.get("thumbnails") else None,
    }


def _aggregate(entries: list[dict], limit: int) -> list[RawCandidate]:
    channels: dict[str, dict] = {}
    for e in entries:
        cid = e.get("channel_id") or e.get("uploader_id")
        curl = e.get("channel_url") or e.get("uploader_url")
        name = e.get("channel") or e.get("uploader")
        if not cid or not curl:
            continue
        bucket = channels.setdefault(
            cid,
            {
                "name": name,
                "url": curl,
                "external_id": cid,
                "match_signal": 0,
                "total_views": 0,
                "thumb": None,
            },
        )
        bucket["match_signal"] += 1
        if e.get("view_count"):
            bucket["total_views"] += int(e["view_count"])
        if not bucket["thumb"] and e.get("id"):
            bucket["thumb"] = f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg"

    ranked = sorted(channels.values(), key=lambda c: c["match_signal"], reverse=True)[:limit]

    candidates: list[RawCandidate] = []
    for i, c in enumerate(ranked):
        cand = RawCandidate(
            platform="youtube",
            url=c["url"],
            name=c["name"],
            external_id=c["external_id"],
            thumbnail_url=c["thumb"],
            suggested_source_type="channel",
            total_views=c["total_views"] or None,
            match_signal=c["match_signal"],
        )
        # enrich only the strongest matches to keep latency bounded
        if i < _ENRICH_TOP_N:
            meta = _enrich_channel(c["url"])
            cand.subscriber_count = meta.get("subscriber_count")
            cand.item_count = meta.get("item_count")
            cand.description = meta.get("description")
            cand.last_active_at = meta.get("last_active_at")
            if meta.get("thumbnail"):
                cand.thumbnail_url = meta["thumbnail"]
        candidates.append(cand)
    return candidates


def _try_channel_by_name(query: str) -> RawCandidate | None:
    """
    When video search finds nothing, try resolving the query as a channel
    handle / custom URL (common when the user types an exact channel name).
    """
    raw = query.strip().lstrip("@").strip()
    if len(raw) < 2:
        return None
    slug = raw.replace(" ", "")
    candidates_urls = [
        f"https://www.youtube.com/@{slug}",
        f"https://www.youtube.com/c/{slug}",
        f"https://www.youtube.com/{slug}",
    ]

    opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "playlistend": 1,
    }
    for url in candidates_urls:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            continue
        if not info:
            continue
        name = info.get("channel") or info.get("uploader") or info.get("title")
        if not name and not info.get("channel_id"):
            continue
        name = name or slug
        channel_url = (
            info.get("channel_url")
            or info.get("uploader_url")
            or (
                f"https://www.youtube.com/channel/{info['channel_id']}"
                if info.get("channel_id")
                else url
            )
        )
        return RawCandidate(
            platform="youtube",
            url=channel_url,
            name=name,
            external_id=info.get("channel_id") or info.get("id"),
            description=((info.get("description") or "")[:600] or None),
            subscriber_count=info.get("channel_follower_count"),
            item_count=info.get("playlist_count"),
            suggested_source_type="channel",
            thumbnail_url=(
                (info.get("thumbnails") or [{}])[-1].get("url") if info.get("thumbnails") else None
            ),
            match_signal=5,
        )
    return None


def _blocking(query: str, limit: int) -> list[RawCandidate]:
    entries = _search_videos(query, limit)
    candidates = _aggregate(entries, limit)
    if candidates:
        return candidates
    # Exact-ish channel name fallback (e.g. user typed a known handle)
    hit = _try_channel_by_name(query)
    return [hit] if hit else []


async def search(query: str, limit: int = 10) -> tuple[list[RawCandidate], str | None]:
    loop = asyncio.get_event_loop()
    candidates = await loop.run_in_executor(None, _blocking, query, limit)
    note = None if candidates else "youtube: no channels matched this query"
    return candidates, note
