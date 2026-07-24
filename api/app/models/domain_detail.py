"""Owned domain portfolio rows (NameBright My domains) — not the shared records spine."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DomainDetail(Base):
    """
    One row per owned domain name in the account portfolio.

    Table: domain_details
    Distinct from `records` (shared cross-plane spine). This is personal registrar data.
    """

    __tablename__ = "domain_details"
    __table_args__ = (UniqueConstraint("domain_name", name="uq_domain_details_domain_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    domain_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whois_privacy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    upgraded_domain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    category: Mapped[str | None] = mapped_column(String(256), nullable=True)
    registrar: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider: Mapped[str] = mapped_column(String(64), default="namebright", nullable=False)

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # DNS / zone (NameBright host records + NS) — empty until detail sync fills them
    nameservers: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    dns_a: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    dns_aaaa: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    dns_cname: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    dns_mx: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    dns_txt: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    dns_srv: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    contacts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    provenance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dns_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
