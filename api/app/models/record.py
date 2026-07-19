import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RecordStatus(str, enum.Enum):
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    needs_review = "needs_review"


class Record(Base):
    """Shared spine record (Architecture v2 §5). Domain payload in `fields` JSONB."""

    __tablename__ = "records"
    __table_args__ = (UniqueConstraint("domain", "dedup_key", name="uq_records_domain_dedup"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    connector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fields: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    raw_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    provenance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="record_status"),
        default=RecordStatus.queued,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
