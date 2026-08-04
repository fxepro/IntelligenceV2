"""Government fetched items — contract opportunities, grants, etc. (not records spine)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GovernmentDetail(Base):
    """
    One row per fetched government item (e.g. SAM.gov opportunity).

    Table: government_details
    """

    __tablename__ = "government_details"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_government_details_dedup_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    connector: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    notice_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    dedup_key: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    solicitation_number: Mapped[str | None] = mapped_column(String(256), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_deadline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notice_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    base_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    naics_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    classification_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    set_aside: Mapped[str | None] = mapped_column(String(256), nullable=True)
    set_aside_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    active: Mapped[str | None] = mapped_column(String(16), nullable=True)
    description_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
