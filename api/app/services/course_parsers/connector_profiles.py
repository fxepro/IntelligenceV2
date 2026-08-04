"""Connector profiles — one place for discover/acquire behavior per curriculum shape."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorProfile:
    key: str
    label: str
    needs_acquire: bool = False
    prefer_js_first: bool = False
    retry_js_if_zero: bool = False
    allow_website_fallback: bool = True
    manual_only: bool = False


PROFILES: dict[str, ConnectorProfile] = {
    "manual": ConnectorProfile(
        key="manual",
        label="Manual only",
        manual_only=True,
        allow_website_fallback=False,
    ),
    "youtube_curriculum": ConnectorProfile(
        key="youtube_curriculum",
        label="Video curriculum",
        retry_js_if_zero=True,
    ),
    "youtube_playlist": ConnectorProfile(
        key="youtube_playlist",
        label="YouTube playlist",
        allow_website_fallback=False,
    ),
    "article_hub": ConnectorProfile(
        key="article_hub",
        label="Article hub",
        needs_acquire=True,
        retry_js_if_zero=True,
    ),
    "coursera_catalog": ConnectorProfile(
        key="coursera_catalog",
        label="Coursera catalog",
        prefer_js_first=True,
        allow_website_fallback=False,
    ),
    "udemy_catalog": ConnectorProfile(
        key="udemy_catalog",
        label="Udemy catalog",
        prefer_js_first=True,
        allow_website_fallback=False,
    ),
    "website": ConnectorProfile(
        key="website",
        label="Generic website",
        retry_js_if_zero=True,
        needs_acquire=False,  # acquire only when article links dominate (future)
    ),
}


def get_connector_profile(curriculum_type: str) -> ConnectorProfile:
    key = (curriculum_type or "website").strip().lower()
    return PROFILES.get(key, PROFILES["website"])


def fetch_ladder_for(curriculum_type: str) -> list[bool]:
    """Ordered prefer_js flags to try when discovering."""
    profile = get_connector_profile(curriculum_type)
    if profile.prefer_js_first:
        return [True]
    if profile.retry_js_if_zero:
        return [False, True]
    return [False]


def connector_needs_acquire(curriculum_type: str) -> bool:
    return get_connector_profile(curriculum_type).needs_acquire
