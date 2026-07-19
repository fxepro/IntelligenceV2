"""
Layer 0 — Research / source discovery.

Given a free-text intent, fan out across every platform we can actually pull
data from, normalise the results into candidate sources, rank them (LLM if a
key is configured, deterministic heuristic otherwise), and hand them back to
the API layer for persistence + operator review.

Design rule: the LLM never invents sources. Real platform APIs return ground
truth (names, stats, recency); the LLM only re-ranks and explains.
"""
import asyncio

from app.services.research.types import RawCandidate, ResearchResult
from app.services.research import youtube, podcasts, web, social
from app.services.research.ranker import rank_candidates

async def _tiktok(query: str, limit: int = 10):
    return await social.search(query, limit, platform="tiktok")


async def _instagram(query: str, limit: int = 10):
    return await social.search(query, limit, platform="instagram")


async def _facebook(query: str, limit: int = 10):
    return await social.search(query, limit, platform="facebook")


# platform -> provider coroutine
PROVIDERS = {
    "youtube": youtube.search,
    "podcast": podcasts.search,
    "website": web.search,
    "tiktok": _tiktok,
    "instagram": _instagram,
    "facebook": _facebook,
}

REAL_PLATFORMS = ["youtube", "podcast", "website", "facebook"]
ALL_PLATFORMS = list(PROVIDERS.keys())


async def run_research(
    query: str,
    platforms: list[str] | None = None,
    max_per_platform: int = 10,
) -> ResearchResult:
    platforms = platforms or REAL_PLATFORMS
    query = query.strip()

    tasks = []
    used = []
    for p in platforms:
        provider = PROVIDERS.get(p)
        if not provider:
            continue
        used.append(p)
        tasks.append(provider(query, max_per_platform))

    notices: list[str] = []
    candidates: list[RawCandidate] = []

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for platform, res in zip(used, results):
        if isinstance(res, Exception):
            notices.append(f"{platform}: search failed ({type(res).__name__}: {res})")
            continue
        cands, note = res
        if note:
            notices.append(note)
        candidates.extend(cands)

    # dedupe by (platform, url)
    seen: set[tuple[str, str]] = set()
    deduped: list[RawCandidate] = []
    for c in candidates:
        key = (c.platform, (c.url or "").rstrip("/").lower())
        if not c.url or key in seen:
            continue
        seen.add(key)
        deduped.append(c)

    ranked = await rank_candidates(query, deduped)

    return ResearchResult(query=query, candidates=ranked, notices=notices)
