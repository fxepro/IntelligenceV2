"""
Social source discovery — TikTok / Instagram / Facebook.

None of these platforms expose an official, keyless creator-search API.
We approximate with DuckDuckGo `site:` queries and keep only profile/page
URLs (not posts/reels). Empty + honest notice if search is unavailable.
"""
import re
from urllib.parse import parse_qs, unquote, urlparse

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

_SITE = {
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "tiktok": "tiktok.com",
}

# path prefixes that are content, not creator profiles
_SKIP_PATH_PREFIXES = (
    "/reel/",
    "/reels/",
    "/watch",
    "/posts/",
    "/permalink",
    "/photo",
    "/video",
    "/stories/",
    "/share/",
    "/groups/",
    "/events/",
    "/marketplace/",
    "/login",
    "/recover",
    "/help",
    "/privacy",
    "/policies",
    "/p/",  # instagram posts
    "/tv/",
    "/explore",
    "/music/",
    "/tag/",
    "/hashtag/",
)


def _clean_text(html: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub("", html)).strip()


def _real_url(href: str) -> str | None:
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        return unquote(target) if target else None
    if parsed.scheme in ("http", "https"):
        return href
    return None


def _normalize_facebook(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    if host not in ("facebook.com", "m.facebook.com", "www.facebook.com", "fb.com", "www.fb.com"):
        return None
    path = parsed.path or "/"
    low = path.lower()
    if any(low.startswith(p) for p in _SKIP_PATH_PREFIXES):
        return None
    # profile.php?id=…
    qs = parse_qs(parsed.query)
    if "profile.php" in low and qs.get("id"):
        return f"https://www.facebook.com/profile.php?id={qs['id'][0]}"
    # /people/Name/ID
    m = re.match(r"^/people/[^/]+/(\d+)/?", path)
    if m:
        return f"https://www.facebook.com/profile.php?id={m.group(1)}"
    # vanity /PageName
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    slug = parts[0]
    if slug in ("pages", "public", "pg"):
        return None
    if slug.startswith("@"):
        slug = slug[1:]
    return f"https://www.facebook.com/{slug}"


def _normalize_instagram(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    if "instagram.com" not in host:
        return None
    path = parsed.path or "/"
    low = path.lower()
    if any(low.startswith(p) for p in _SKIP_PATH_PREFIXES):
        return None
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    slug = parts[0].lstrip("@")
    if slug in ("accounts", "about", "developer", "directory"):
        return None
    return f"https://www.instagram.com/{slug}/"


def _normalize_tiktok(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    if "tiktok.com" not in host:
        return None
    path = parsed.path or "/"
    low = path.lower()
    if any(low.startswith(p) for p in _SKIP_PATH_PREFIXES):
        return None
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    slug = parts[0]
    if not slug.startswith("@"):
        slug = f"@{slug}"
    return f"https://www.tiktok.com/{slug}"


_NORMALIZERS = {
    "facebook": _normalize_facebook,
    "instagram": _normalize_instagram,
    "tiktok": _normalize_tiktok,
}


def _name_from_url(platform: str, url: str, label: str) -> str:
    cleaned = _clean_text(label)
    if cleaned and len(cleaned) > 2:
        return cleaned[:120]
    parsed = urlparse(url)
    parts = [p for p in (parsed.path or "").split("/") if p]
    if not parts:
        return url
    slug = parts[-1] if "profile.php" not in parts else parts[0]
    if platform == "facebook" and "profile.php" in (parsed.path or ""):
        qs = parse_qs(parsed.query)
        return f"Facebook profile {qs.get('id', [''])[0]}"
    return slug.lstrip("@").replace("-", " ")[:120]


async def search(
    query: str,
    limit: int = 10,
    platform: str = "facebook",
) -> tuple[list[RawCandidate], str | None]:
    site = _SITE.get(platform)
    normalize = _NORMALIZERS.get(platform)
    if not site or not normalize:
        return [], f"{platform}: unsupported social platform"

    ddg_query = f"site:{site} {query}".strip()
    try:
        async with httpx.AsyncClient(timeout=15, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.post(_DDG_URL, data={"q": ddg_query})
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        return [], f"{platform}: web search unavailable ({type(exc).__name__})"

    seen: set[str] = set()
    candidates: list[RawCandidate] = []
    for href, label in _RESULT_RE.findall(html):
        raw = _real_url(href)
        if not raw:
            continue
        url = normalize(raw)
        if not url:
            continue
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            RawCandidate(
                platform=platform,
                url=url,
                name=_name_from_url(platform, url, label),
                description=_clean_text(label)[:300] or None,
                suggested_source_type="profile",
                match_signal=1,
            )
        )
        if len(candidates) >= limit:
            break

    if candidates:
        return candidates, None
    return (
        [],
        f"{platform}: no public pages matched — try the exact page URL on Sources, "
        "or a broader name",
    )
