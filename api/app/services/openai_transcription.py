"""Sync OpenAI audio transcription for Celery workers."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

OPENAI_MODELS = (
    "whisper-1",
    "gpt-4o-transcribe",
    "gpt-4o-mini-transcribe",
)

# Official list prices (USD per audio minute). Billing is per second of audio.
OPENAI_USD_PER_MINUTE: dict[str, float] = {
    "whisper-1": 0.006,
    "gpt-4o-transcribe": 0.006,
    "gpt-4o-mini-transcribe": 0.003,
}

SPOKEN_WORDS_PER_MINUTE_ESTIMATE = 140
OPENAI_MAX_BYTES = 25 * 1024 * 1024


def usd_per_word_estimate(model: str) -> float:
    per_minute = OPENAI_USD_PER_MINUTE.get(model, OPENAI_USD_PER_MINUTE["whisper-1"])
    return per_minute / SPOKEN_WORDS_PER_MINUTE_ESTIMATE


def estimated_cost_usd(duration_seconds: float | int | None, model: str) -> float | None:
    if duration_seconds is None:
        return None
    per_minute = OPENAI_USD_PER_MINUTE.get(model, OPENAI_USD_PER_MINUTE["whisper-1"])
    return round((float(duration_seconds) / 60.0) * per_minute, 6)


def transcribe_file(
    audio_path: Path,
    *,
    model: str = "whisper-1",
    language: str = "auto",
) -> dict:
    api_key = get_settings().openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to v2/.env and restart workers.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    kwargs: dict = {"model": model}
    if model == "whisper-1":
        kwargs["response_format"] = "verbose_json"
    else:
        kwargs["response_format"] = "json"
    if language and language != "auto":
        kwargs["language"] = language

    with audio_path.open("rb") as handle:
        kwargs["file"] = handle
        response = client.audio.transcriptions.create(**kwargs)

    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return {"text": str(response)}


def normalize_openai_transcript(
    raw: dict,
    model: str,
    *,
    duration_seconds: float | int | None = None,
) -> dict:
    segments_raw = raw.get("segments") or []
    text_parts: list[str] = []
    normalized_segments: list[dict] = []
    for segment in segments_raw:
        text = str(segment.get("text") or "").strip()
        if text:
            text_parts.append(text)
        start = segment.get("start")
        end = segment.get("end")
        normalized_segments.append(
            {
                "start_ms": int(float(start) * 1000) if start is not None else None,
                "end_ms": int(float(end) * 1000) if end is not None else None,
                "text": text,
            }
        )

    full_text = str(raw.get("text") or " ".join(text_parts)).strip()
    duration = duration_seconds if duration_seconds is not None else raw.get("duration")
    billing = {
        "unit": "audio_minute",
        "usd_per_minute": OPENAI_USD_PER_MINUTE.get(model, OPENAI_USD_PER_MINUTE["whisper-1"]),
        "usd_per_word_estimate": usd_per_word_estimate(model),
        "words_per_minute_estimate": SPOKEN_WORDS_PER_MINUTE_ESTIMATE,
        "duration_seconds": duration,
        "estimated_cost_usd": estimated_cost_usd(duration, model),
    }
    return {
        "provider": "openai",
        "model": model,
        "language": raw.get("language"),
        "text": full_text,
        "full_text": full_text,
        "word_count": len(full_text.split()) if full_text else 0,
        "segments": normalized_segments,
        "billing": billing,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
