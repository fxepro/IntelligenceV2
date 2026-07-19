"""
Podcast source discovery — via Apple's iTunes Search API (keyless, free).

Returns the show name, episode count, artwork, the most recent release date
(recency), and crucially the RSS `feedUrl` — which is exactly what a promoted
Source needs to be monitored as an `rss_feed`.
"""
from datetime import datetime

import httpx

from app.services.research.types import RawCandidate

_ITUNES_URL = "https://itunes.apple.com/search"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # iTunes returns ISO 8601 with trailing Z
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def search(query: str, limit: int = 10) -> tuple[list[RawCandidate], str | None]:
    params = {"term": query, "media": "podcast", "entity": "podcast", "limit": limit}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(_ITUNES_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    candidates: list[RawCandidate] = []
    for r in data.get("results", []):
        feed = r.get("feedUrl")
        if not feed:
            continue
        genres = ", ".join(r.get("genres", [])[:3])
        candidates.append(
            RawCandidate(
                platform="podcast",
                url=feed,
                name=r.get("collectionName") or r.get("trackName"),
                external_id=str(r.get("collectionId")) if r.get("collectionId") else None,
                thumbnail_url=r.get("artworkUrl600") or r.get("artworkUrl100"),
                description=f"{r.get('artistName', '')} — {genres}".strip(" —") or None,
                suggested_source_type="rss_feed",
                item_count=r.get("trackCount"),
                last_active_at=_parse_date(r.get("releaseDate")),
            )
        )

    note = None if candidates else "podcast: no shows matched this query"
    return candidates, note
