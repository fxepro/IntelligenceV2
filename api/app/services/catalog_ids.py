"""Stable per-domain catalog IDs: MEDIA-0001, GOV-0001, …"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.source import Source

# Short prefixes for known planes; others use uppercase domain slug.
DOMAIN_PREFIX: dict[str, str] = {
    "media": "MEDIA",
    "government": "GOV",
    "finance": "FIN",
    "software": "SOFT",
    "business": "BIZ",
    "taxes": "TAX",
    "healthcare": "HLTH",
    "people": "PPL",
    "geography": "GEO",
    "politics": "POL",
    "nonprofit": "NPO",
    "news": "NEWS",
    "real_estate": "RE",
    "auctions": "AUC",
    "torrents": "TOR",
    "trademarks": "TMK",
    "domain_names": "WWW",
    "library": "LIB",
    "patents": "PAT",
    "songs": "SONG",
    "music": "MUSIC",
    "books": "BOOK",
    "movies": "MOV",
    "fiction": "FIC",
}

_CATALOG_RE = re.compile(r"^([A-Z0-9]+)-(\d+)$")


def catalog_prefix(domain: str) -> str:
    key = (domain or "media").strip().lower()
    if key in DOMAIN_PREFIX:
        return DOMAIN_PREFIX[key]
    slug = re.sub(r"[^a-z0-9]+", "", key).upper()
    return (slug[:8] or "SRC")


def format_catalog_id(prefix: str, n: int) -> str:
    return f"{prefix}-{n:04d}"


def _next_number_sync(session: Session, domain: str, prefix: str) -> int:
    rows = (
        session.execute(
            select(Source.catalog_id).where(
                Source.domain == domain,
                Source.catalog_id.is_not(None),
            )
        )
        .scalars()
        .all()
    )
    max_n = 0
    for raw in rows:
        m = _CATALOG_RE.match(str(raw or ""))
        if m and m.group(1) == prefix:
            max_n = max(max_n, int(m.group(2)))
    return max_n + 1


async def _next_number(db: AsyncSession, domain: str, prefix: str) -> int:
    rows = (
        await db.execute(
            select(Source.catalog_id).where(
                Source.domain == domain,
                Source.catalog_id.is_not(None),
            )
        )
    ).scalars().all()
    max_n = 0
    for raw in rows:
        m = _CATALOG_RE.match(str(raw or ""))
        if m and m.group(1) == prefix:
            max_n = max(max_n, int(m.group(2)))
    return max_n + 1


async def allocate_catalog_id(db: AsyncSession, domain: str) -> str:
    prefix = catalog_prefix(domain)
    n = await _next_number(db, domain, prefix)
    return format_catalog_id(prefix, n)


def backfill_catalog_ids_sync(session: Session) -> int:
    """Assign catalog_id to rows that lack one, ordered by created_at per domain."""
    domains = session.execute(select(Source.domain).distinct()).scalars().all()
    updated = 0
    for domain in domains:
        domain_key = str(domain or "media")
        prefix = catalog_prefix(domain_key)
        missing = (
            session.execute(
                select(Source)
                .where(Source.domain == domain_key, Source.catalog_id.is_(None))
                .order_by(Source.created_at.asc(), Source.id.asc())
            )
            .scalars()
            .all()
        )
        if not missing:
            continue
        next_n = _next_number_sync(session, domain_key, prefix)
        for source in missing:
            source.catalog_id = format_catalog_id(prefix, next_n)
            next_n += 1
            updated += 1
    if updated:
        session.commit()
    return updated
