"""Platform login credentials + session cookies for gated scrapers."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.source import Platform


class CredentialStatus(str, enum.Enum):
    saved = "saved"
    connected = "connected"
    error = "error"


class PlatformCredential(Base):
    __tablename__ = "platform_credentials"
    __table_args__ = (
        UniqueConstraint("platform", "username", name="uq_platform_credentials_platform_username"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(512), nullable=False)
    password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    session_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[CredentialStatus] = mapped_column(
        Enum(CredentialStatus, name="credential_status"),
        default=CredentialStatus.saved,
        nullable=False,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
