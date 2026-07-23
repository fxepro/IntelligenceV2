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
        # site_url distinguishes multiple "website" logins (e.g. academy.scytale.ai).
        # Empty string for non-website platforms.
        UniqueConstraint(
            "platform",
            "username",
            "site_url",
            name="uq_platform_credentials_platform_username_site",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(512), nullable=False)
    # Which site these credentials are for when platform=website (origin URL).
    site_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="", server_default="")
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
