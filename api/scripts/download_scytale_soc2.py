"""
Download Scytale SOC 2 Academy curriculum text (authenticated).

Uses platform_credentials (platform=website) password.
Writes under v2/data/scytale-soc2/ (gitignored).

  cd v2/api
  python scripts/download_scytale_soc2.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.platform_credential import PlatformCredential
from app.models.source import Platform
from app.services.credential_crypto import decrypt_secret

SITE = "https://academy.scytale.ai"
COURSE_HOME = f"{SITE}/courses/take/scytale-SOC-2-academy/"
SIGN_IN = f"{SITE}/users/sign_in"
OUT_DIR = ROOT / "data" / "scytale-soc2"


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1] or "item"
    name = re.sub(r"[^\w\-]+", "-", name).strip("-").lower()
    return name[:120] or "item"


def _load_website_login() -> tuple[str, str]:
    engine = create_engine(get_settings().database_url_sync)
    with Session(engine) as session:
        row = session.scalar(
            select(PlatformCredential).where(PlatformCredential.platform == Platform.website)
        )
        if not row:
            raise SystemExit("No website credential in platform_credentials.")
        return row.username, decrypt_secret(row.password_encrypted)


def _is_curriculum_url(href: str) -> bool:
    if not href.startswith(f"{SITE}/courses/take/scytale-SOC-2-academy/"):
        return False
    if "#" in href.split("/")[-1] and "/lessons/" not in href and "/texts/" not in href and "/quizzes/" not in href:
        return False
    path = urlparse(href).path
    return any(seg in path for seg in ("/lessons/", "/texts/", "/quizzes/"))


def _extract_page_text(page) -> tuple[str, str]:
    title = (page.title() or "").strip()
    # Prefer structured markdown from Thinkific / Froala content (keeps headings, lists, tables, images).
    text = page.evaluate(
        """() => {
          const picks = [
            '.fr-view',
            '.lecture-content',
            '[data-testid="course-player"] .fr-view',
            '.course-player__content',
            '.course-player',
            'article',
            'main',
            '#main-content',
          ];

          function cellText(node) {
            return (node.innerText || node.textContent || '').replace(/\\s+/g, ' ').trim();
          }

          function absUrl(src) {
            if (!src) return '';
            try { return new URL(src, location.href).href; } catch (e) { return src; }
          }

          function imgSrc(img) {
            let src = img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '';
            if (!src) {
              const srcset = img.getAttribute('srcset') || img.getAttribute('data-srcset') || '';
              if (srcset) src = srcset.split(',')[0].trim().split(/\\s+/)[0] || '';
            }
            return absUrl(src);
          }

          function pushImage(parts, img) {
            const src = imgSrc(img);
            if (!src) return;
            if (/^data:image\\/svg/i.test(src)) return;
            const alt = (img.getAttribute('alt') || '').replace(/[\\[\\]]/g, '').trim();
            parts.push('![' + alt + '](' + src + ')');
          }

          function tableToMd(table) {
            const rows = [];
            for (const tr of table.querySelectorAll('tr')) {
              const cells = Array.from(tr.querySelectorAll('th,td')).map((td) =>
                cellText(td).replace(/\\|/g, '\\\\|')
              );
              if (!cells.length) continue;
              rows.push('| ' + cells.join(' | ') + ' |');
            }
            if (!rows.length) return '';
            const colCount = Math.max(...rows.map((r) => (r.match(/\\|/g) || []).length - 1), 1);
            const sep = '| ' + Array.from({ length: colCount }, () => '---').join(' | ') + ' |';
            return [rows[0], sep, ...rows.slice(1)].join('\\n');
          }

          function toMd(root) {
            const parts = [];
            const blocks = root.querySelectorAll(
              'h1,h2,h3,h4,h5,h6,p,ul,ol,blockquote,pre,table,figure,img'
            );
            if (!blocks.length) {
              return (root.innerText || '').trim();
            }
            for (const el of blocks) {
              if (el.closest('li') && (el.tagName === 'P' || el.tagName === 'UL' || el.tagName === 'OL')) {
                continue;
              }
              const tag = el.tagName.toLowerCase();
              if (tag.match(/^h[1-6]$/)) {
                const level = Math.min(4, parseInt(tag[1], 10) || 2);
                const t = cellText(el);
                if (t) parts.push('#'.repeat(level) + ' ' + t);
                continue;
              }
              if (tag === 'p') {
                for (const img of el.querySelectorAll('img')) pushImage(parts, img);
                const clone = el.cloneNode(true);
                clone.querySelectorAll('img').forEach((n) => n.remove());
                const t = cellText(clone);
                if (t) parts.push(t);
                continue;
              }
              if (tag === 'figure') {
                const img = el.querySelector('img');
                if (img) pushImage(parts, img);
                const cap = el.querySelector('figcaption');
                if (cap) {
                  const t = cellText(cap);
                  if (t) parts.push('*' + t + '*');
                }
                continue;
              }
              if (tag === 'img') {
                if (el.closest('p, figure, table, li')) continue;
                pushImage(parts, el);
                continue;
              }
              if (tag === 'ul' || tag === 'ol') {
                if (el.parentElement && el.parentElement.closest('li')) continue;
                const items = [];
                for (const li of el.querySelectorAll(':scope > li')) {
                  for (const img of li.querySelectorAll('img')) pushImage(parts, img);
                  const t = cellText(li);
                  if (!t) continue;
                  items.push((tag === 'ol' ? '1. ' : '- ') + t);
                }
                if (items.length) parts.push(items.join('\\n'));
                continue;
              }
              if (tag === 'blockquote') {
                const t = cellText(el);
                if (t) parts.push('> ' + t);
                continue;
              }
              if (tag === 'pre') {
                const t = (el.innerText || '').trim();
                if (t) parts.push('```\\n' + t + '\\n```');
                continue;
              }
              if (tag === 'table') {
                if (el.closest('table') !== el) continue;
                const md = tableToMd(el);
                if (md) parts.push(md);
              }
            }
            return parts.join('\\n\\n').trim();
          }

          for (const sel of picks) {
            const el = document.querySelector(sel);
            if (!el) continue;
            const md = toMd(el);
            if (md && md.length > 40) return md;
          }
          const body = document.body ? document.body.innerText : '';
          return (body || '').trim();
        }"""
    )
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    # Drop noisy chrome tails
    for marker in ("Â© 2026 Scytale", "Teach online with Thinkific", "© 2026 Scytale"):
        if marker in text:
            text = text.split(marker)[0].strip()
    return title, text


def _localize_body_images(page, body: str, slug: str) -> str:
    from app.services.library_media import localize_markdown_images

    asset_dir = OUT_DIR / "assets" / slug
    prefix = f"scytale-soc2/assets/{slug}"

    def request_get(url: str):
        return page.context.request.get(url, timeout=60000)

    return localize_markdown_images(
        body,
        disk_dir=asset_dir,
        files_prefix=prefix,
        request_get=request_get,
    )


def _is_locked_text(text: str) -> bool:
    low = (text or "").lower()
    return "have not yet been completed" in low or (
        "prerequisite" in low and "ok, got it" in low
    )


def _click_by_text(page, labels: list[str]) -> bool:
    """Click first visible button/link matching one of the labels."""
    for label in labels:
        loc = page.get_by_role("button", name=re.compile(rf"^\s*{re.escape(label)}\s*$", re.I))
        try:
            if loc.count() and loc.first.is_visible():
                loc.first.click(timeout=3000)
                page.wait_for_timeout(1200)
                return True
        except Exception:
            pass
        loc = page.get_by_text(re.compile(rf"^\s*{re.escape(label)}\s*$", re.I))
        try:
            if loc.count() and loc.first.is_visible():
                loc.first.click(timeout=3000)
                page.wait_for_timeout(1200)
                return True
        except Exception:
            pass
    return False


def _advance_lesson(page) -> None:
    """Mark lesson complete / continue so later modules unlock."""
    _click_by_text(
        page,
        [
            "COMPLETE & CONTINUE",
            "Complete & Continue",
            "CONTINUE",
            "Continue",
            "MARK COMPLETE",
            "Mark Complete",
        ],
    )


def _try_complete_quiz(page) -> None:
    """Best-effort: pick first option per question and submit (unlocks progression)."""
    try:
        # Radio / checkbox answers
        inputs = page.locator('input[type="radio"], input[type="checkbox"]')
        count = inputs.count()
        seen_names: set[str] = set()
        for i in range(min(count, 40)):
            el = inputs.nth(i)
            name = el.get_attribute("name") or f"__{i}"
            if name in seen_names:
                continue
            seen_names.add(name)
            try:
                el.check(timeout=1000)
            except Exception:
                try:
                    el.click(timeout=1000)
                except Exception:
                    pass
        page.wait_for_timeout(400)
        _click_by_text(
            page,
            ["Submit", "SUBMIT", "Submit Quiz", "Check Answers", "Finish", "Complete"],
        )
        page.wait_for_timeout(1500)
        _advance_lesson(page)
    except Exception as exc:
        print(f"  quiz advance skipped: {type(exc).__name__}: {exc}")


def _capture_item(page, label: str, url: str, kind: str) -> tuple[str, str, bool]:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1800)
    title, body = _extract_page_text(page)
    if len(body) < 40:
        page.wait_for_timeout(2500)
        title, body = _extract_page_text(page)
    locked = _is_locked_text(body)
    if locked:
        return title, body, True
    # Unlock next items by completing this one when possible.
    if kind == "quiz":
        _try_complete_quiz(page)
    else:
        _advance_lesson(page)
    return title, body, False


def run() -> dict:
    """Re-scrape Scytale SOC 2 curriculum. Returns summary stats for jobs/CLI."""
    username, password = _load_website_login()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "pages").mkdir(exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        print("signing in…")
        page.goto(SIGN_IN, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1200)
        page.locator('input[type="email"], input[name="user[email]"], #user_email').first.fill(username)
        page.locator('input[type="password"], input[name="user[password]"], #user_password').first.fill(password)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_timeout(4000)
        if "/users/sign_in" in page.url:
            raise RuntimeError(f"Login failed — still on {page.url}")
        print("signed in ->", page.url)

        print("loading course outline…")
        page.goto(COURSE_HOME, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)

        links = page.eval_on_selector_all(
            "a",
            """els => els.map(a => ({
              text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 200),
              href: (a.href || '').split('#')[0]
            }))""",
        )
        urls: list[tuple[str, str]] = []
        seen: set[str] = set()
        for link in links:
            href = (link.get("href") or "").rstrip("/")
            if not _is_curriculum_url(href) or href in seen:
                continue
            seen.add(href)
            label = link.get("text") or _slug_from_url(href)
            urls.append((label, href))

        # Ensure first lesson is included
        first = f"{SITE}/courses/take/scytale-SOC-2-academy/lessons/35009308-1-introduction-to-soc-2"
        if first not in seen:
            urls.insert(0, ("1. Introduction to SOC 2", first))

        print(f"curriculum urls: {len(urls)}")
        (OUT_DIR / "urls.json").write_text(
            json.dumps([{"title": t, "url": u} for t, u in urls], indent=2),
            encoding="utf-8",
        )

        # Pass 1: visit in order, complete/continue to unlock later modules.
        # Pass 2: retry any locked pages after earlier items were marked complete.
        locked_idxs: list[int] = []
        results: dict[int, dict] = {}

        for pass_no in (1, 2):
            targets = list(range(len(urls))) if pass_no == 1 else list(locked_idxs)
            if pass_no == 2 and not targets:
                break
            print(f"pass {pass_no} — {len(targets)} items")
            locked_idxs = []
            for i in targets:
                label, url = urls[i]
                kind = "lesson"
                if "/texts/" in url:
                    kind = "text"
                elif "/quizzes/" in url:
                    kind = "quiz"
                idx = i + 1
                slug = f"{idx:03d}-{kind}-{_slug_from_url(url)}"
                out_path = OUT_DIR / "pages" / f"{slug}.md"
                print(f"[{idx}/{len(urls)}] {kind} {label[:60]}")
                try:
                    title, body, locked = _capture_item(page, label, url, kind)
                    if locked:
                        print("  LOCKED (prerequisites) — will retry after unlock pass")
                        locked_idxs.append(i)
                    elif body:
                        body = _localize_body_images(page, body, slug)
                    md = (
                        f"# {title or label}\n\n"
                        f"- kind: {kind}\n"
                        f"- label: {label}\n"
                        f"- url: {url}\n"
                        f"- locked: {str(locked).lower()}\n"
                        f"- fetched_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n\n"
                        f"---\n\n{body}\n"
                    )
                    out_path.write_text(md, encoding="utf-8")
                    results[i] = {
                        "index": idx,
                        "kind": kind,
                        "label": label,
                        "title": title,
                        "url": url,
                        "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                        "chars": len(body),
                        "locked": locked,
                        "ok": True,
                    }
                except Exception as exc:
                    print(f"  FAIL {type(exc).__name__}: {exc}")
                    results[i] = {
                        "index": idx,
                        "kind": kind,
                        "label": label,
                        "url": url,
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                time.sleep(0.35)

        browser.close()

    manifest = [results[i] for i in sorted(results)]
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    ok = sum(1 for m in manifest if m.get("ok"))
    locked = sum(1 for m in manifest if m.get("locked"))
    failed = sum(1 for m in manifest if not m.get("ok"))
    print(f"done — {ok}/{len(manifest)} saved, {locked} still locked -> {OUT_DIR}")
    return {
        "course_id": "soc-2-compliance",
        "ok": ok,
        "locked": locked,
        "failed": failed,
        "total": len(manifest),
        "out_dir": str(OUT_DIR),
    }


def main() -> None:
    try:
        run()
    except Exception as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
