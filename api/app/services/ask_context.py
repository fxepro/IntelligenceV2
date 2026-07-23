"""Build grounded platform context for Ask (AI chat over catalog facts)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import Record
from app.models.source import Source, SourceStatus


PLATFORM_DOMAINS = [
    "media",
    "finance",
    "software",
    "business",
    "government",
    "taxes",
    "healthcare",
    "people",
    "geography",
    "politics",
    "nonprofit",
    "news",
    "real_estate",
    "auctions",
    "torrents",
    "trademarks",
    "domain_names",
    "patents",
    "songs",
    "music",
    "books",
    "movies",
    "fiction",
]


@dataclass
class PlatformFacts:
    source_total: int
    active: int
    by_platform: list[tuple[str, int]]
    domain_counts: list[tuple[str, int]]
    recent_sources: list[tuple[str, str, str, str]]  # name, platform, url, domain
    recent_records: list[tuple[str, str, str]]  # title, url, domain

    def as_context(self) -> str:
        platform_lines = [f"  - {p}: {n}" for p, n in self.by_platform] or ["  - (none yet)"]
        domain_lines = [f"  - {d}: {n} records" for d, n in self.domain_counts] or [
            "  - (no records yet)"
        ]
        source_lines = [
            f"  - [{domain}] {name} ({platform}) — {url}"
            for name, platform, url, domain in self.recent_sources
        ] or ["  - (none yet)"]
        recent_lines = [
            f"  - [{domain}] {title} — {url or '—'}"
            for title, url, domain in self.recent_records
        ] or ["  - (none yet)"]
        return "\n".join(
            [
                "PLATFORM SNAPSHOT (ground truth — do not invent beyond this):",
                f"Registered domain planes: {', '.join(PLATFORM_DOMAINS)}",
                f"Sources total: {self.source_total} (active: {self.active})",
                "Sources by platform:",
                *platform_lines,
                "Records by domain:",
                *domain_lines,
                "Recent monitored sources:",
                *source_lines,
                "Recent catalog records:",
                *recent_lines,
            ]
        )


async def build_platform_facts(db: AsyncSession) -> PlatformFacts:
    source_total = await db.scalar(select(func.count()).select_from(Source)) or 0
    active = (
        await db.scalar(
            select(func.count())
            .select_from(Source)
            .where(Source.status == SourceStatus.active)
        )
        or 0
    )
    by_platform_rows = (
        await db.execute(
            select(Source.platform, func.count())
            .group_by(Source.platform)
            .order_by(func.count().desc())
        )
    ).all()
    by_platform = [(str(getattr(p, "value", p)), int(n)) for p, n in by_platform_rows]

    domain_rows = (
        await db.execute(
            select(Record.domain, func.count())
            .group_by(Record.domain)
            .order_by(func.count().desc())
        )
    ).all()
    domain_counts = [(str(d), int(n)) for d, n in domain_rows]

    recent = (
        await db.execute(
            select(Record.title, Record.canonical_url, Record.domain)
            .order_by(Record.created_at.desc())
            .limit(12)
        )
    ).all()
    recent_records = [
        ((title or "Untitled").replace("\n", " ").strip()[:100], url or "", str(domain))
        for title, url, domain in recent
    ]

    sources_sample = (
        await db.execute(
            select(Source.name, Source.platform, Source.source_url, Source.domain)
            .order_by(Source.updated_at.desc())
            .limit(15)
        )
    ).all()
    recent_sources = [
        (
            str(name),
            str(getattr(platform, "value", platform)),
            str(url),
            str(domain),
        )
        for name, platform, url, domain in sources_sample
    ]

    return PlatformFacts(
        source_total=int(source_total),
        active=int(active),
        by_platform=by_platform,
        domain_counts=domain_counts,
        recent_sources=recent_sources,
        recent_records=recent_records,
    )


async def build_platform_context(db: AsyncSession) -> str:
    return (await build_platform_facts(db)).as_context()


SYSTEM_PROMPT = """You are Ask inside the Intelligence platform.

You help operators query what is already in the platform: domains, sources, catalog records, and pipeline status implied by the snapshot.

Rules:
- Answer only from the PLATFORM SNAPSHOT and the conversation. If something is not in the snapshot, say you do not have that in platform context yet.
- Never invent sources, URLs, transcripts, or record counts.
- Prefer short, direct answers. Use bullet lists when listing entities.
- When relevant, point the operator to Research (find sources), Sources (monitor), Intelligence (read catalog), or Domains (pick a control plane).
- You are not a general web search engine.
"""


def local_reply(question: str, facts: PlatformFacts, *, reason: str | None = None) -> str:
    """
    Short deterministic answers from structured facts.
    Used when OpenAI is missing or rate-limited — never dump the full snapshot
    unless the user asks for an overview/snapshot.
    """
    q = (question or "").strip().lower()
    header = f"{reason}\n\n" if reason else ""

    want_snapshot = any(
        tok in q
        for tok in ("snapshot", "overview", "full context", "everything", "dump")
    )
    if want_snapshot:
        return header + facts.as_context()

    if any(tok in q for tok in ("how many source", "source count", "sources am i", "monitoring")):
        platforms = ", ".join(f"{p} {n}" for p, n in facts.by_platform) or "none"
        return (
            f"{header}"
            f"You are monitoring {facts.source_total} sources "
            f"({facts.active} active).\n"
            f"By platform: {platforms}."
        )

    if "active" in q and "source" in q:
        return f"{header}{facts.active} of {facts.source_total} sources are active."

    if any(tok in q for tok in ("domain", "plane")) and any(
        tok in q for tok in ("record", "have", "which", "what")
    ):
        if not facts.domain_counts:
            return f"{header}No domain has catalog records yet."
        lines = [f"- {d}: {n:,}" for d, n in facts.domain_counts]
        return f"{header}Domains with records:\n" + "\n".join(lines)

    if any(tok in q for tok in ("how many record", "record count", "catalog size", "items")):
        total = sum(n for _, n in facts.domain_counts)
        by = ", ".join(f"{d} {n:,}" for d, n in facts.domain_counts) or "none"
        return f"{header}Catalog has {total:,} records ({by})."

    if any(tok in q for tok in ("recent catalog", "recent item", "recent reel", "latest")):
        if not facts.recent_records:
            return f"{header}No recent catalog records."
        lines = [
            f"- [{domain}] {title}" for title, _url, domain in facts.recent_records[:8]
        ]
        return f"{header}Recent catalog items:\n" + "\n".join(lines)

    if any(tok in q for tok in ("recent source", "which source", "list source", "my source")):
        if not facts.recent_sources:
            return f"{header}No sources yet."
        lines = [
            f"- {name} ({platform})"
            for name, platform, _url, _domain in facts.recent_sources[:10]
        ]
        return f"{header}Recently updated sources:\n" + "\n".join(lines)

    # Name lookup against recent sources
    for name, platform, url, domain in facts.recent_sources:
        if len(name) > 3 and name.lower() in q:
            return (
                f"{header}{name} — domain {domain}, platform {platform}.\n"
                f"{url}"
            )

    # Generic platform question
    m = re.search(r"\b(facebook|youtube|podcast|instagram|tiktok)\b", q)
    if m and ("how many" in q or "count" in q or "source" in q):
        plat = m.group(1)
        n = next((c for p, c in facts.by_platform if p == plat), 0)
        return f"{header}{n} {plat} source{'s' if n != 1 else ''}."

    if any(tok in q for tok in ("transcript", "intelligence", "read")):
        return (
            f"{header}Open Intelligence to browse catalog items and transcripts. "
            f"Catalog size right now: {sum(n for _, n in facts.domain_counts):,} records."
        )

    if any(tok in q for tok in ("research", "find channel", "new channel")):
        return f"{header}Use Research to find candidate channels, then promote them to Sources."

    # Default short summary — not the full dump
    platforms = ", ".join(f"{p} {n}" for p, n in facts.by_platform[:4]) or "none"
    records = sum(n for _, n in facts.domain_counts)
    return (
        f"{header}"
        f"Platform snapshot (short): {facts.source_total} sources "
        f"({facts.active} active); {records:,} catalog records. "
        f"Platforms: {platforms}.\n\n"
        "Ask something specific (e.g. source counts, domains with records, recent items), "
        "or say snapshot for the full context dump."
    )


