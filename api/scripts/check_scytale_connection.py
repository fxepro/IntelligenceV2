"""One-shot: check Scytale website credential + course access. No secrets printed."""
from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.platform_credential import PlatformCredential
from app.models.source import Platform
from app.services.credential_crypto import decrypt_secret

SITE = "https://academy.scytale.ai"
SIGN_IN = f"{SITE}/users/sign_in"
COURSE_HOME = f"{SITE}/courses/take/scytale-SOC-2-academy/"


def main() -> int:
    engine = create_engine(get_settings().database_url_sync)
    with Session(engine) as session:
        n = session.scalar(
            select(func.count())
            .select_from(PlatformCredential)
            .where(PlatformCredential.platform == Platform.website)
        ) or 0
        row = session.scalar(
            select(PlatformCredential).where(PlatformCredential.platform == Platform.website)
        )
        if not row or not row.password_encrypted:
            print("RESULT=FAIL")
            print("reason=no_website_credential_in_db")
            return 1
        username = (row.username or "").strip()
        password = decrypt_secret(row.password_encrypted)
        site_url = (getattr(row, "site_url", None) or "").strip()
        print("creds_found=true")
        print(f"credential_rows={n}")
        print(f"site_url_set={bool(site_url)}")
        print(f"username_set={bool(username)}")
        print(f"password_set={bool(password)}")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        try:
            page.goto(SIGN_IN, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1000)
            page.locator(
                'input[type="email"], input[name="user[email]"], #user_email'
            ).first.fill(username)
            page.locator(
                'input[type="password"], input[name="user[password]"], #user_password'
            ).first.fill(password)
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_timeout(4500)
            if "/users/sign_in" in page.url:
                print("RESULT=FAIL")
                print("stage=login")
                print("reason=still_on_sign_in")
                return 2
            print("stage=login_ok")

            page.goto(COURSE_HOME, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3500)
            title = (page.title() or "").strip()
            links = page.eval_on_selector_all(
                "a",
                'els => els.map(a => (a.href || "").split("#")[0])',
            )
            cur = [
                h
                for h in links
                if h.startswith(COURSE_HOME)
                and any(s in h for s in ("/lessons/", "/texts/", "/quizzes/"))
            ]
            cur = sorted(set(cur))
            body_snip = (page.inner_text("body") or "")[:800].lower()
            locked = "have not yet been completed" in body_snip or (
                "prerequisite" in body_snip and "ok, got it" in body_snip
            )
            denied = any(
                x in body_snip
                for x in ("access denied", "not enrolled", "purchase this course")
            )
            on_course = "scytale-soc-2-academy" in page.url.lower()
            print(f"stage={'course_ok' if not denied else 'course_denied'}")
            print(f"course_title={title!r}")
            print(f"on_course_path={on_course}")
            print(f"curriculum_urls={len(cur)}")
            print(f"locked_gate={locked}")
            print(f"denied={denied}")
            if denied or not on_course:
                print("RESULT=FAIL")
                return 3
            if len(cur) == 0:
                print("RESULT=FAIL")
                print("reason=no_curriculum_links")
                return 4
            print("RESULT=OK")
            print("connection_valid=true")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
