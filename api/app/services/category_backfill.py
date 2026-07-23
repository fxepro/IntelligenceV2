"""Move catalog Category values out of tags[] into sources.category."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source


def backfill_category_from_tags_sync(session: Session) -> int:
    """
    For non-media rows with empty category, take the first tag that is not
    secondary:* or catalog:*, set category, and drop that tag from tags.

    Media keeps freeform tags in tags[] — do not migrate them into category.
    """
    rows = session.scalars(
        select(Source).where(
            Source.category.is_(None),
            Source.domain != "media",
        )
    ).all()
    updated = 0
    for source in rows:
        tags = list(source.tags or [])
        if not tags:
            continue
        category = None
        keep: list[str] = []
        for tag in tags:
            text = str(tag).strip()
            if not text:
                continue
            low = text.lower()
            if low.startswith("secondary:") or low.startswith("catalog:"):
                keep.append(text)
                continue
            if category is None:
                category = text[:128]
            else:
                keep.append(text)
        if not category:
            continue
        source.category = category
        source.tags = keep
        updated += 1
    if updated:
        session.commit()
    return updated


def restore_media_tags_from_category_sync(session: Session) -> int:
    """
    Put category back into tags[] for media when tags are empty.
    Clears category so Media Sources keeps a single Tags surface.
    """
    rows = session.scalars(select(Source).where(Source.domain == "media")).all()
    updated = 0
    for source in rows:
        tags = [str(t).strip() for t in (source.tags or []) if str(t).strip()]
        category = (source.category or "").strip()
        if tags or not category:
            continue
        source.tags = [category[:64]]
        source.category = None
        updated += 1
    if updated:
        session.commit()
    return updated
