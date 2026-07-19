"""Source URL probes — detect dead links and identity redirects.

Facebook (and similar) block plain HTTP with a generic 400 Error page for both
live and dead URLs. Soft-OK on that wall caused false greens. Facebook checks
use Playwright + the saved Access session so results match a real browser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import httpx

URL_CHECK_PREFIX = "URL check: "

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

_SOCIAL = {"facebook", "instagram", "tiktok", "x", "youtube"}
_BROWSER_PLATFORMS = frozenset({"facebook"})

_DEAD_MARKERS = (
    "this content isn't available",
    "content isn't available right now",
    "this page isn't available",
    "page isn't available",
    "profile isn't available",
    "sorry, this page isn't available",
    "the link you followed may be broken",
    "content not found",
    "page not found",
    "isn't available right now",
)

_BOT_WALL_MARKERS = (
    "checkpoint",
    "suspicious activity",
    "confirm you're human",
    "confirm you are human",
)


@dataclass
class UrlProbeResult:
    ok: bool
    checked_url: str
    final_url: str | None = None
    status_code: int | None = None
    redirected: bool = False
    identity_changed: bool = False
    hard_fail: bool = False
    inconclusive: bool = False
    error: str | None = None


def _strip_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _normalize_compare_url(url: str, platform: str) -> str:
    from app.services.facebook_reels import (
        extract_facebook_profile_id,
        normalize_facebook_page_url,
    )

    cleaned = _strip_url(url)
    if not cleaned:
        return ""
    if platform == "facebook":
        profile_id = extract_facebook_profile_id(cleaned)
        if profile_id:
            return f"https://www.facebook.com/profile.php?id={profile_id}"
        return normalize_facebook_page_url(cleaned)
    parsed = urlparse(cleaned)
    host = (parsed.netloc or "").lower().removeprefix("www.")
    path = (parsed.path or "/").rstrip("/") or "/"
    return urlunparse(("https", host, path, "", "", ""))


def _identity_key(url: str, platform: str) -> str:
    from app.services.facebook_reels import extract_facebook_profile_id

    if platform == "facebook":
        profile_id = extract_facebook_profile_id(url)
        if profile_id:
            return f"fb:{profile_id}"
    return _normalize_compare_url(url, platform)


def _body_has_dead_marker(text: str) -> bool:
    lower = (text or "").lower()
    return any(marker in lower for marker in _DEAD_MARKERS)


def _is_http_bot_wall(*, status_code: int | None, title: str, body: str) -> bool:
    """Facebook/Meta often returns a tiny titled Error page to non-browser clients."""
    if status_code is None:
        return False
    title_l = (title or "").strip().lower()
    body_l = (body or "").lower()
    if status_code in (400, 401, 403) and title_l in {"error", "error facebook", "facebook"}:
        if len(body or "") < 8000 and not _body_has_dead_marker(body_l):
            return True
    if any(m in body_l for m in _BOT_WALL_MARKERS):
        return True
    return False


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _httpx_cookies(platform: str) -> httpx.Cookies | None:
    try:
        from app.services.platform_sessions import load_connected_session

        state = load_connected_session(platform)
        if not state:
            return None
        jar = httpx.Cookies()
        for cookie in state.get("cookies") or []:
            if not isinstance(cookie, dict) or not cookie.get("name"):
                continue
            jar.set(
                str(cookie["name"]),
                str(cookie.get("value") or ""),
                domain=str(cookie.get("domain") or "") or None,
                path=str(cookie.get("path") or "/"),
            )
        return jar
    except Exception:
        return None


def _interpret(
    checked: str,
    *,
    platform: str,
    final: str,
    status_code: int,
    body: str = "",
    title: str = "",
) -> UrlProbeResult:
    redirected = _normalize_compare_url(final, platform) != _normalize_compare_url(
        checked, platform
    )
    identity_changed = _identity_key(final, platform) != _identity_key(checked, platform)
    lower_final = final.lower()
    text = body or ""

    if _body_has_dead_marker(text) or _body_has_dead_marker(title):
        # Facebook (and other social) often inject these phrases on login /
        # restricted interstitials for live pages. Only hard-fail on real 404/410.
        if platform in _SOCIAL and status_code not in (404, 410):
            return UrlProbeResult(
                ok=False,
                checked_url=checked,
                final_url=final,
                status_code=status_code,
                redirected=redirected,
                identity_changed=identity_changed,
                hard_fail=False,
                inconclusive=True,
                error="unavailable wording — could not verify (not marked dead)",
            )
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            identity_changed=identity_changed,
            hard_fail=True,
            error="content not available",
        )

    if status_code in (404, 410):
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            identity_changed=identity_changed,
            hard_fail=True,
            error=f"HTTP {status_code} — URL not found",
        )

    if identity_changed:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=True,
            identity_changed=True,
            hard_fail=False,
            error=f"identity changed → {final}",
        )

    if _is_http_bot_wall(status_code=status_code, title=title, body=text):
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            hard_fail=False,
            inconclusive=True,
            error="blocked by platform bot wall — needs browser check",
        )

    # Login interstitial without a clear death marker: inconclusive for social.
    if platform in _SOCIAL and "login" in lower_final and not identity_changed:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            hard_fail=False,
            inconclusive=True,
            error="login wall — could not verify URL",
        )

    if status_code >= 400:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            identity_changed=identity_changed,
            hard_fail=True,
            error=f"HTTP {status_code}",
        )

    return UrlProbeResult(
        ok=True,
        checked_url=checked,
        final_url=final,
        status_code=status_code,
        redirected=redirected,
        identity_changed=False,
        hard_fail=False,
        error=None,
    )


def _client_kwargs(platform: str, timeout: float) -> dict:
    return {
        "follow_redirects": True,
        "timeout": timeout,
        "headers": {
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "cookies": _httpx_cookies(platform) if platform in _SOCIAL else None,
    }


def _http_probe_sync(url: str, *, platform: str, timeout: float) -> UrlProbeResult:
    checked = _strip_url(url)
    if not checked:
        return UrlProbeResult(ok=False, checked_url="", hard_fail=True, error="empty URL")

    try:
        with httpx.Client(**_client_kwargs(platform, timeout)) as client:
            if platform in _SOCIAL:
                response = client.get(checked)
            else:
                try:
                    response = client.head(checked)
                    if response.status_code in (405, 501) or response.status_code >= 400:
                        response = client.get(checked)
                except httpx.HTTPError:
                    response = client.get(checked)
    except httpx.TimeoutException:
        return UrlProbeResult(ok=False, checked_url=checked, hard_fail=True, error="timed out")
    except httpx.HTTPError as exc:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            hard_fail=True,
            error=f"{type(exc).__name__}: {exc}"[:240],
        )

    body = ""
    try:
        body = response.text[:100_000]
    except Exception:
        body = ""
    return _interpret(
        checked,
        platform=platform,
        final=str(response.url),
        status_code=response.status_code,
        body=body,
        title=_extract_title(body),
    )


async def _http_probe(url: str, *, platform: str, timeout: float) -> UrlProbeResult:
    checked = _strip_url(url)
    if not checked:
        return UrlProbeResult(ok=False, checked_url="", hard_fail=True, error="empty URL")

    try:
        async with httpx.AsyncClient(**_client_kwargs(platform, timeout)) as client:
            if platform in _SOCIAL:
                response = await client.get(checked)
            else:
                try:
                    response = await client.head(checked)
                    if response.status_code in (405, 501) or response.status_code >= 400:
                        response = await client.get(checked)
                except httpx.HTTPError:
                    response = await client.get(checked)
    except httpx.TimeoutException:
        return UrlProbeResult(ok=False, checked_url=checked, hard_fail=True, error="timed out")
    except httpx.HTTPError as exc:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            hard_fail=True,
            error=f"{type(exc).__name__}: {exc}"[:240],
        )

    body = ""
    try:
        body = response.text[:100_000]
    except Exception:
        body = ""
    return _interpret(
        checked,
        platform=platform,
        final=str(response.url),
        status_code=response.status_code,
        body=body,
        title=_extract_title(body),
    )


def _playwright_probe_facebook(page, url: str) -> UrlProbeResult:
    """Evaluate a Facebook URL in an already-open Playwright page."""
    from app.services.facebook_reels import _dismiss_facebook_overlays

    checked = _strip_url(url)
    if not checked:
        return UrlProbeResult(ok=False, checked_url="", hard_fail=True, error="empty URL")

    try:
        response = page.goto(checked, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2200)
        try:
            _dismiss_facebook_overlays(page)
        except Exception:
            pass
        page.wait_for_timeout(400)
        final = str(page.url or checked)
        title = ""
        try:
            title = page.title() or ""
        except Exception:
            title = ""
        try:
            body = page.inner_text("body")[:8000]
        except Exception:
            body = ""
        status_code = response.status if response else 200
    except Exception as exc:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            hard_fail=False,
            inconclusive=True,
            error=f"browser check failed: {type(exc).__name__}: {exc}"[:240],
        )

    redirected = _normalize_compare_url(final, "facebook") != _normalize_compare_url(
        checked, "facebook"
    )
    identity_changed = _identity_key(final, "facebook") != _identity_key(checked, "facebook")
    lower_final = final.lower()
    lower_body = body.lower()

    if _body_has_dead_marker(lower_body) or _body_has_dead_marker(title):
        # Logged-out / partial FB sessions often show "isn't available" on live pages.
        # Do not paint the source red unless the HTTP status is a real not-found.
        if status_code not in (404, 410):
            return UrlProbeResult(
                ok=False,
                checked_url=checked,
                final_url=final,
                status_code=status_code,
                redirected=redirected,
                identity_changed=identity_changed,
                hard_fail=False,
                inconclusive=True,
                error="unavailable wording — could not verify (not marked dead)",
            )
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            identity_changed=identity_changed,
            hard_fail=True,
            error="content not available",
        )

    if identity_changed:
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=True,
            identity_changed=True,
            hard_fail=False,
            error=f"identity changed → {final}",
        )

    if "/login" in lower_final or "log in" in lower_body[:400]:
        # Logged-out interstitial — not proof the page is dead.
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            hard_fail=False,
            inconclusive=True,
            error="login wall — connect Facebook in Access, then recheck",
        )

    if status_code in (404, 410):
        return UrlProbeResult(
            ok=False,
            checked_url=checked,
            final_url=final,
            status_code=status_code,
            redirected=redirected,
            hard_fail=True,
            error=f"HTTP {status_code} — URL not found",
        )

    return UrlProbeResult(
        ok=True,
        checked_url=checked,
        final_url=final,
        status_code=status_code,
        redirected=redirected,
        hard_fail=False,
        error=None,
    )


class FacebookBrowserProbe:
    """Reuse one Chromium context across many Facebook URL checks."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self) -> FacebookBrowserProbe:
        import asyncio
        import sys

        from playwright.sync_api import sync_playwright

        from app.services.facebook_reels import _load_facebook_storage_state

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        storage = _load_facebook_storage_state()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context_kwargs: dict = {
            "user_agent": _UA,
            "viewport": {"width": 1280, "height": 900},
            "locale": "en-US",
        }
        if storage:
            context_kwargs["storage_state"] = storage
        self._context = self._browser.new_context(**context_kwargs)
        self._page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._context is not None:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser is not None:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    def probe(self, url: str) -> UrlProbeResult:
        if self._page is None:
            return UrlProbeResult(
                ok=False,
                checked_url=_strip_url(url),
                inconclusive=True,
                error="browser not started",
            )
        return _playwright_probe_facebook(self._page, url)


def probe_url_sync(
    url: str,
    *,
    platform: str = "website",
    timeout: float = 10.0,
    browser: FacebookBrowserProbe | None = None,
) -> UrlProbeResult:
    platform_key = platform if isinstance(platform, str) else str(platform)

    if platform_key in _BROWSER_PLATFORMS:
        if browser is not None:
            return browser.probe(url)
        try:
            with FacebookBrowserProbe() as fb:
                return fb.probe(url)
        except Exception as exc:
            # Fall through to HTTP so callers still get a structured result.
            http_result = _http_probe_sync(url, platform=platform_key, timeout=timeout)
            if http_result.inconclusive or http_result.ok:
                return UrlProbeResult(
                    ok=False,
                    checked_url=_strip_url(url),
                    hard_fail=False,
                    inconclusive=True,
                    error=f"browser check unavailable: {type(exc).__name__}: {exc}"[:240],
                )
            return http_result

    return _http_probe_sync(url, platform=platform_key, timeout=timeout)


async def probe_url(
    url: str,
    *,
    platform: str = "website",
    timeout: float = 10.0,
) -> UrlProbeResult:
    import asyncio

    platform_key = platform if isinstance(platform, str) else str(platform)
    if platform_key in _BROWSER_PLATFORMS:
        return await asyncio.to_thread(probe_url_sync, url, platform=platform_key, timeout=timeout)
    return await _http_probe(url, platform=platform_key, timeout=timeout)


def _rollup(results: list[tuple[str, UrlProbeResult]]) -> dict:
    details: list[dict] = []
    fails: list[UrlProbeResult] = []
    inconclusives: list[UrlProbeResult] = []
    oks = 0
    for label, result in results:
        details.append(
            {
                "target": label,
                "checked_url": result.checked_url,
                "final_url": result.final_url,
                "status_code": result.status_code,
                "ok": result.ok,
                "redirected": result.redirected,
                "identity_changed": result.identity_changed,
                "inconclusive": result.inconclusive,
                "error": result.error,
            }
        )
        if result.inconclusive:
            inconclusives.append(result)
        elif result.ok:
            oks += 1
        else:
            fails.append(result)

    if fails:
        first = fails[0]
        return {
            "ok": False,
            "hard_fail": any(item.hard_fail for item in fails),
            "identity_changed": any(item.identity_changed for item in fails),
            "inconclusive": False,
            "error": first.error,
            "details": details,
        }

    source_ok = any(
        label == "source" and result.ok and not result.inconclusive
        for label, result in results
    )
    if oks and (not inconclusives or source_ok):
        return {
            "ok": True,
            "hard_fail": False,
            "identity_changed": False,
            "inconclusive": False,
            "error": None,
            "details": details,
        }

    return {
        "ok": False,
        "hard_fail": False,
        "identity_changed": False,
        "inconclusive": True,
        "error": (inconclusives[0].error if inconclusives else "could not verify URL"),
        "details": details,
    }


def check_source_urls_sync(
    *,
    platform: str,
    source_url: str,
    stream_urls: list[str] | None = None,
    browser: FacebookBrowserProbe | None = None,
) -> dict:
    platform_key = platform if isinstance(platform, str) else str(platform)
    targets: list[tuple[str, str]] = [("source", source_url)]
    for i, stream_url in enumerate(stream_urls or []):
        if stream_url and stream_url.strip():
            targets.append((f"stream:{i}", stream_url))
    results = [
        (
            label,
            probe_url_sync(target, platform=platform_key, browser=browser),
        )
        for label, target in targets
    ]
    return _rollup(results)


async def check_source_urls(
    *,
    platform: str,
    source_url: str,
    stream_urls: list[str] | None = None,
) -> dict:
    import asyncio

    return await asyncio.to_thread(
        check_source_urls_sync,
        platform=platform,
        source_url=source_url,
        stream_urls=stream_urls,
    )


def apply_url_check_to_source(source, result: dict, *, now) -> None:
    """Persist probe rollup onto a Source row."""
    from app.models.source import SourceStatus

    source.last_url_check = now

    # Inconclusive (bot wall / no session): do not paint green or red.
    if result.get("inconclusive") and not result.get("hard_fail"):
        return

    if result["ok"]:
        if source.error_message and str(source.error_message).startswith(URL_CHECK_PREFIX):
            source.error_message = None
        if source.status == SourceStatus.error and not source.error_message:
            source.status = SourceStatus.active
        return

    msg = result.get("error") or "failed"
    source.error_message = f"{URL_CHECK_PREFIX}{msg}"[:1024]
    if result.get("hard_fail"):
        source.status = SourceStatus.error
