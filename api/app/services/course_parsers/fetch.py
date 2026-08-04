"""Fetch ladder: HTTP → cloudscraper → Playwright."""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 MediaIntelligence/1.0"
)


@dataclass
class FetchResult:
    html: str
    final_url: str
    mode: str
    status_code: int


def _playwright_executable() -> str:
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise RuntimeError("No suitable browser found for Playwright")


def fetch_html(url: str, *, prefer_js: bool = False) -> FetchResult:
    """Return rendered or raw HTML using escalating fetch strategies."""
    url = (url or "").strip()
    if not url.startswith("http"):
        raise ValueError("URL must start with http(s)")

    if not prefer_js:
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
                resp = client.get(url)
                html = resp.text or ""
                if resp.status_code == 200 and len(html) > 500 and "cf-browser-verification" not in html.lower():
                    return FetchResult(html=html, final_url=str(resp.url), mode="http", status_code=resp.status_code)
        except Exception:
            pass

        try:
            import cloudscraper

            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url, timeout=30, headers={"User-Agent": USER_AGENT})
            html = resp.text or ""
            if resp.status_code == 200 and len(html) > 500:
                return FetchResult(
                    html=html,
                    final_url=str(resp.url),
                    mode="cloudscraper",
                    status_code=resp.status_code,
                )
        except ImportError:
            pass
        except Exception:
            pass

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=_playwright_executable())
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)
        html = page.content()
        final = page.url
        browser.close()
    return FetchResult(html=html, final_url=final, mode="playwright", status_code=200)


def guess_hub_path_prefix(url: str) -> str:
    """Default article path prefix from hub URL path (e.g. /learn/soc-2)."""
    path = urlparse(url).path.rstrip("/")
    return path if path else "/"
