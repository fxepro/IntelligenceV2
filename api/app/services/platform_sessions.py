"""Platform browser-session helpers for Access credentials + yt-dlp cookies."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from app.models.source import Platform

SESSION_PLATFORMS: tuple[Platform, ...] = (
    Platform.facebook,
    Platform.youtube,
    Platform.instagram,
    Platform.tiktok,
    Platform.x,
)

PLATFORM_DOMAINS: dict[str, str] = {
    "youtube": ".youtube.com",
    "instagram": ".instagram.com",
    "tiktok": ".tiktok.com",
    "x": ".x.com",
    "facebook": ".facebook.com",
}

# Cookies that prove a real login (not anonymous tracking).
AUTH_COOKIE_NAMES: dict[str, frozenset[str]] = {
    "facebook": frozenset({"c_user", "xs"}),
    "youtube": frozenset({"SID", "__Secure-1PSID", "__Secure-3PSID", "LOGIN_INFO"}),
    "instagram": frozenset({"sessionid"}),
    "tiktok": frozenset({"sessionid", "sid_tt"}),
    "x": frozenset({"auth_token"}),
}


def platform_key(platform: Platform | str) -> str:
    return platform.value if hasattr(platform, "value") else str(platform)


def has_auth_cookies(platform: Platform | str, session_json: dict | None) -> bool:
    if not isinstance(session_json, dict):
        return False
    cookies = session_json.get("cookies") or []
    names = {c.get("name") for c in cookies if isinstance(c, dict) and c.get("name")}
    required = AUTH_COOKIE_NAMES.get(platform_key(platform), frozenset())
    if not required:
        return bool(names)
    if platform_key(platform) == "facebook":
        return "c_user" in names and "xs" in names
    return bool(names & required)


def _cookie_entry(
    *,
    name: str,
    value: str,
    domain: str,
    path: str = "/",
    secure: bool = True,
    http_only: bool = False,
    expires: float = -1,
) -> dict[str, Any]:
    return {
        "name": name,
        "value": value,
        "domain": domain,
        "path": path or "/",
        "expires": expires,
        "httpOnly": http_only,
        "secure": secure,
        "sameSite": "None",
    }


def parse_cookie_header(raw: str, *, default_domain: str) -> list[dict[str, Any]]:
    cookies: list[dict[str, Any]] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        cookies.append(
            _cookie_entry(
                name=name,
                value=value,
                domain=default_domain,
                secure=True,
                http_only=name.lower() in {"xs", "sessionid", "auth_token", "sid", "sid_tt"},
            )
        )
    return cookies


def parse_netscape_cookies(raw: str) -> list[dict[str, Any]]:
    cookies: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _flag, path, secure, expires, name, value = parts[:7]
        try:
            exp = float(expires)
        except ValueError:
            exp = -1
        cookies.append(
            _cookie_entry(
                name=name,
                value=value,
                domain=domain,
                path=path or "/",
                secure=str(secure).upper() == "TRUE",
                expires=exp if exp > 0 else -1,
            )
        )
    return cookies


def cookies_from_paste(raw: str, platform: Platform | str) -> list[dict[str, Any]]:
    text = (raw or "").strip()
    if not text:
        return []
    key = platform_key(platform)
    default_domain = PLATFORM_DOMAINS.get(key, f".{key}.com")

    if "\t" in text or re.search(r"(?m)^# Netscape", text):
        cookies = parse_netscape_cookies(text)
        if cookies:
            return cookies

    # JSON array of cookie objects (DevTools copy / Playwright export)
    if text.startswith("[") or text.startswith("{"):
        import json

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and isinstance(data.get("cookies"), list):
            data = data["cookies"]
        if isinstance(data, list):
            out: list[dict[str, Any]] = []
            for item in data:
                if not isinstance(item, dict) or not item.get("name"):
                    continue
                out.append(
                    _cookie_entry(
                        name=str(item["name"]),
                        value=str(item.get("value") or ""),
                        domain=str(item.get("domain") or default_domain),
                        path=str(item.get("path") or "/"),
                        secure=bool(item.get("secure", True)),
                        http_only=bool(item.get("httpOnly", False)),
                        expires=float(item["expires"]) if item.get("expires") else -1,
                    )
                )
            if out:
                return out

    return parse_cookie_header(text, default_domain=default_domain)


def storage_state_from_cookies(cookies: list[dict[str, Any]]) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    for cookie in cookies:
        row = dict(cookie)
        try:
            exp = float(row.get("expires") if row.get("expires") is not None else -1)
        except (TypeError, ValueError):
            exp = -1
        if exp <= 0:
            row["expires"] = 4102444800.0
        normalized.append(row)
    return {"cookies": normalized, "origins": []}


def platform_from_url(url: str) -> str | None:
    low = (url or "").lower()
    if "youtube.com" in low or "youtu.be" in low:
        return "youtube"
    if "instagram.com" in low:
        return "instagram"
    if "tiktok.com" in low:
        return "tiktok"
    if "x.com" in low or "twitter.com" in low:
        return "x"
    if "facebook.com" in low or "fb.com" in low or "fb.watch" in low:
        return "facebook"
    return None


def load_connected_session(platform: Platform | str) -> dict[str, Any] | None:
    """Best-effort sync load of the newest connected session for a platform."""
    try:
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import Session

        from app.config import get_settings
        from app.models.platform_credential import CredentialStatus, PlatformCredential

        key = platform_key(platform)
        try:
            enum_platform = Platform(key)
        except ValueError:
            return None

        engine = create_engine(get_settings().database_url_sync)
        with Session(engine) as db:
            rows = db.scalars(
                select(PlatformCredential)
                .where(PlatformCredential.platform == enum_platform)
                .order_by(PlatformCredential.updated_at.desc())
            ).all()
            for row in rows:
                state = dict(row.session_json) if isinstance(row.session_json, dict) else None
                if has_auth_cookies(key, state):
                    return state
    except Exception:
        return None
    return None


def write_netscape_cookiefile(session_json: dict[str, Any], path: Path) -> Path:
    lines = ["# Netscape HTTP Cookie File", "# Generated by Media Intelligence", ""]
    for cookie in session_json.get("cookies") or []:
        if not isinstance(cookie, dict):
            continue
        name = cookie.get("name")
        value = cookie.get("value")
        if not name:
            continue
        domain = str(cookie.get("domain") or "")
        include_sub = "TRUE" if domain.startswith(".") else "FALSE"
        path_value = str(cookie.get("path") or "/")
        secure = "TRUE" if cookie.get("secure") else "FALSE"
        expires = cookie.get("expires")
        try:
            # yt-dlp skips expires <= 0; session cookies (-1) must get a far-future stamp.
            exp_i = int(float(expires)) if expires is not None and float(expires) > 0 else 4102444800
        except (TypeError, ValueError):
            exp_i = 4102444800
        lines.append(
            "\t".join(
                [
                    domain or ".example.com",
                    include_sub,
                    path_value,
                    secure,
                    str(exp_i),
                    str(name),
                    str(value or ""),
                ]
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def cookiefile_for_url(url: str, work_dir: Path | None = None) -> Path | None:
    platform = platform_from_url(url)
    if not platform:
        return None
    state = load_connected_session(platform)
    if not state:
        return None
    base = work_dir or Path(tempfile.gettempdir()) / "mi-cookies"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{platform}.txt"
    return write_netscape_cookiefile(state, path)


def apply_cookies_to_ydl_opts(opts: dict, url: str, work_dir: Path | None = None) -> dict:
    """Return yt-dlp opts with cookiefile when a connected session exists."""
    cookiefile = cookiefile_for_url(url, work_dir)
    if cookiefile:
        opts = dict(opts)
        opts["cookiefile"] = str(cookiefile)
    return opts
