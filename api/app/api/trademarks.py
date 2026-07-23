"""Trademarks domain control-plane routes."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.source import Source
from app.models.trademark_source_detail import TrademarkSourceDetail
from app.services.credential_crypto import encrypt_secret

router = APIRouter()


class TrademarkSourceDetailOut(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    catalog_id: str
    country: str | None = None
    country_code: str | None = None
    jurisdiction: str | None = None
    office: str | None = None
    search_url: str | None = None
    status_lookup_url: str | None = None
    filing_url: str | None = None
    registry_url: str | None = None
    gazette_url: str | None = None
    journal_url: str | None = None
    api_url: str | None = None
    api_docs_url: str | None = None
    bulk_download_url: str | None = None
    has_api_key: bool = False
    response_format: str | None = None
    pagination: str | None = None
    query_parameters: str | None = None
    access_type: str | None = None
    authentication: str | None = None
    rate_limit: str | None = None
    supports_nice_classes: bool | None = None
    supports_image_search: bool | None = None
    update_frequency: str | None = None
    detail_status: str | None = None
    last_verified: date | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class TrademarkSourceDetailPatch(BaseModel):
    """Manual fields editable from the source detail page."""

    api_key: str | None = Field(
        default=None,
        max_length=2048,
        description="Set to store/replace the API key; send empty string to clear.",
    )


def _to_out(row: TrademarkSourceDetail) -> TrademarkSourceDetailOut:
    data = TrademarkSourceDetailOut.model_validate(row)
    data.has_api_key = bool(row.api_key_encrypted)
    return data


async def _get_trademark_source(db: AsyncSession, source_id: uuid.UUID) -> Source:
    source = await db.get(Source, source_id)
    if not source or source.domain != "trademarks":
        raise HTTPException(status_code=404, detail="Trademark source not found")
    return source


async def _get_detail_for_source(
    db: AsyncSession, source: Source
) -> TrademarkSourceDetail | None:
    row = await db.scalar(
        select(TrademarkSourceDetail).where(TrademarkSourceDetail.source_id == source.id)
    )
    if not row and source.catalog_id:
        row = await db.scalar(
            select(TrademarkSourceDetail).where(
                TrademarkSourceDetail.catalog_id == source.catalog_id
            )
        )
    return row


@router.get(
    "/sources/{source_id}/details",
    response_model=TrademarkSourceDetailOut,
)
async def get_trademark_source_details(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    source = await _get_trademark_source(db, source_id)
    row = await _get_detail_for_source(db, source)
    if not row:
        raise HTTPException(status_code=404, detail="Trademark source details not found")
    return _to_out(row)


@router.patch(
    "/sources/{source_id}/details",
    response_model=TrademarkSourceDetailOut,
)
async def patch_trademark_source_details(
    source_id: uuid.UUID,
    payload: TrademarkSourceDetailPatch,
    db: AsyncSession = Depends(get_db),
):
    source = await _get_trademark_source(db, source_id)
    row = await _get_detail_for_source(db, source)
    if not row:
        raise HTTPException(status_code=404, detail="Trademark source details not found")

    data = payload.model_dump(exclude_unset=True)
    if "api_key" in data:
        raw = data["api_key"]
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            row.api_key_encrypted = None
        else:
            row.api_key_encrypted = encrypt_secret(str(raw).strip())

    await db.flush()
    await db.refresh(row)
    return _to_out(row)


@router.delete(
    "/sources/{source_id}/details/api-key",
    response_model=TrademarkSourceDetailOut,
)
async def delete_trademark_api_key(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    source = await _get_trademark_source(db, source_id)
    row = await _get_detail_for_source(db, source)
    if not row:
        raise HTTPException(status_code=404, detail="Trademark source details not found")
    row.api_key_encrypted = None
    await db.flush()
    await db.refresh(row)
    return _to_out(row)


class TrademarkConnectReadinessOut(BaseModel):
    source_id: uuid.UUID
    catalog_id: str
    """Machine channel readiness: api | bulk | api_bulk. Only machine sources are listed."""
    connect_readiness: str
    can_query: bool = True
    can_refresh: bool = True


class TrademarkConnectReadinessList(BaseModel):
    items: list[TrademarkConnectReadinessOut]
    total: int


def _connect_readiness(row: TrademarkSourceDetail) -> str | None:
    def _is_url(v: str | None) -> bool:
        s = (v or "").strip().lower()
        return s.startswith("http://") or s.startswith("https://")

    has_api = _is_url(row.api_url)
    has_bulk = _is_url(row.bulk_download_url)
    if has_api and has_bulk:
        return "api_bulk"
    if has_api:
        return "api"
    if has_bulk:
        return "bulk"
    return None


@router.get(
    "/connect-readiness",
    response_model=TrademarkConnectReadinessList,
)
async def list_trademark_connect_readiness(db: AsyncSession = Depends(get_db)):
    """
    Sources with a machine channel (api_url and/or bulk_download_url).

    These are treated as immediately connectable for query/refresh (credentials may
    still be required at pull time for API-key sources).
    """
    rows = (
        await db.scalars(
            select(TrademarkSourceDetail).order_by(TrademarkSourceDetail.catalog_id.asc())
        )
    ).all()
    items: list[TrademarkConnectReadinessOut] = []
    for row in rows:
        readiness = _connect_readiness(row)
        if not readiness:
            continue
        items.append(
            TrademarkConnectReadinessOut(
                source_id=row.source_id,
                catalog_id=row.catalog_id,
                connect_readiness=readiness,
                can_query=True,
                can_refresh=True,
            )
        )
    return TrademarkConnectReadinessList(items=items, total=len(items))


@router.get(
    "/catalog/{catalog_id}/details",
    response_model=TrademarkSourceDetailOut,
)
async def get_trademark_details_by_catalog(
    catalog_id: str,
    db: AsyncSession = Depends(get_db),
):
    cid = catalog_id.strip().upper()
    row = await db.scalar(
        select(TrademarkSourceDetail).where(TrademarkSourceDetail.catalog_id == cid)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Trademark source details not found")
    return _to_out(row)
