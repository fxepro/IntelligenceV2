"""Helpers for source content streams (videos, shorts, reels)."""
from __future__ import annotations

from app.models.source import Platform, SourceType


def youtube_channel_base(url: str) -> str:
    clean = url.rstrip("/")
    for suffix in ("/videos", "/shorts"):
        if clean.lower().endswith(suffix):
            return clean[: -len(suffix)]
    return clean


def normalize_stream_url(url: str | None) -> str | None:
    if not url:
        return None
    clean = url.strip().rstrip("/")
    return clean or None


def default_streams_for_platform(
    platform: Platform,
    primary: SourceType | None = None,
    source_url: str = "",
    stream_urls: dict[str, str] | None = None,
) -> list[tuple[SourceType, bool, str | None]]:
    """Return (stream_type, enabled, stream_url). Blank URL = subtype does not exist."""
    p = platform.value if hasattr(platform, "value") else str(platform)
    explicit = stream_urls or {}

    if p == "youtube":
        videos = normalize_stream_url(explicit.get(SourceType.youtube_videos.value))
        shorts = normalize_stream_url(explicit.get(SourceType.youtube_shorts.value))
        return [
            (SourceType.youtube_videos, bool(videos), videos),
            (SourceType.youtube_shorts, bool(shorts), shorts),
        ]

    if p == "facebook":
        reels = normalize_stream_url(explicit.get(SourceType.facebook_reels.value))
        videos = normalize_stream_url(explicit.get(SourceType.facebook_videos.value))
        return [
            (SourceType.facebook_reels, bool(reels), reels),
            (SourceType.facebook_videos, bool(videos), videos),
        ]

    if p == "instagram":
        url = normalize_stream_url(source_url)
        return [(SourceType.instagram_reels, bool(url), url)]
    if p == "tiktok":
        url = normalize_stream_url(source_url)
        return [(SourceType.tiktok_videos, bool(url), url)]
    if p == "x":
        url = normalize_stream_url(source_url)
        return [(SourceType.x_posts, bool(url), url)]
    if p in ("podcast", "rss"):
        url = normalize_stream_url(source_url)
        return [(SourceType.rss_feed, bool(url), url)]
    if p == "website":
        url = normalize_stream_url(source_url)
        return [(SourceType.sitemap, bool(url), url)]
    if p == "government":
        url = normalize_stream_url(source_url)
        stream = primary if primary else SourceType.website
        return [(stream, bool(url), url)]
    if primary:
        url = normalize_stream_url(source_url)
        return [(primary, bool(url), url)]
    url = normalize_stream_url(source_url)
    return [(SourceType.profile, bool(url), url)]


def infer_stream_type(
    platform: str,
    content_type: str | None = None,
    fallback: str | None = None,
) -> str:
    """Map discovered content to a stream subtype."""
    if fallback:
        return fallback
    p = (platform or "").lower()
    ct = (content_type or "video").lower()
    if p == "youtube":
        return SourceType.youtube_shorts.value if ct == "short" else SourceType.youtube_videos.value
    if p == "facebook":
        return SourceType.facebook_reels.value if ct == "short" else SourceType.facebook_videos.value
    if p == "instagram":
        return SourceType.instagram_reels.value
    if p == "tiktok":
        return SourceType.tiktok_videos.value
    if p == "x":
        return SourceType.x_posts.value
    if p in ("podcast", "rss"):
        return SourceType.rss_feed.value
    if p == "website":
        return SourceType.sitemap.value
    return fallback or SourceType.profile.value
