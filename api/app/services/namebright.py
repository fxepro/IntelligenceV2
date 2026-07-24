"""NameBright Domain API client (OAuth2 client_credentials)."""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

AUTH_URL = "https://api.namebright.com/auth/token"
REST_BASE = "https://api.namebright.com/rest"

_token: str | None = None
_token_expires_at: float = 0.0


def _ipv4_client(*, timeout: float = 30.0) -> httpx.Client:
    """Force IPv4 egress — NameBright whitelists are usually IPv4-only."""
    return httpx.Client(
        timeout=timeout,
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    )


def _credentials() -> tuple[str, str]:
    settings = get_settings()
    client_id = (settings.namebright_client_id or "").strip()
    client_secret = (settings.namebright_client_secret or "").strip()
    if not client_id or not client_secret:
        raise RuntimeError(
            "NameBright credentials missing. Set NAMEBRIGHT_CLIENT_ID and "
            "NAMEBRIGHT_CLIENT_SECRET in v2/.env"
        )
    return client_id, client_secret


def get_access_token(*, force: bool = False) -> str:
    """Return a bearer token (cached ~25 minutes)."""
    global _token, _token_expires_at
    now = time.time()
    if not force and _token and now < _token_expires_at:
        return _token

    client_id, client_secret = _credentials()
    with _ipv4_client(timeout=30.0) as client:
        res = client.post(
            AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if res.status_code >= 400:
            detail = (res.text or "")[:500]
            raise RuntimeError(f"NameBright auth failed ({res.status_code}): {detail}")
        data = res.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"NameBright auth response missing access_token: {data!r}")
    # Tokens last 30 minutes; refresh a bit early.
    expires_in = int(data.get("expires_in") or 1800)
    _token = str(token)
    _token_expires_at = now + max(60, expires_in - 300)
    return _token


def list_account_domains(*, page_size: int = 100) -> list[dict[str, Any]]:
    """Paginate GET /account/domains until exhausted (max 100 per page)."""
    page_size = max(1, min(100, int(page_size)))
    out: list[dict[str, Any]] = []
    page = 1
    token = get_access_token()

    with _ipv4_client(timeout=60.0) as client:
        while True:
            res = client.get(
                f"{REST_BASE}/account/domains",
                params={"page": page, "domainsPerPage": page_size},
                headers={"Authorization": f"Bearer {token}"},
            )
            if res.status_code == 401:
                token = get_access_token(force=True)
                res = client.get(
                    f"{REST_BASE}/account/domains",
                    params={"page": page, "domainsPerPage": page_size},
                    headers={"Authorization": f"Bearer {token}"},
                )
            if res.status_code >= 400:
                detail = (res.text or "")[:500]
                raise RuntimeError(f"NameBright domains failed ({res.status_code}): {detail}")
            data = res.json()
            batch = data.get("Domains") or data.get("domains") or []
            if not isinstance(batch, list):
                raise RuntimeError(f"Unexpected NameBright domains payload: {type(batch)}")
            out.extend(batch)
            total = int(data.get("ResultsTotal") or data.get("resultsTotal") or len(out))
            if len(out) >= total or not batch:
                break
            page += 1
            if page > 500:
                break
            time.sleep(1.05)  # stay under NameBright rate guidance
    return out


def _authorized_get(client: httpx.Client, path: str, *, token: str) -> tuple[str, httpx.Response]:
    """GET with one 401 retry. Returns (token, response)."""
    url = f"{REST_BASE}{path}"
    res = client.get(url, headers={"Authorization": f"Bearer {token}"})
    if res.status_code == 401:
        token = get_access_token(force=True)
        res = client.get(url, headers={"Authorization": f"Bearer {token}"})
    return token, res


def get_nameservers(domain: str, *, client: httpx.Client | None = None, token: str | None = None) -> list[str]:
    """GET /account/domains/{domain}/nameservers."""
    name = domain.strip().lower()
    own = client is None
    token = token or get_access_token()
    http = client or _ipv4_client(timeout=30.0)
    try:
        token, res = _authorized_get(http, f"/account/domains/{name}/nameservers", token=token)
        if res.status_code >= 400:
            detail = (res.text or "")[:300]
            raise RuntimeError(f"NameBright nameservers failed ({res.status_code}): {detail}")
        data = res.json()
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
        for key in ("NameServers", "nameservers", "Servers", "servers"):
            batch = data.get(key) if isinstance(data, dict) else None
            if isinstance(batch, list):
                return [str(x).strip() for x in batch if str(x).strip()]
        return []
    finally:
        if own:
            http.close()


def get_host_records(
    domain: str, *, client: httpx.Client | None = None, token: str | None = None
) -> dict[str, list[dict[str, Any]]]:
    """GET /account/domains/{domain}/hostrecords/all — normalize into typed lists."""
    name = domain.strip().lower()
    own = client is None
    token = token or get_access_token()
    http = client or _ipv4_client(timeout=30.0)
    try:
        token, res = _authorized_get(http, f"/account/domains/{name}/hostrecords/all", token=token)
        if res.status_code >= 400:
            detail = (res.text or "")[:300]
            raise RuntimeError(f"NameBright hostrecords failed ({res.status_code}): {detail}")
        data = res.json() if res.content else {}
        if not isinstance(data, dict):
            data = {}

        def _list(key: str, alt: str) -> list[dict[str, Any]]:
            raw = data.get(key) or data.get(alt) or []
            return [x for x in raw if isinstance(x, dict)] if isinstance(raw, list) else []

        return {
            "a": _list("ARecords", "aRecords"),
            "aaaa": _list("AAAARecords", "aaaaRecords"),
            "cname": _list("CNAMERecords", "cnameRecords"),
            "mx": _list("MXRecords", "mxRecords"),
            "txt": _list("TXTRecords", "txtRecords"),
            "srv": _list("SRVRecords", "srvRecords"),
        }
    finally:
        if own:
            http.close()


def credentials_configured() -> bool:
    settings = get_settings()
    return bool(
        (settings.namebright_client_id or "").strip()
        and (settings.namebright_client_secret or "").strip()
    )
