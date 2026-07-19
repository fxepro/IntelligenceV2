"""Move catalog Category values out of tags[] into sources.category."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source


def backfill_category_from_tags_sync(session: Session) -> int:
    """
    For rows with empty category, take the first tag that is not
    secondary:* or catalog:*, set category, and drop that tag from tags.
    """
    rows = session.scalars(select(Source).where(Source.category.is_(None))).all()
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
