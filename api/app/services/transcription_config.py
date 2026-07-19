"""Shared transcription engine + pacing settings."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

TRANSCRIPTION_DEFAULTS = {
    "engine": "whisper_cpp",
    "model": "medium",
    "language": "auto",
    "keep_audio": False,
    "concurrency": 1,
    "batch_size": 20,
}

CONCURRENCY_CEILING = 16
BATCH_SIZE_CEILING = 200


def normalize_transcription_settings(value: dict | None) -> dict:
    settings = {**TRANSCRIPTION_DEFAULTS, **(value or {})}
    settings["keep_audio"] = bool(settings.get("keep_audio", False))
    settings["concurrency"] = max(1, min(CONCURRENCY_CEILING, int(settings.get("concurrency") or 1)))
    settings["batch_size"] = max(1, min(BATCH_SIZE_CEILING, int(settings.get("batch_size") or 20)))
    return settings


async def get_transcription_settings(db: AsyncSession) -> dict:
    row = await db.get(AppSetting, "transcription")
    return normalize_transcription_settings(row.value if row else {})


def get_transcription_settings_sync(session: Session) -> dict:
    row = session.get(AppSetting, "transcription")
    return normalize_transcription_settings(row.value if row else {})
