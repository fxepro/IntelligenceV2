"""
Facebook Reels link discovery via Playwright (sync API).

yt-dlp cannot list public page reels without auth. This scraper opens the
page's reels tab, scrolls to load the grid, and collects every /reel/{id}
URL. Video bytes are not downloaded here — only links + light metadata
for the media_items catalog. Incremental refresh is handled by the
caller via on_conflict_do_nothing on canonical_url.

FB virtualizes the DOM (~keeps a window of tiles) and paginates via
GraphQL — so we accumulate IDs every scroll from (1) visible anchors,
(2) HTML/JSON blobs, and (3) intercepted GraphQL responses. A single
page-source dump will falsely look capped around ~70.

Any Facebook page/profile URL is normalized into its reels tab:
  - vanity:  https://www.facebook.com/Handle        → …/Handle/reels
  - numeric: https://www.facebook.com/profile.php?id=123
             → …/profile.php?id=123&sk=reels_tab

Uses the sync Playwright API so it can run safely inside uvicorn's
thread-pool executor on Windows (async subprocess transport is flaky there).
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse, urlunparse

from playwright.sync_api import sync_playwright

_REEL_ID_RE = re.compile(r"/reel/(\d+)")
_PROFILE_ID_RE = re.compile(r"(?:^|[?&])id=(\d+)", re.I)
_PEOPLE_ID_RE = re.compile(r"/people/[^/]+/(\d+)", re.I)
_PATH_ID_RE = re.compile(r"/(\d{10,})/?$")
_PLACEHOLDER_TITLE_RE = re.compile(
    r"^(reel\s*tile\s*preview|tile\s*preview|preview|reels?|facebook\s*reel)$",
    re.I,
)


def clean_reel_title(title: str | None) -> str | None:
    """Drop FB placeholder aria-labels like 'Reel tile preview'."""
    if not title:
        return None
    text = " ".join(str(title).split()).strip()
    if not text:
        return None
    if _PLACEHOLDER_TITLE_RE.match(text) or "tile preview" in text.lower():
        return None
    return text[:240]


def extract_facebook_profile_id(url: str) -> str | None:
    """Return numeric profile/page id from query, /people/Name/ID, or trailing path id."""
    raw = (url or "").strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query)
    if "id" in qs and qs["id"] and qs["id"][0].isdigit():
        return qs["id"][0]
    m = _PROFILE_ID_RE.search(raw)
    if m:
        return m.group(1)
    m = _PEOPLE_ID_RE.search(parsed.path or "")
    if m:
        return m.group(1)
    m = _PATH_ID_RE.search(parsed.path or "")
    if m:
        return m.group(1)
    return None


# Vanity page HTML embeds: {"6158…":{"page_id":"6158…","page_id_type":"page"
_PAGE_ID_TYPED_RE = re.compile(
    r'"page_id"\s*:\s*"(\d+)"\s*,\s*"page_id_type"\s*:\s*"page"',
    re.I,
)
_PAGE_ID_TYPED_ESC_RE = re.compile(
    r'\\"page_id\\"\s*:\s*\\"(\d+)\\"\s*,\s*\\"page_id_type\\"\s*:\s*\\"page\\"',
    re.I,
)
_USER_ID_RE = re.compile(r'"userID"\s*:\s*"(\d+)"', re.I)
_USER_ID_ESC_RE = re.compile(r'\\"userID\\"\s*:\s*\\"(\d+)\\"', re.I)


def extract_facebook_page_id_from_html(html: str) -> str | None:
    """Pull numeric page/profile id from Facebook page source (vanity pages included)."""
    text = html or ""
    for pattern in (_PAGE_ID_TYPED_RE, _PAGE_ID_TYPED_ESC_RE):
        m = pattern.search(text)
        if m:
            return m.group(1)
    for pattern in (_USER_ID_RE, _USER_ID_ESC_RE):
        m = pattern.search(text)
        if m:
            return m.group(1)
    # Last resort: bare page_id without type (weaker).
    m = re.search(r'"page_id"\s*:\s*"(\d{8,})"', text)
    if m:
        return m.group(1)
    m = re.search(r'\\"page_id\\"\s*:\s*\\"(\d{8,})\\"', text)
    if m:
        return m.group(1)
    return None


def facebook_identity_url(page_id: str) -> str:
    return f"https://www.facebook.com/profile.php?id={page_id}"


def normalize_facebook_vanity_url(url: str) -> str:
    """Strip reels/tab junk; keep vanity path when no numeric id in the URL."""
    base = normalize_facebook_page_url(url)
    if extract_facebook_profile_id(base):
        return base
    return base.rstrip("/")


def resolve_facebook_identity_from_vanity(url: str) -> tuple[str, str | None, str | None]:
    """
    Resolve vanity (or any FB page URL) → (vanity_url, identity_url, page_id).

    identity_url is profile.php?id=… when page source yields a page_id.
    Uses Access session Playwright when available; HTTP fallback otherwise.
    """
    raw = (url or "").strip()
    if not raw:
        return "", None, None

    # Already an id URL — nothing to scrape.
    existing_id = extract_facebook_profile_id(raw)
    if existing_id:
        identity = facebook_identity_url(existing_id)
        return identity, identity, existing_id

    vanity = normalize_facebook_vanity_url(raw)
    html = _fetch_facebook_page_html(vanity)
    page_id = extract_facebook_page_id_from_html(html or "")
    if not page_id:
        return vanity, None, None
    identity = facebook_identity_url(page_id)
    return vanity, identity, page_id


def _fetch_facebook_page_html(url: str) -> str | None:
    """Best-effort HTML for id extraction (Playwright + session preferred)."""
    try:
        return _fetch_facebook_html_playwright(url)
    except Exception:
        pass
    try:
        import httpx

        from app.services.platform_sessions import load_connected_session

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        cookies = None
        state = load_connected_session("facebook")
        if state and state.get("cookies"):
            cookies = {
                str(c["name"]): str(c.get("value") or "")
                for c in state["cookies"]
                if isinstance(c, dict) and c.get("name")
            }
        with httpx.Client(
            headers=headers,
            cookies=cookies,
            follow_redirects=True,
            timeout=20.0,
        ) as client:
            resp = client.get(url)
            if resp.status_code < 500 and resp.text:
                return resp.text
    except Exception:
        return None
    return None


def _safe_playwright_close(*closables) -> None:
    """Close Playwright objects; ignore already-dead targets."""
    for obj in closables:
        if obj is None:
            continue
        try:
            obj.close()
        except Exception:
            pass


def _fetch_facebook_html_playwright(url: str) -> str | None:
    import sys
    import asyncio

    from playwright.sync_api import sync_playwright

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    storage = _load_facebook_storage_state()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            ctx_kwargs: dict = {
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "viewport": {"width": 1280, "height": 900},
                "locale": "en-US",
            }
            if storage:
                ctx_kwargs["storage_state"] = storage
            context = browser.new_context(**ctx_kwargs)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            return page.content()
        finally:
            _safe_playwright_close(browser)


def normalize_facebook_page_url(url: str) -> str:
    """
    Canonical page/profile base URL (no reels tab).

    Always prefers profile.php?id=… when a numeric id is present (vanity and
    /people/Name/ID forms both collapse to this stable form).
    """
    raw = url.strip()
    parsed = urlparse(raw)
    path = (parsed.path or "/").rstrip("/") or "/"

    for suffix in ("/reels", "/reels_tab", "/videos", "/about", "/posts", "/photos", "/live"):
        if path.lower().endswith(suffix):
            path = path[: -len(suffix)] or "/"
            break

    profile_id = extract_facebook_profile_id(raw)
    if profile_id:
        return f"https://www.facebook.com/profile.php?id={profile_id}"

    if path.lower().endswith("profile.php"):
        return "https://www.facebook.com/profile.php"

    return urlunparse(("https", "www.facebook.com", path, "", "", "")).rstrip("/")


def reels_tab_url(page_url: str) -> str:
    """
    Convert any Facebook page/profile URL into its Reels tab URL.

    Page → reels mapping:
      profile.php?id=123  →  profile.php?id=123&sk=reels_tab
      /people/Name/123    →  profile.php?id=123&sk=reels_tab
      /Handle             →  /Handle/reels
    """
    profile_id = extract_facebook_profile_id(page_url)
    if profile_id:
        return f"https://www.facebook.com/profile.php?id={profile_id}&sk=reels_tab"
    base = normalize_facebook_page_url(page_url)
    profile_id = extract_facebook_profile_id(base)
    if profile_id:
        return f"https://www.facebook.com/profile.php?id={profile_id}&sk=reels_tab"
    return f"{base.rstrip('/')}/reels"


def _reel_id(href: str) -> str | None:
    m = _REEL_ID_RE.search(href or "")
    return m.group(1) if m else None


def _canonical_reel_url(reel_id: str) -> str:
    return f"https://www.facebook.com/reel/{reel_id}"


def parse_view_count(raw: str | None) -> int | None:
    if not raw:
        return None
    s = raw.strip().upper().replace(",", "").replace(" ", "")
    mult = 1
    if s.endswith("K"):
        mult = 1_000
        s = s[:-1]
    elif s.endswith("M"):
        mult = 1_000_000
        s = s[:-1]
    elif s.endswith("B"):
        mult = 1_000_000_000
        s = s[:-1]
    try:
        return int(float(s) * mult)
    except ValueError:
        return None



def _harvest_reel_anchors(page) -> list[dict]:
    """Pull /reel/{id} tiles currently in the owner reels grid DOM (not sidebar suggestions)."""
    return page.evaluate(
        """() => {
          const out = [];
          const seen = new Set();
          // Prefer anchors inside the main reels grid; fall back to all page reel links.
          const main = document.querySelector('[role="main"]') || document.body;
          const anchors = Array.from(main.querySelectorAll('a[href*="/reel/"]'));
          for (const a of anchors) {
            const href = a.href || '';
            const m = href.match(/\\/reel\\/(\\d+)/);
            if (!m) continue;
            const id = m[1];
            if (seen.has(id)) continue;
            seen.add(id);
            let title = (a.getAttribute('aria-label') || a.innerText || '').trim();
            title = title.replace(/\\s+/g, ' ').slice(0, 240) || null;
            if (title) {
              const low = title.toLowerCase();
              if (
                low === 'reel tile preview'
                || low === 'tile preview'
                || low === 'preview'
                || low.includes('tile preview')
              ) {
                title = null;
              }
            }
            let thumb = null;
            const img = a.querySelector('img');
            if (img) {
              thumb = img.currentSrc || img.src || img.getAttribute('data-src') || null;
              if (thumb && (thumb.startsWith('data:') || thumb.startsWith('blob:'))) thumb = null;
              if ((!title || !title.trim())) {
                const alt = (img.getAttribute('alt') || '').trim();
                if (alt && !/tile preview/i.test(alt) && alt.toLowerCase() !== 'preview') {
                  title = alt.slice(0, 240);
                }
              }
            }
            if (!thumb) {
              const bgEl = a.querySelector('[style*="background-image"]');
              const style = bgEl ? (bgEl.getAttribute('style') || '') : '';
              const bm = style.match(/background-image:\\s*url\\([\"']?([^\"')]+)[\"']?\\)/i);
              if (bm && bm[1] && !bm[1].startsWith('data:')) thumb = bm[1];
            }
            let views = null;
            const labeled = a.querySelector('[aria-label*="view" i]');
            if (labeled) {
              const t = labeled.getAttribute('aria-label') || '';
              const vm = t.match(/([\\d,.]+\\s*[KMB]?)\\s*views?/i);
              if (vm) views = vm[1];
            }
            // Duration overlay like 0:45 / 1:02 on the tile
            let duration = null;
            const blob = ((a.getAttribute('aria-label') || '') + ' ' + (a.innerText || '')).trim();
            const dm = blob.match(/\\b(\\d{1,2}):([0-5]\\d)\\b/);
            if (dm) duration = parseInt(dm[1], 10) * 60 + parseInt(dm[2], 10);
            if (!duration) {
              for (const el of a.querySelectorAll('span, div')) {
                const t = (el.textContent || '').trim();
                if (!/^\\d{1,2}:[0-5]\\d$/.test(t)) continue;
                const parts = t.split(':');
                duration = parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
                break;
              }
            }
            out.push({ id, href, title, thumb, views, duration });
          }
          return out;
        }"""
    ) or []


def _harvest_reel_ids_from_html(page) -> list[str]:
    """
    FB virtualizes the reels grid — old <a href="/reel/…"> nodes are discarded
    as you scroll. IDs often linger in script/JSON blobs longer than in tiles,
    so scrape the document HTML each round and merge into the accumulator.
    """
    return page.evaluate(
        """() => {
          const html = document.documentElement ? document.documentElement.innerHTML : '';
          const out = new Set();
          const patterns = [
            /\\/reel\\/(\\d+)/g,
            /"video_id"\\s*:\\s*"(\\d+)"/g,
            /"legacy_video_id"\\s*:\\s*"(\\d+)"/g,
          ];
          for (const re of patterns) {
            let m;
            while ((m = re.exec(html)) !== null) out.add(m[1]);
          }
          return [...out];
        }"""
    ) or []


def _ingest_text_for_reel_ids(text: str, collected: dict[str, dict], max_items: int) -> int:
    """
    Disabled for creating new catalog rows.

    Scraping every /reel/ id or video_id from HTML/GraphQL pulls suggested
    reels and unrelated video ids, so Play opens the wrong clip. New IDs must
    come from visible owner-grid tiles or the active viewer URL only.
    """
    return 0


def _attach_graphql_reel_sniffer(page, collected: dict[str, dict], max_items: int) -> None:
    """No-op: GraphQL payloads mix owner reels with recommendations."""
    return


def _hydrate_durations_from_page(page, collected: dict[str, dict]) -> int:
    """
    Attach playable_duration to IDs we already collected — from FB JSON in the
    page HTML. Does not create new IDs (avoids suggested-reel pollution).
    """
    if not collected:
        return 0
    try:
        mapping = page.evaluate(
            """() => {
              const html = document.documentElement
                ? document.documentElement.innerHTML
                : '';
              const out = {};
              const addMs = (id, ms) => {
                if (!id || ms == null) return;
                const sec = Math.max(1, Math.round(Number(ms) / 1000));
                if (!out[id] || sec > out[id]) out[id] = sec;
              };
              const addSec = (id, sec) => {
                if (!id || sec == null) return;
                const s = Math.max(1, Math.round(Number(sec)));
                if (!out[id] || s > out[id]) out[id] = s;
              };
              let m;
              const re1 = /"video_id"\\s*:\\s*"(\\d+)"[\\s\\S]{0,500}?"playable_duration_in_ms"\\s*:\\s*(\\d+)/g;
              while ((m = re1.exec(html)) !== null) addMs(m[1], m[2]);
              const re2 = /"playable_duration_in_ms"\\s*:\\s*(\\d+)[\\s\\S]{0,500}?"video_id"\\s*:\\s*"(\\d+)"/g;
              while ((m = re2.exec(html)) !== null) addMs(m[2], m[1]);
              const re3 = /"id"\\s*:\\s*"(\\d+)"[\\s\\S]{0,300}?"length_in_second"\\s*:\\s*(\\d+)/g;
              while ((m = re3.exec(html)) !== null) addSec(m[1], m[2]);
              const re4 = /"length_in_second"\\s*:\\s*(\\d+)[\\s\\S]{0,300}?"id"\\s*:\\s*"(\\d+)"/g;
              while ((m = re4.exec(html)) !== null) addSec(m[2], m[1]);
              return out;
            }"""
        ) or {}
    except Exception:
        return 0
    updated = 0
    for rid, sec in mapping.items():
        if rid not in collected:
            continue
        try:
            seconds = int(sec)
        except (TypeError, ValueError):
            continue
        if seconds <= 0:
            continue
        if not collected[rid].get("duration_seconds"):
            collected[rid]["duration_seconds"] = seconds
            updated += 1
    return updated


def _merge_dom_batch(batch: list[dict], collected: dict[str, dict], max_items: int) -> int:
    """Merge owner-grid tiles. New IDs require a thumbnail (complete tile only)."""
    added = 0
    for row in batch:
        rid = row.get("id") or _reel_id(row.get("href") or "")
        if not rid:
            continue
        title = clean_reel_title(row.get("title"))
        thumb = (row.get("thumb") or "").strip() or None
        if rid in collected:
            # Enrich metadata if a later tile has title/thumb
            existing = collected[rid]
            if not clean_reel_title(existing.get("title")) and title:
                existing["title"] = title
            if not existing.get("thumbnail_url") and thumb:
                existing["thumbnail_url"] = thumb
            if not existing.get("view_count_raw") and row.get("views"):
                existing["view_count_raw"] = row.get("views")
            if not existing.get("duration_seconds") and row.get("duration"):
                try:
                    existing["duration_seconds"] = int(row["duration"])
                except (TypeError, ValueError):
                    pass
            continue
        # Incomplete tiles are skipped — never invent a row without art.
        if not thumb:
            continue
        duration = None
        if row.get("duration") is not None:
            try:
                duration = int(row["duration"])
            except (TypeError, ValueError):
                duration = None
        collected[rid] = {
            "id": rid,
            "url": _canonical_reel_url(rid),
            "title": title,
            "thumbnail_url": thumb,
            "view_count_raw": row.get("views"),
            "duration_seconds": duration,
        }
        added += 1
        if len(collected) >= max_items:
            break
    return added


def _scroll_reels_feed(page) -> None:
    """
    Facebook's reels grid often ignores mouse.wheel alone (logged-out
    sessions stall at ~10 tiles). PageDown + window.scrollBy loads the rest.
    Avoid clicking the grid — that opens a reel overlay and freezes discovery.
    """
    page.evaluate(
        """() => {
          const scrollers = Array.from(document.querySelectorAll('div')).filter(d => {
            const s = getComputedStyle(d);
            return (s.overflowY === 'auto' || s.overflowY === 'scroll')
              && d.scrollHeight > d.clientHeight + 200
              && d.clientHeight > 300;
          });
          for (const d of scrollers) {
            d.scrollTop = Math.min(d.scrollTop + 2400, d.scrollHeight);
          }
          window.scrollBy(0, 2400);
          document.documentElement.scrollTop = (document.documentElement.scrollTop || 0) + 2400;
        }"""
    )
    page.mouse.move(700, 700)
    page.mouse.wheel(0, 4000)
    try:
        page.keyboard.press("PageDown")
        page.keyboard.press("PageDown")
        page.keyboard.press("End")
    except Exception:
        pass


def _current_reel_id(page) -> str | None:
    try:
        return _reel_id(page.url or "")
    except Exception:
        return None


def _viewer_reel_thumb(page) -> str | None:
    """Best-effort poster/og image for the reel currently open in the viewer."""
    try:
        return page.evaluate(
            """() => {
              const og = document.querySelector('meta[property="og:image"]');
              if (og && og.content && !og.content.startsWith('data:')) return og.content;
              const vid = document.querySelector('video');
              if (vid) {
                const p = vid.getAttribute('poster');
                if (p && !p.startsWith('data:')) return p;
              }
              const imgs = Array.from(document.querySelectorAll('img'));
              for (const img of imgs) {
                const src = img.currentSrc || img.src || '';
                if (!src || src.startsWith('data:') || src.startsWith('blob:')) continue;
                if (/scontent|fbcdn|facebook/i.test(src) && img.naturalWidth >= 120) return src;
              }
              return null;
            }"""
        )
    except Exception:
        return None


def _walk_reel_viewer(
    page,
    collected: dict[str, dict],
    max_items: int,
    *,
    max_steps: int = 200,
    idle_limit: int = 12,
) -> None:
    """
    Depth path after the owner grid soft-caps: walk the fullscreen viewer
    (owner feed when seeded from a grid tile). Only keep reels that yield a thumb.
    """
    if len(collected) >= max_items or not collected:
        return

    # Prefer a DOM-harvested tile (has thumb/title) so the viewer opens an owner reel.
    seed_id = next(
        (rid for rid, row in collected.items() if row.get("thumbnail_url") or row.get("title")),
        next(iter(collected)),
    )
    try:
        page.goto(_canonical_reel_url(seed_id), wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
    except Exception:
        return

    stagnant = 0
    last_seen = _current_reel_id(page)
    for _ in range(max_steps):
        if len(collected) >= max_items:
            break

        before = len(collected)
        # Only the reel currently open in the viewer — never vacuum HTML here.
        rid = _current_reel_id(page)
        if rid and rid not in collected:
            thumb = (_viewer_reel_thumb(page) or "").strip() or None
            if thumb:
                duration = None
                try:
                    duration = page.evaluate(
                        """() => {
                          const v = document.querySelector('video');
                          if (v && isFinite(v.duration) && v.duration > 0)
                            return Math.round(v.duration);
                          return null;
                        }"""
                    )
                except Exception:
                    duration = None
                collected[rid] = {
                    "id": rid,
                    "url": _canonical_reel_url(rid),
                    "title": None,
                    "thumbnail_url": thumb,
                    "view_count_raw": None,
                    "duration_seconds": int(duration) if duration else None,
                }
        elif rid and rid in collected and not collected[rid].get("duration_seconds"):
            try:
                duration = page.evaluate(
                    """() => {
                      const v = document.querySelector('video');
                      if (v && isFinite(v.duration) && v.duration > 0)
                        return Math.round(v.duration);
                      return null;
                    }"""
                )
                if duration:
                    collected[rid]["duration_seconds"] = int(duration)
            except Exception:
                pass
        _hydrate_durations_from_page(page, collected)

        # Advance to next reel in the owner feed
        advanced = False
        for key in ("ArrowDown", "ArrowRight"):
            try:
                page.keyboard.press(key)
                advanced = True
                break
            except Exception:
                pass
        if not advanced:
            try:
                nxt = page.get_by_role("button", name=re.compile(r"Next|Go to next", re.I))
                if nxt.count():
                    nxt.first.click(timeout=1500)
                    advanced = True
            except Exception:
                pass
        page.wait_for_timeout(1400)

        now = _current_reel_id(page)
        if len(collected) == before and now == last_seen:
            stagnant += 1
            if stagnant >= idle_limit:
                break
        else:
            stagnant = 0
            last_seen = now or last_seen


def _load_facebook_storage_state() -> dict | None:
    """Best-effort: load connected Facebook session from DB (sync)."""
    try:
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import Session
        from app.config import get_settings
        from app.models.platform_credential import PlatformCredential, CredentialStatus
        from app.models.source import Platform

        engine = create_engine(get_settings().database_url_sync)
        with Session(engine) as db:
            row = db.scalar(
                select(PlatformCredential).where(
                    PlatformCredential.platform == Platform.facebook,
                    PlatformCredential.status == CredentialStatus.connected,
                ).order_by(PlatformCredential.updated_at.desc()).limit(1)
            )
            if row and row.session_json:
                state = dict(row.session_json)
                cookies = state.get("cookies") or []
                names = {c.get("name") for c in cookies}
                # Tracking cookies alone are not a login — require auth cookies.
                if "c_user" in names and "xs" in names:
                    return state
    except Exception:
        return None
    return None


def _dismiss_facebook_overlays(page) -> None:
    """Cookie banners + login walls block the reels grid and clicks."""
    for label in (
        "Allow all cookies",
        "Accept All",
        "Decline optional cookies",
        "Not Now",
        "Close",
        "No thanks",
    ):
        try:
            btn = page.get_by_role("button", name=re.compile(label, re.I))
            if btn.count():
                btn.first.click(timeout=1200, force=True)
                page.wait_for_timeout(300)
        except Exception:
            pass
    try:
        # Login wall / interstitial dialogs
        for sel in ('[aria-label="Close"]', '[aria-label="Close dialog"]', 'div[role="dialog"] [aria-label="Close"]'):
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=1000, force=True)
                page.wait_for_timeout(250)
    except Exception:
        pass


def scrape_facebook_reels_sync(
    page_url: str,
    max_items: int = 200,
    max_scrolls: int = 50,
    idle_rounds: int = 6,
) -> tuple[list[dict], str]:
    """
    Collect reel links from a public Facebook page (blocking).

    Converts any page/profile URL → reels tab, follows Facebook redirects
    to profile.php?id=… when a vanity handle resolves, then scrapes.

    Uses a saved Facebook session (Settings → Access) when available so
    logged-in catalogs can exceed the public ~70-tile cap.

    Returns (items, resolved_reels_tab_url).
    items: id, url, title, thumbnail_url, view_count_raw.
    """
    import sys
    import asyncio

    # Uvicorn on Windows can leave SelectorEventLoop as the default policy;
    # Playwright needs ProactorEventLoop to spawn Chromium subprocesses.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Start from the page (not always /reels) so FB can redirect vanity → profile.php?id=
    start = normalize_facebook_page_url(page_url)
    target = reels_tab_url(page_url)
    collected: dict[str, dict] = {}
    resolved_reels = target
    storage = _load_facebook_storage_state()
    # Scale scroll budget with requested depth (virtualized grid needs many page-downs).
    max_scrolls = max(max_scrolls, min(260, max(80, max_items // 2)))
    idle_rounds = max(idle_rounds, 14 if max_items >= 300 else 10)
    if storage:
        max_scrolls = max(max_scrolls, 140)
        idle_rounds = max(idle_rounds, 12)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        context_kwargs: dict = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1400, "height": 1100},
            "locale": "en-US",
        }
        if storage:
            context_kwargs["storage_state"] = storage
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        _attach_graphql_reel_sniffer(page, collected, max_items)
        try:
            # Go straight to the reels tab. Visiting the base profile first can
            # put logged-out sessions into a stuck ~10-tile preview grid.
            page.goto(target, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            _dismiss_facebook_overlays(page)

            for label in ("Allow all cookies", "Accept All", "Decline optional cookies", "Close"):
                try:
                    btn = page.get_by_role("button", name=re.compile(label, re.I))
                    if btn.count():
                        btn.first.click(timeout=1500)
                        page.wait_for_timeout(400)
                except Exception:
                    pass

            # If vanity didn't resolve / empty grid, open the base page once to
            # capture Handle → profile.php?id=… redirects, then reopen reels.
            if (page.eval_on_selector_all('a[href*="/reel/"]', "els => els.length") or 0) == 0:
                page.goto(start, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
                landed = page.url or start
                resolved_reels = reels_tab_url(landed if extract_facebook_profile_id(landed) else page_url)
                page.goto(resolved_reels, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

            # Stay on whatever FB actually served (/people/Name/ID/?sk=reels_tab
            # works; forcing profile.php?id=… often caps the grid at ~10).
            landed_reels = page.url or target
            if "sk=reels" in landed_reels or "/reels" in (urlparse(landed_reels).path or ""):
                resolved_reels = landed_reels
            else:
                resolved_reels = reels_tab_url(landed_reels)
                page.goto(resolved_reels, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                resolved_reels = page.url or resolved_reels

            # Don't click owner_reels — for logged-out scrapes it often swaps the
            # working /people/…/?sk=reels_tab grid for a stuck ~10-tile preview.

            # If still no reel anchors, try clicking the Reels tab link
            def _count_reels() -> int:
                return page.eval_on_selector_all('a[href*="/reel/"]', "els => els.length") or 0

            if _count_reels() == 0:
                for name in (r"^Reels$", r"Reels"):
                    try:
                        link = page.get_by_role("link", name=re.compile(name, re.I))
                        if link.count():
                            link.first.click(timeout=2000)
                            page.wait_for_timeout(2500)
                            break
                    except Exception:
                        pass

            # Seed only from visible owner-grid tiles (not HTML/GraphQL vacuum).
            _merge_dom_batch(_harvest_reel_anchors(page), collected, max_items)
            _hydrate_durations_from_page(page, collected)

            stagnant = 0
            for _ in range(max_scrolls):
                before = len(collected)

                # Visible tiles only — titles + thumbs from the owner grid.
                _merge_dom_batch(_harvest_reel_anchors(page), collected, max_items)
                _hydrate_durations_from_page(page, collected)

                if len(collected) >= max_items:
                    break

                if len(collected) == before:
                    stagnant += 1
                    if stagnant >= idle_rounds:
                        break
                else:
                    stagnant = 0

                _scroll_reels_feed(page)
                page.wait_for_timeout(1800)

            # Final duration pass on whatever JSON is still in the DOM.
            _hydrate_durations_from_page(page, collected)

            # Do NOT walk the fullscreen reel viewer for catalog growth.
            # ArrowDown leaves the owner grid and the SPA keeps a sticky
            # og:image/poster, so we mint hundreds of foreign reel IDs that
            # all share the same thumbnail. Owner grid scroll only.

        finally:
            _safe_playwright_close(context, browser)

    return list(collected.values()), resolved_reels
