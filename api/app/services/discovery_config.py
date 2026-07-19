"""Shared discovery schedule and list-size limits."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

DISCOVERY_DEFAULTS = {
    "interval_minutes": 60,
    "max_items": 100,
    "media_page_size": 500,
    "url_check_enabled": False,
    "url_check_interval_minutes": 360,
}

MAX_ITEMS_CEILING = 5000
MEDIA_PAGE_SIZE_CEILING = 5000
MIN_MEDIA_PAGE_SIZE = 50
URL_CHECK_BATCH = 15


def normalize_discovery_settings(value: dict | None) -> dict:
    settings = {**DISCOVERY_DEFAULTS, **(value or {})}
    settings["interval_minutes"] = max(5, min(10080, int(settings["interval_minutes"])))
    settings["max_items"] = max(1, min(MAX_ITEMS_CEILING, int(settings["max_items"])))
    settings["media_page_size"] = max(
        MIN_MEDIA_PAGE_SIZE,
        min(MEDIA_PAGE_SIZE_CEILING, int(settings["media_page_size"])),
    )
    # URL check removed — keep keys for stored settings shape, always off.
    settings["url_check_enabled"] = False
    settings["url_check_interval_minutes"] = max(
        15, min(10080, int(settings.get("url_check_interval_minutes") or 360))
    )
    return settings


async def get_discovery_settings(db: AsyncSession) -> dict:
    row = await db.get(AppSetting, "discovery")
    return normalize_discovery_settings(row.value if row else {})


def get_discovery_settings_sync(session: Session) -> dict:
    row = session.get(AppSetting, "discovery")
    return normalize_discovery_settings(row.value if row else {})
