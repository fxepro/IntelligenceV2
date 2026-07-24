"""Domains control plane — My domains (NameBright → domain_details)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain_detail import DomainDetail
from app.models.job import JobType
from app.schemas import JobOut
from app.services.jobs import enqueue_job
from app.services.namebright import credentials_configured

router = APIRouter()


class PortfolioDomainOut(BaseModel):
    id: uuid.UUID
    domain_name: str
    status: str | None = None
    purchase_date: str | None = None
    expiration_date: str | None = None
    locked: bool = False
    auto_renew: bool = False
    whois_privacy: bool = False
    upgraded_domain: bool = False
    category: str | None = None
    registrar: str | None = None
    provider: str = "namebright"
    nameservers: list[Any] = Field(default_factory=list)
    dns_a: list[Any] = Field(default_factory=list)
    dns_aaaa: list[Any] = Field(default_factory=list)
    dns_cname: list[Any] = Field(default_factory=list)
    dns_mx: list[Any] = Field(default_factory=list)
    dns_txt: list[Any] = Field(default_factory=list)
    dns_srv: list[Any] = Field(default_factory=list)
    synced_at: str | None = None
    dns_synced_at: str | None = None


class PortfolioListOut(BaseModel):
    items: list[PortfolioDomainOut]
    total: int
    credentials_configured: bool


def _iso(dt: Any) -> str | None:
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def _to_out(row: DomainDetail) -> PortfolioDomainOut:
    return PortfolioDomainOut(
        id=row.id,
        domain_name=row.domain_name,
        status=row.status,
        purchase_date=_iso(row.purchase_date),
        expiration_date=_iso(row.expiration_date),
        locked=bool(row.locked),
        auto_renew=bool(row.auto_renew),
        whois_privacy=bool(row.whois_privacy),
        upgraded_domain=bool(row.upgraded_domain),
        category=row.category,
        registrar=row.registrar,
        provider=row.provider or "namebright",
        nameservers=list(row.nameservers or []),
        dns_a=list(row.dns_a or []),
        dns_aaaa=list(row.dns_aaaa or []),
        dns_cname=list(row.dns_cname or []),
        dns_mx=list(row.dns_mx or []),
        dns_txt=list(row.dns_txt or []),
        dns_srv=list(row.dns_srv or []),
        synced_at=_iso(row.synced_at),
        dns_synced_at=_iso(row.dns_synced_at),
    )


@router.get("/portfolio", response_model=PortfolioListOut)
async def list_portfolio(
    q: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DomainDetail).order_by(DomainDetail.domain_name.asc()).limit(limit)
    rows = (await db.scalars(stmt)).all()
    query = (q or "").strip().lower()
    items: list[PortfolioDomainOut] = []
    for row in rows:
        name = (row.domain_name or "").strip()
        if query and query not in name.lower():
            continue
        items.append(_to_out(row))
    total = await db.scalar(select(func.count()).select_from(DomainDetail))
    return PortfolioListOut(
        items=items,
        total=int(total or 0),
        credentials_configured=credentials_configured(),
    )


@router.post("/portfolio/sync", response_model=JobOut)
async def sync_portfolio(db: AsyncSession = Depends(get_db)):
    """Enqueue NameBright portfolio list pull into domain_details (Celery acquire)."""
    if not credentials_configured():
        raise HTTPException(
            status_code=400,
            detail="NameBright credentials missing. Set NAMEBRIGHT_CLIENT_ID and "
            "NAMEBRIGHT_CLIENT_SECRET in v2/.env",
        )
    try:
        job = await enqueue_job(
            db,
            job_type=JobType.acquire,
            domain="domain_names",
            payload={"action": "namebright_portfolio_sync"},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return job


@router.get("/portfolio/{domain_name}", response_model=PortfolioDomainOut)
async def get_portfolio_domain(domain_name: str, db: AsyncSession = Depends(get_db)):
    name = domain_name.strip().lower()
    row = await db.scalar(select(DomainDetail).where(DomainDetail.domain_name == name))
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found in portfolio")
    return _to_out(row)


@router.post("/portfolio/{domain_name}/sync-dns", response_model=JobOut)
async def sync_portfolio_domain_dns(domain_name: str, db: AsyncSession = Depends(get_db)):
    """Enqueue nameserver + host-record pull for one domain."""
    if not credentials_configured():
        raise HTTPException(
            status_code=400,
            detail="NameBright credentials missing. Set NAMEBRIGHT_CLIENT_ID and "
            "NAMEBRIGHT_CLIENT_SECRET in v2/.env",
        )
    name = domain_name.strip().lower()
    row = await db.scalar(select(DomainDetail).where(DomainDetail.domain_name == name))
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found in portfolio")
    try:
        job = await enqueue_job(
            db,
            job_type=JobType.acquire,
            domain="domain_names",
            payload={"action": "namebright_dns_sync", "domain_name": name},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return job
