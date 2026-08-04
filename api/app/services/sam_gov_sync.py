"""Upsert SAM.gov contract opportunities into government_details (GOV-0001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.government_detail import GovernmentDetail
from app.models.source import Source
from app.services.sam_gov import (
    CONNECTOR,
    GOV_CATALOG_OPPORTUNITIES,
    default_posted_range,
    search_opportunities,
)


def _parse_dt(raw: Any) -> datetime | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    for fmt, slice_len in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            dt = datetime.strptime(text[:slice_len], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _apply_opp(row: GovernmentDetail, *, source: Source, opp: dict[str, Any], now: datetime) -> None:
    notice_id = str(opp.get("noticeId") or "").strip()
    title = (opp.get("title") or "").strip() or notice_id
    ui_link = (opp.get("uiLink") or "").strip()
    canonical_url = ui_link or f"https://sam.gov/opp/{notice_id}/view"

    row.source_id = source.id
    row.catalog_id = GOV_CATALOG_OPPORTUNITIES
    row.connector = CONNECTOR
    row.notice_id = notice_id
    row.title = title
    row.canonical_url = canonical_url
    row.solicitation_number = (opp.get("solicitationNumber") or "").strip() or None
    row.posted_at = _parse_dt(opp.get("postedDate"))
    row.response_deadline = opp.get("responseDeadLine") or opp.get("reponseDeadLine")
    row.notice_type = opp.get("type")
    row.base_type = opp.get("baseType")
    row.naics_code = opp.get("naicsCode")
    row.classification_code = opp.get("classificationCode")
    row.set_aside = opp.get("setAside") or opp.get("typeOfSetAsideDescription")
    row.set_aside_code = opp.get("setAsideCode") or opp.get("typeOfSetAside")
    row.organization = opp.get("fullParentPathName") or opp.get("department")
    row.active = opp.get("active")
    row.description_url = opp.get("description")
    row.payload = opp
    row.error_message = None
    row.synced_at = now


def _upsert_opportunity(
    session: Session, *, source: Source, opp: dict[str, Any], now: datetime
) -> str:
    notice_id = str(opp.get("noticeId") or "").strip()
    if not notice_id:
        return "skipped"

    dedup_key = f"sam.gov:opportunity:{notice_id}"
    existing = session.scalar(
        select(GovernmentDetail).where(GovernmentDetail.dedup_key == dedup_key)
    )
    if existing:
        _apply_opp(existing, source=source, opp=opp, now=now)
        return "updated"

    row = GovernmentDetail(dedup_key=dedup_key, notice_id=notice_id)
    _apply_opp(row, source=source, opp=opp, now=now)
    session.add(row)
    return "new"


def sync_opportunities(
    session: Session,
    *,
    source_id: uuid.UUID,
    posted_from: str | None = None,
    posted_to: str | None = None,
    limit: int = 100,
    max_pages: int = 1,
) -> dict[str, Any]:
    source = session.get(Source, source_id)
    if not source:
        raise ValueError(f"Source {source_id} not found")
    if source.domain != "government":
        raise ValueError("Source is not a government source")
    if (source.catalog_id or "").strip().upper() != GOV_CATALOG_OPPORTUNITIES:
        raise ValueError(f"Source must be catalog {GOV_CATALOG_OPPORTUNITIES}")

    if not posted_from or not posted_to:
        posted_from, posted_to = default_posted_range(days=7)

    new_count = 0
    updated = 0
    skipped = 0
    fetched = 0
    total_records: int | None = None
    pages = max(1, min(max_pages, 10))
    now = datetime.now(timezone.utc)

    for page in range(pages):
        offset = page * limit
        payload = search_opportunities(
            posted_from=posted_from,
            posted_to=posted_to,
            limit=limit,
            offset=offset,
        )
        if total_records is None:
            try:
                total_records = int(payload.get("totalRecords") or 0)
            except (TypeError, ValueError):
                total_records = 0

        rows = payload.get("opportunitiesData") or []
        if not isinstance(rows, list):
            rows = []
        fetched += len(rows)
        for opp in rows:
            if not isinstance(opp, dict):
                skipped += 1
                continue
            outcome = _upsert_opportunity(session, source=source, opp=opp, now=now)
            if outcome == "new":
                new_count += 1
            elif outcome == "updated":
                updated += 1
            else:
                skipped += 1

        if len(rows) < limit:
            break
        if total_records is not None and offset + len(rows) >= total_records:
            break

    session.flush()
    return {
        "catalog_id": GOV_CATALOG_OPPORTUNITIES,
        "posted_from": posted_from,
        "posted_to": posted_to,
        "fetched": fetched,
        "new": new_count,
        "updated": updated,
        "skipped": skipped,
        "total_records": total_records,
        "source_id": str(source_id),
    }
