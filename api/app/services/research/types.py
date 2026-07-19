from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawCandidate:
    """A normalised source candidate before persistence."""
    platform: str
    url: str
    name: str | None = None
    external_id: str | None = None
    thumbnail_url: str | None = None
    description: str | None = None
    suggested_source_type: str | None = None

    subscriber_count: int | None = None
    item_count: int | None = None
    total_views: int | None = None
    last_active_at: datetime | None = None

    relevance_score: float | None = None
    ai_reason: str | None = None

    # internal signal used by the heuristic ranker (e.g. how many of the
    # query's top results belonged to this channel)
    match_signal: int = 0


@dataclass
class ResearchResult:
    query: str
    candidates: list[RawCandidate] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
