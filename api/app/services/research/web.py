"""
Website / general-web source discovery — keyless, best-effort.

Uses the DuckDuckGo HTML endpoint (no API key) to find sites relevant to the
intent, then collapses results to their root domain so each becomes a website
source candidate. The discovery engine (Layer 2) can later detect each site's
RSS/sitemap when the candidate is promoted.

This path is intentionally defensive: if DuckDuckGo changes markup or rate
limits us, we degrade to an empty result with a notice rather than erroring.
"""
import re
from urllib.parse import urlparse, parse_qs, unquote

import httpx

from app.services.research.types import RawCandidate

_DDG_URL = "https://html.duckduckgo.com/html/"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}
_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(html: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub("", html)).strip()


def _real_url(href: str) -> str | None:
    # DDG wraps results as //duckduckgo.com/l/?uddg=<encoded target>
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        return unquote(target) if target else None
    if parsed.scheme in ("http", "https"):
        return href
    return None


async def search(query: str, limit: int = 10) -> tuple[list[RawCandidate], str | None]:
    try:
        async with httpx.AsyncClient(timeout=15, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.post(_DDG_URL, data={"q": query})
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        return [], f"website: web search unavailable ({type(exc).__name__})"

    seen_domains: set[str] = set()
    candidates: list[RawCandidate] = []
    for href, label in _RESULT_RE.findall(html):
        url = _real_url(href)
        if not url:
            continue
        domain = urlparse(url).netloc.lower().lstrip("www.")
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        root = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        candidates.append(
            RawCandidate(
                platform="website",
                url=root,
                name=domain,
                description=_clean_text(label)[:300] or None,
                suggested_source_type="sitemap",
            )
        )
        if len(candidates) >= limit:
            break

    note = None if candidates else "website: no results (search may be rate-limited)"
    return candidates, note
