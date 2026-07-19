"""
Fuzzy ranking layer.

Two-stage: always compute a deterministic heuristic score (so the feature
works with zero API keys), then — if an OpenAI key is configured — let the LLM
re-rank and write a one-line "why this matches" reason. The LLM only reorders
and explains real candidates; it never invents them.
"""
import json
import math
import re
from datetime import datetime, timezone

from app.config import get_settings
from app.services.research.types import RawCandidate

settings = get_settings()

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "of", "and", "or", "for", "to", "in", "on", "who", "what", "is", "are", "about"}


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOP and len(t) > 1}


def _recency_boost(last_active: datetime | None) -> float:
    if not last_active:
        return 0.0
    if last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - last_active).days
    if days <= 14:
        return 20.0
    if days <= 90:
        return 12.0
    if days <= 365:
        return 6.0
    return 0.0


def _size_boost(c: RawCandidate) -> float:
    size = c.subscriber_count or c.item_count or 0
    return min(math.log10(size + 1) * 4, 15.0)


def _heuristic_score(query_tokens: set[str], c: RawCandidate) -> float:
    text_tokens = _tokens(f"{c.name or ''} {c.description or ''}")
    overlap = len(query_tokens & text_tokens) / max(len(query_tokens), 1)
    base = overlap * 50.0
    base += min(c.match_signal * 4, 20.0)  # youtube channel ownership signal
    base += _recency_boost(c.last_active_at)
    base += _size_boost(c)
    return round(min(base, 99.0), 1)


def _heuristic_reason(c: RawCandidate) -> str:
    bits = []
    if c.subscriber_count:
        bits.append(f"{c.subscriber_count:,} subscribers")
    if c.item_count:
        bits.append(f"{c.item_count:,} items")
    if c.last_active_at:
        days = (datetime.now(timezone.utc) - c.last_active_at.replace(tzinfo=c.last_active_at.tzinfo or timezone.utc)).days
        bits.append("active recently" if days <= 30 else f"last active ~{days}d ago")
    if c.match_signal:
        bits.append(f"{c.match_signal} matching results")
    return "; ".join(bits) or f"{c.platform} source matching your query"


async def _llm_rerank(query: str, candidates: list[RawCandidate]) -> bool:
    """Mutate candidate score/reason via the LLM. Returns True on success."""
    if not settings.openai_api_key:
        return False
    try:
        from app.services.openai_client import chat_completion

        payload = [
            {
                "index": i,
                "platform": c.platform,
                "name": c.name,
                "description": (c.description or "")[:300],
                "subscribers": c.subscriber_count,
                "items": c.item_count,
                "last_active": c.last_active_at.isoformat() if c.last_active_at else None,
            }
            for i, c in enumerate(candidates)
        ]
        system = (
            "You rank candidate media sources by how well they match an intelligence "
            "analyst's research intent. Use ONLY the provided data; do not invent facts. "
            'Respond as JSON: {"rankings":[{"index":int,"score":0-100,"reason":"<=15 words"}]}. '
            "Score reflects topical relevance, authority (size), and recency."
        )
        user = json.dumps({"intent": query, "candidates": payload})
        raw = await chat_completion(system, user, response_format={"type": "json_object"})
        parsed = json.loads(raw)
        for item in parsed.get("rankings", []):
            idx = item.get("index")
            if isinstance(idx, int) and 0 <= idx < len(candidates):
                if item.get("score") is not None:
                    candidates[idx].relevance_score = round(float(item["score"]), 1)
                if item.get("reason"):
                    candidates[idx].ai_reason = str(item["reason"])[:280]
        return True
    except Exception:
        return False


async def rank_candidates(query: str, candidates: list[RawCandidate]) -> list[RawCandidate]:
    query_tokens = _tokens(query)

    # stage 1 — deterministic baseline (always)
    for c in candidates:
        c.relevance_score = _heuristic_score(query_tokens, c)
        c.ai_reason = _heuristic_reason(c)

    # stage 2 — LLM refinement (only top 25, only if key configured)
    candidates.sort(key=lambda c: c.relevance_score or 0, reverse=True)
    await _llm_rerank(query, candidates[:25])

    candidates.sort(key=lambda c: c.relevance_score or 0, reverse=True)
    return candidates
