"""SAM.gov Contract Opportunities API client (GOV-0001)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

from app.config import get_settings

SEARCH_URL = "https://api.sam.gov/opportunities/v2/search"
CONNECTOR = "sam_gov_opportunities"
GOV_CATALOG_OPPORTUNITIES = "GOV-0001"


def credentials_configured() -> bool:
    return bool((get_settings().sam_gov_api_key or "").strip())


def _api_key() -> str:
    key = (get_settings().sam_gov_api_key or "").strip()
    if not key:
        raise RuntimeError("SAM_GOV_API_KEY missing in v2/.env")
    return key


def default_posted_range(*, days: int = 7) -> tuple[str, str]:
    """Return (postedFrom, postedTo) as MM/dd/yyyy — max 365-day window."""
    end = date.today()
    start = end - timedelta(days=max(1, min(days, 365)))
    return start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y")


def search_opportunities(
    *,
    posted_from: str,
    posted_to: str,
    limit: int = 100,
    offset: int = 0,
    ptype: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "api_key": _api_key(),
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": max(1, min(limit, 1000)),
        "offset": max(0, offset),
    }
    if ptype:
        params["ptype"] = ptype

    with httpx.Client(timeout=60.0) as client:
        res = client.get(SEARCH_URL, params=params)
        if res.status_code >= 400:
            detail = res.text[:500]
            raise RuntimeError(f"SAM.gov API {res.status_code}: {detail}")
        data = res.json()
        if not isinstance(data, dict):
            raise RuntimeError("SAM.gov API returned non-object JSON")
        return data
