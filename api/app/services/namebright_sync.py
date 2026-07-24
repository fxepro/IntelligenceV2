"""Sync NameBright account domains into domain_details (owned portfolio table)."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain_detail import DomainDetail
from app.models.record import Record
from app.models.source import Platform, Source, SourcePriority, SourceStatus, SourceType
from app.services.catalog_ids import _next_number_sync, catalog_prefix, format_catalog_id
from app.services.namebright import (
    get_host_records,
    get_nameservers,
    list_account_domains,
    _ipv4_client,
    get_access_token,
)


SOURCE_URL = "https://www.namebright.com/"
PROVIDER = "namebright"


def _ensure_source(session: Session) -> Source:
    row = session.scalar(
        select(Source).where(
            Source.domain == "domain_names",
            Source.source_url == SOURCE_URL,
        )
    )
    if row:
        return row

    prefix = catalog_prefix("domain_names")
    n = _next_number_sync(session, "domain_names", prefix)
    catalog_id = format_catalog_id(prefix, n)

    row = Source(
        domain="domain_names",
        platform=Platform.website,
        source_type=SourceType.website,
        source_url=SOURCE_URL,
        catalog_id=catalog_id,
        name="NameBright",
        description="NameBright registrar API — account portfolio (My domains).",
        category="My domains",
        tags=["registrar", "portfolio", "api"],
        status=SourceStatus.active,
        priority=SourcePriority.normal,
    )
    session.add(row)
    session.flush()
    return row


def _parse_dt(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    text = str(raw).strip()
    if not text:
        return None
    try:
        # NameBright often returns ISO-ish strings
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _bool(item: dict[str, Any], *keys: str) -> bool:
    for k in keys:
        if k in item and item[k] is not None:
            return bool(item[k])
    return False


def _purge_legacy_portfolio_records(session: Session) -> int:
    """Remove old spine rows that used records for My domains."""
    rows = session.scalars(
        select(Record).where(
            Record.domain == "domain_names",
            Record.fields["sub_plane"].as_string() == "portfolio",
        )
    ).all()
    n = 0
    for row in rows:
        session.delete(row)
        n += 1
    return n


def _apply_dns(row: DomainDetail, name: str, *, client: Any, token: str, now: datetime) -> None:
    ns = get_nameservers(name, client=client, token=token)
    time.sleep(1.05)
    hr = get_host_records(name, client=client, token=token)
    row.nameservers = ns
    row.dns_a = hr.get("a") or []
    row.dns_aaaa = hr.get("aaaa") or []
    row.dns_cname = hr.get("cname") or []
    row.dns_mx = hr.get("mx") or []
    row.dns_txt = hr.get("txt") or []
    row.dns_srv = hr.get("srv") or []
    row.dns_synced_at = now


def sync_domain_dns(session: Session, domain_name: str) -> dict[str, Any]:
    """Pull nameservers + host records for one owned domain into domain_details."""
    name = domain_name.strip().lower()
    row = session.scalar(select(DomainDetail).where(DomainDetail.domain_name == name))
    if not row:
        raise ValueError(f"Domain not in portfolio: {name}")

    now = datetime.now(timezone.utc)
    token = get_access_token()
    with _ipv4_client(timeout=60.0) as client:
        try:
            _apply_dns(row, name, client=client, token=token, now=now)
            row.provenance = {
                **(row.provenance or {}),
                "dns_api": "GET nameservers + hostrecords/all",
                "dns_synced_at": now.isoformat(),
                "dns_error": None,
            }
        except Exception as exc:
            row.provenance = {
                **(row.provenance or {}),
                "dns_error": str(exc)[:400],
            }
            raise

    session.flush()
    return {
        "provider": PROVIDER,
        "table": "domain_details",
        "domain_name": name,
        "nameservers": len(row.nameservers or []),
        "dns_a": len(row.dns_a or []),
        "dns_aaaa": len(row.dns_aaaa or []),
        "dns_cname": len(row.dns_cname or []),
        "dns_mx": len(row.dns_mx or []),
        "dns_txt": len(row.dns_txt or []),
        "dns_srv": len(row.dns_srv or []),
        "dns_synced_at": now.isoformat(),
    }


def sync_portfolio(session: Session, *, fetch_dns: bool = False) -> dict[str, Any]:
    """
    Fetch NameBright portfolio into domain_details.

    List fields always. When fetch_dns=True, also pulls nameservers + host records
    per domain (slow — ~2s each under NameBright rate limits).
    """
    source = _ensure_source(session)
    raw_domains = list_account_domains()
    now = datetime.now(timezone.utc)
    upserted = 0
    skipped = 0
    dns_ok = 0
    dns_fail = 0
    seen: set[str] = set()

    token = get_access_token()
    with _ipv4_client(timeout=60.0) as client:
        for item in raw_domains:
            name = (item.get("DomainName") or item.get("domainName") or "").strip().lower()
            if not name:
                skipped += 1
                continue
            seen.add(name)

            row = session.scalar(select(DomainDetail).where(DomainDetail.domain_name == name))
            if not row:
                row = DomainDetail(domain_name=name)
                session.add(row)

            row.status = item.get("Status") or item.get("status")
            row.purchase_date = _parse_dt(
                item.get("PurchaseDate")
                or item.get("purchaseDate")
                or item.get("RegistrationDate")
                or item.get("registrationDate")
            )
            row.expiration_date = _parse_dt(
                item.get("ExpirationDate") or item.get("expirationDate")
            )
            row.locked = _bool(item, "Locked", "locked")
            row.auto_renew = _bool(item, "AutoRenew", "autoRenew")
            row.whois_privacy = _bool(item, "WhoIsPrivacy", "whoIsPrivacy")
            row.upgraded_domain = _bool(item, "UpgradedDomain", "upgradedDomain")
            row.category = item.get("Category") or item.get("category")
            row.registrar = "NameBright"
            row.provider = PROVIDER
            row.source_id = source.id
            row.synced_at = now
            row.provenance = {
                "provider": PROVIDER,
                "api": "GET /account/domains",
                "synced_at": now.isoformat(),
            }

            if fetch_dns:
                try:
                    time.sleep(1.05)
                    _apply_dns(row, name, client=client, token=token, now=now)
                    dns_ok += 1
                except Exception as exc:  # noqa: BLE001 — keep portfolio row even if DNS fails
                    dns_fail += 1
                    row.provenance = {
                        **(row.provenance or {}),
                        "dns_error": str(exc)[:400],
                    }

            upserted += 1

    # Drop domains no longer in the account
    removed = 0
    if seen:
        stale = session.scalars(
            select(DomainDetail).where(
                DomainDetail.provider == PROVIDER,
                DomainDetail.domain_name.notin_(seen),
            )
        ).all()
        for row in stale:
            session.delete(row)
            removed += 1

    legacy_purged = _purge_legacy_portfolio_records(session)
    session.flush()

    return {
        "provider": PROVIDER,
        "table": "domain_details",
        "fetched": len(raw_domains),
        "upserted": upserted,
        "skipped": skipped,
        "removed": removed,
        "dns_ok": dns_ok,
        "dns_fail": dns_fail,
        "legacy_records_purged": legacy_purged,
        "source_id": str(source.id),
        "catalog_id": source.catalog_id,
    }
