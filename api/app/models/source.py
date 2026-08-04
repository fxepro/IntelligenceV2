import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Platform(str, enum.Enum):
    youtube = "youtube"
    facebook = "facebook"
    x = "x"
    instagram = "instagram"
    tiktok = "tiktok"
    rss = "rss"
    podcast = "podcast"
    website = "website"
    # Offices / public authorities (trademarks, gov intel, etc.)
    government = "government"
    # Local folder on disk (Library domain).
    local = "local"


class SourceType(str, enum.Enum):
    facebook_reels = "facebook_reels"
    facebook_videos = "facebook_videos"
    x_posts = "x_posts"
    youtube_videos = "youtube_videos"
    youtube_shorts = "youtube_shorts"
    instagram_reels = "instagram_reels"
    tiktok_videos = "tiktok_videos"
    # Feed/site types remain platform-specific enough as-is.
    rss_feed = "rss_feed"
    sitemap = "sitemap"
    # Generic access surface (portals, registries, marketing sites).
    website = "website"
    # Legacy values retained so old/imported rows remain readable.
    channel = "channel"
    playlist = "playlist"
    profile = "profile"
    video = "video"
    # Library: manually registered folder path.
    local_folder = "local_folder"


class SourceStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    error = "error"


class SourcePriority(str, enum.Enum):
    # Display rank 1–5 where 1 is highest priority (urgent → lowest).
    urgent = "urgent"  # 1
    high = "high"  # 2
    normal = "normal"  # 3
    low = "low"  # 4
    lowest = "lowest"  # 5


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("domain", "catalog_id", name="uq_sources_domain_catalog_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain: Mapped[str] = mapped_column(String(64), default="media", nullable=False, index=True)
    # Stable human id per domain: MEDIA-0001, GOV-0001, … (not the UUID pk).
    catalog_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform"), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, name="source_type"), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    # Original vanity / handle URL when source_url was resolved to profile.php?id=…
    vanity_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Catalog taxonomy (e.g. procurement) — not freeform tags.
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    priority: Mapped[SourcePriority] = mapped_column(
        Enum(SourcePriority, name="source_priority"),
        default=SourcePriority.normal,
        nullable=False,
    )
    autorun: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # When True, successful Discover auto-queues pending items for transcription
    # (paced by Settings → Transcription concurrency / batch size).
    auto_transcribe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus, name="source_status"),
        default=SourceStatus.active,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Last automatic source-URL health probe (Settings → Discovery URL check).
    last_url_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Connector type for routing discovery (e.g., "strongdm", "drata", "youtube")
    connector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
