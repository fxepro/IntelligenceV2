import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.job import JobStatus, JobType
from app.models.source import Platform, SourcePriority, SourceStatus, SourceType
from app.models.record import RecordStatus


class JobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_type: JobType
    status: JobStatus
    domain: str
    source_id: uuid.UUID | None
    record_id: uuid.UUID | None
    celery_task_id: str | None
    progress: float
    payload: dict | None
    result: dict | None
    error_message: str | None
    attempt: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class EnqueueResponse(BaseModel):
    job_id: uuid.UUID
    status: JobStatus = JobStatus.queued


class SourceStreamOut(BaseModel):
    id: uuid.UUID
    stream_type: SourceType
    stream_url: str | None = None
    enabled: bool = True
    item_count: int = 0
    last_checked: datetime | None = None
    error_message: str | None = None


class SourceCreate(BaseModel):
    domain: str = "media"
    platform: Platform
    source_type: SourceType
    source_url: str = Field(..., min_length=8, max_length=2048)
    # Optional; for Facebook we also resolve vanity → profile.php?id= automatically.
    vanity_url: str | None = None
    # Optional stable id (GOV-0001). Auto-allocated per domain when omitted.
    catalog_id: str | None = Field(default=None, max_length=32)
    stream_urls: dict[str, str] = Field(default_factory=dict)
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: SourcePriority = SourcePriority.normal
    autorun: bool = False
    auto_transcribe: bool = False
    access_mode: str = "public"
    # Library course slug → v2/data/{course_id}/ on disk
    course_id: str | None = Field(default=None, max_length=128)
    connector: str | None = Field(default=None, max_length=64)


class SourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    source_url: str | None = None
    vanity_url: str | None = None
    catalog_id: str | None = None
    category: str | None = None
    stream_urls: dict[str, str] | None = None
    source_type: SourceType | None = None
    status: SourceStatus | None = None
    autorun: bool | None = None
    auto_transcribe: bool | None = None
    tags: list[str] | None = None
    priority: SourcePriority | None = None
    course_id: str | None = Field(default=None, max_length=128)
    connector: str | None = Field(default=None, max_length=64)


class SourceOut(BaseModel):
    """Shape aligned with v1 UI `mapSource`."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    domain: str = "media"
    catalog_id: str | None = None
    platform: Platform
    source_type: SourceType
    source_url: str
    vanity_url: str | None = None
    name: str | None
    description: str | None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: SourcePriority = SourcePriority.normal
    access_mode: str = "public"
    autorun: bool
    auto_transcribe: bool = False
    status: SourceStatus
    error_message: str | None
    last_checked: datetime | None
    subscriber_count: int | None = None
    video_count: int | None = None
    total_views: int | None = None
    joined_at: datetime | None = None
    item_count: int = 0
    reel_count: int = 0
    # Catalog transcription progress (not the auto_transcribe toggle).
    transcription_completed: int = 0
    transcription_done: bool = False
    streams: list[SourceStreamOut] = Field(default_factory=list)
    connector: str | None = None
    created_at: datetime
    updated_at: datetime


class SourceList(BaseModel):
    items: list[SourceOut]
    total: int


from app.services.discovery_config import MAX_ITEMS_CEILING


class DiscoverRequest(BaseModel):
    max_items: int = Field(500, ge=1, le=MAX_ITEMS_CEILING)


class DiscoverSourceResponse(BaseModel):
    """Compat with v1 Sources UI — items empty until worker connectors write results."""

    source_id: uuid.UUID
    job_id: uuid.UUID
    new: int = 0
    total_found: int = 0
    items: list[dict] = []
    status: str = "queued"


class RecordOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    domain: str
    source_id: uuid.UUID | None
    connector: str | None
    external_id: str | None
    dedup_key: str
    canonical_url: str | None
    title: str | None
    fields: dict
    status: RecordStatus
    confidence: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class RecordList(BaseModel):
    items: list[RecordOut]
    total: int


class MediaItemOut(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID | None = None
    platform: str | None = None
    external_id: str | None = None
    canonical_url: str | None = None
    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    thumbnail_url: str | None = None
    channel_name: str | None = None
    duration_seconds: int | None = None
    file_size_bytes: int | None = None
    view_count: int | None = None
    stream_type: str | None = None
    download_status: str = "pending"
    transcription_status: str = "pending"
    transcript: dict | None = None
    summary: dict | None = None
    published_at: datetime | None = None
    discovered_at: datetime | None = None
    processed_at: datetime | None = None
    status: str = "queued"
    error_message: str | None = None


class MediaItemList(BaseModel):
    items: list[MediaItemOut]
    total: int
    page: int = 1
    page_size: int = 50


class TranscriptListItem(BaseModel):
    media_id: uuid.UUID
    title: str | None = None
    canonical_url: str | None = None
    thumbnail_url: str | None = None
    published_at: str | None = None
    discovered_at: str | None = None
    status: str = "completed"
    full_text: str
    language: str | None = None
    word_count: int | None = None
    model_used: str | None = None
    generated_at: str | None = None


class TranscriptListResponse(BaseModel):
    items: list[TranscriptListItem]
    total: int
    page: int = 1
    page_size: int = 50


class HealthOut(BaseModel):
    status: str
    version: str
    topology: str


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1024)
    platforms: list[str] | None = None
    max_per_platform: int = Field(10, ge=1, le=25)


class ResearchCandidateOut(BaseModel):
    id: str
    query: str
    platform: str
    external_id: str | None = None
    name: str | None = None
    url: str
    thumbnail_url: str | None = None
    description: str | None = None
    suggested_source_type: str | None = None
    subscriber_count: int | None = None
    item_count: int | None = None
    total_views: int | None = None
    last_active_at: datetime | None = None
    relevance_score: float | None = None
    ai_reason: str | None = None
    status: str = "suggested"
    created_at: datetime | None = None


class ResearchResponse(BaseModel):
    query: str
    total: int
    candidates: list[ResearchCandidateOut]
    notices: list[str] = []
