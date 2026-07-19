"""
Playwright login helpers — capture storage_state for gated platforms.

Facebook is first-class (needed for full reels catalogs). Other platforms
share the same storage shape so the scraper can load session_json later.
"""
from __future__ import annotations

import asyncio
import re
import sys
from typing import Any


def login_and_capture_session(
    platform: str,
    username: str,
    password: str,
    *,
    interactive: bool = True,
) -> dict[str, Any]:
    """Blocking: log in and return Playwright storage_state dict.

    Facebook defaults to an interactive (headed) browser so you can clear
    checkpoint / 2FA — headless login is almost always blocked.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    platform = (platform or "").lower()
    if platform == "facebook":
        if interactive:
            return _facebook_login_interactive(username, password)
        return _facebook_login(username, password)
    if platform == "instagram":
        return _instagram_login(username, password)
    if platform == "tiktok":
        raise RuntimeError("TikTok login is not wired yet — save credentials for later.")
    if platform == "youtube":
        raise RuntimeError(
            "YouTube usually works without login for public channels. "
            "Google login is not automated here (2FA / bot checks)."
        )
    raise RuntimeError(f"No login flow for platform '{platform}'")


def _dismiss_cookie_banners(page) -> None:
    labels = (
        r"Allow all cookies",
        r"Accept All",
        r"Accept all",
        r"Decline optional cookies",
        r"Only allow essential",
        r"Allow essential",
    )
    for label in labels:
        try:
            btn = page.get_by_role("button", name=re.compile(label, re.I))
            if btn.count():
                btn.first.click(timeout=2000)
                page.wait_for_timeout(500)
        except Exception:
            pass


def _click_facebook_login(page) -> None:
    """FB markup varies (often a visible 'Log in' div + a hidden submit input)."""
    # Prefer the visible control Facebook actually shows
    try:
        btn = page.get_by_role("button", name=re.compile(r"^\s*log\s*in\s*$", re.I))
        if btn.count():
            btn.first.click(timeout=8000)
            return
    except Exception:
        pass

    candidates = [
        'button[name="login"]',
        'input[name="login"]',
        "#loginbutton",
        'button[data-testid="royal-login-button"]',
        'form#login_form input[type="submit"]',
        'button[type="submit"]',
        'input[type="submit"]',
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            target = loc.first
            try:
                if target.is_visible(timeout=400):
                    target.click(timeout=5000)
                    return
            except Exception:
                pass
            # Hidden submit inputs are common — force or JS-submit the form
            try:
                target.click(timeout=3000, force=True)
                return
            except Exception:
                pass
        except Exception:
            continue

    # JS form submit bypasses Playwright visibility checks
    try:
        submitted = page.evaluate(
            """() => {
              const form = document.querySelector('form#login_form')
                || document.querySelector('form[action*="login"]')
                || document.querySelector('form');
              if (!form) return false;
              if (typeof form.requestSubmit === 'function') { form.requestSubmit(); return true; }
              form.submit();
              return true;
            }"""
        )
        if submitted:
            return
    except Exception:
        pass

    # Last resort: Enter on the password field
    pwd = page.locator('input[name="pass"], input#pass, input[type="password"]').first
    pwd.press("Enter", timeout=5000)


def _facebook_has_auth_cookies(state_or_cookies) -> bool:
    cookies = state_or_cookies
    if isinstance(state_or_cookies, dict):
        cookies = state_or_cookies.get("cookies") or []
    names = {c.get("name") for c in cookies}
    return "c_user" in names and "xs" in names


def _facebook_login_interactive(
    username: str,
    password: str,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    """
    Open a visible Chromium window, pre-fill login, and wait until real
    auth cookies appear (user completes checkpoint / 2FA if prompted).
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        try:
            page.goto(
                "https://www.facebook.com/login",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1200)
            _dismiss_cookie_banners(page)
            try:
                page.locator('input[name="email"], input#email').first.fill(username, timeout=8000)
                page.locator('input[name="pass"], input#pass').first.fill(password, timeout=8000)
                _click_facebook_login(page)
            except Exception:
                # User can type manually in the opened window.
                pass

            deadline = timeout_seconds * 1000
            waited = 0
            while waited < deadline:
                state = context.storage_state()
                if _facebook_has_auth_cookies(state):
                    page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(1500)
                    return context.storage_state()
                page.wait_for_timeout(2000)
                waited += 2000

            url = page.url or ""
            raise RuntimeError(
                "Timed out waiting for a Facebook login session (missing c_user/xs). "
                "In the browser window that opened: finish any checkpoint / 2FA, "
                "then click Connect again. "
                f"Last URL: {url}"
            )
        finally:
            context.close()
            browser.close()


def _facebook_login(username: str, password: str) -> dict[str, Any]:
    """
    Log in via mbasic (reliable form), then warm www.facebook.com cookies.

    Success requires real auth cookies (c_user + xs). Tracking-only cookies
    (datr/fr/sb) are NOT a logged-in session.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        try:
            # mbasic has a classic email/pass/login form that automation can submit.
            page.goto(
                "https://mbasic.facebook.com/login/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1500)
            _dismiss_cookie_banners(page)

            email = page.locator('input[name="email"]').first
            pwd = page.locator('input[name="pass"]').first
            email.wait_for(state="visible", timeout=15000)
            email.fill(username, timeout=10000)
            pwd.fill(password, timeout=10000)
            # Do not click hidden input[type=submit] without force — FB hides it.
            _click_facebook_login(page)

            page.wait_for_timeout(5000)

            url = page.url or ""
            body = ""
            try:
                body = page.inner_text("body")[:1500]
            except Exception:
                pass
            body_l = body.lower()

            if "checkpoint" in url or "two_factor" in url or "two-factor" in url or "approvals" in url:
                raise RuntimeError(
                    "Facebook requires a checkpoint / 2FA step. "
                    "Approve the login on your phone or complete it in a normal browser, then Connect again."
                )
            if any(
                x in body_l
                for x in (
                    "incorrect",
                    "wrong password",
                    "isn't connected to an account",
                    "invalid username",
                    "login information you entered",
                )
            ):
                raise RuntimeError("Facebook rejected the username or password.")

            # Warm www cookies used by the reels scraper
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            _dismiss_cookie_banners(page)

            state = context.storage_state()
            if not _facebook_has_auth_cookies(state):
                # One more attempt on www login form if mbasic didn't stick
                page.goto("https://www.facebook.com/login", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1500)
                _dismiss_cookie_banners(page)
                try:
                    page.locator('input[name="email"], input#email').first.fill(username, timeout=8000)
                    page.locator('input[name="pass"], input#pass').first.fill(password, timeout=8000)
                    _click_facebook_login(page)
                    page.wait_for_timeout(6000)
                    page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(2000)
                    state = context.storage_state()
                except Exception:
                    pass

            if not _facebook_has_auth_cookies(state):
                url = page.url or ""
                raise RuntimeError(
                    "Facebook did not issue a real login session (missing c_user/xs cookies). "
                    "This usually means a checkpoint, 2FA, or bot check blocked headless login. "
                    f"Last URL: {url}"
                )
            return state
        finally:
            context.close()
            browser.close()


def _instagram_login(username: str, password: str) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        try:
            page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            page.locator('input[name="username"]').fill(username, timeout=15000)
            page.locator('input[name="password"]').fill(password, timeout=10000)
            page.locator('button[type="submit"]').first.click(timeout=10000)
            page.wait_for_timeout(5000)
            url = page.url or ""
            if "challenge" in url or "two_factor" in url:
                raise RuntimeError("Instagram requires a challenge / 2FA step.")
            if "accounts/login" in url:
                raise RuntimeError("Instagram login did not complete. Check credentials.")
            state = context.storage_state()
            if not state.get("cookies"):
                raise RuntimeError("No cookies captured after Instagram login.")
            return state
        finally:
            context.close()
            browser.close()
