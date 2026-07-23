"""Per-source trademark office detail (standard 26-column enrichment profile)."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrademarkSourceDetail(Base):
    """
    1:1 companion to sources (domain=trademarks).

    Table: trademark_source_details
    Keyed by source_id; catalog_id denormalized for seed/import convenience.
    """

    __tablename__ = "trademark_source_details"
    __table_args__ = (
        UniqueConstraint("source_id", name="uq_trademark_source_details_source_id"),
        UniqueConstraint("catalog_id", name="uq_trademark_source_details_catalog_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(256), nullable=True)
    office: Mapped[str | None] = mapped_column(String(512), nullable=True)

    search_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status_lookup_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    filing_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    registry_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    gazette_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    journal_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    api_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    api_docs_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    bulk_download_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    # Manual API key for this source (encrypted). Not part of sheet enrichment.
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    response_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    pagination: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_parameters: Mapped[str | None] = mapped_column(Text, nullable=True)

    access_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authentication: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate_limit: Mapped[str | None] = mapped_column(Text, nullable=True)
    supports_nice_classes: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    supports_image_search: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    update_frequency: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
