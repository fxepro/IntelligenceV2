"""Persisted application settings."""

from pathlib import Path



from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession



from app.config import get_settings

from app.database import get_db

from app.models.app_setting import AppSetting

from app.services.discovery_config import normalize_discovery_settings
from app.services.transcription_config import (
    TRANSCRIPTION_DEFAULTS,
    normalize_transcription_settings,
)
from app.services.openai_transcription import (
    OPENAI_MODELS,
    OPENAI_USD_PER_MINUTE,
    SPOKEN_WORDS_PER_MINUTE_ESTIMATE,
    usd_per_word_estimate,
)



router = APIRouter()



ROOT = Path(__file__).resolve().parents[3]

WHISPER_ROOT = ROOT / "infra" / "whisper"

WHISPER_CLI = WHISPER_ROOT / "bin" / "whisper-cli.exe"

WHISPER_MODELS = (

    "tiny",

    "base",

    "small",

    "medium",

    "large-v3-turbo",

    "large-v3",

)

DEFAULTS = dict(TRANSCRIPTION_DEFAULTS)


class TranscriptionSettings(BaseModel):

    engine: str = "whisper_cpp"

    model: str = "medium"

    language: str = "auto"

    keep_audio: bool = False

    concurrency: int = 1

    batch_size: int = 20


class DiscoverySettings(BaseModel):
    interval_minutes: int = 60
    max_items: int = 100
    media_page_size: int = 500
    url_check_enabled: bool = False
    url_check_interval_minutes: int = 360





def _pricing_payload() -> dict:

    models = {}

    for model, usd_per_minute in OPENAI_USD_PER_MINUTE.items():

        models[model] = {

            "usd_per_minute": usd_per_minute,

            "usd_per_hour": round(usd_per_minute * 60, 4),

            "usd_per_word_estimate": usd_per_word_estimate(model),

        }

    return {

        "billing_unit": "audio_minute",

        "words_per_minute_estimate": SPOKEN_WORDS_PER_MINUTE_ESTIMATE,

        "note": "OpenAI bills per second of audio, not per word. Per-word figures assume ~140 spoken words/min.",

        "openai": models,

        "whisper_cpp": {

            "usd_per_minute": 0.0,

            "usd_per_word_estimate": 0.0,

            "note": "Local compute only — no API usage fee.",

        },

    }





def _response(value: dict) -> dict:

    settings = normalize_transcription_settings(value)

    engine = settings["engine"]

    if engine == "openai":

        available_models = list(OPENAI_MODELS)

    else:

        engine = "whisper_cpp"

        settings["engine"] = engine

        available_models = list(WHISPER_MODELS)



    model_path = WHISPER_ROOT / "models" / f"ggml-{settings['model']}.bin"

    return {

        **settings,

        "available_engines": ["whisper_cpp", "openai"],

        "available_models": available_models,

        "whisper_models": list(WHISPER_MODELS),

        "openai_models": list(OPENAI_MODELS),

        "whisper_installed": WHISPER_CLI.exists(),

        "model_installed": model_path.exists() if engine == "whisper_cpp" else True,

        "openai_configured": bool(get_settings().openai_api_key),

        "cli_path": str(WHISPER_CLI),

        "model_path": str(model_path),

        "pricing": _pricing_payload(),

    }





@router.get("/transcription")

async def get_transcription_settings(db: AsyncSession = Depends(get_db)):

    row = await db.get(AppSetting, "transcription")

    return _response(row.value if row else {})





@router.put("/transcription")

async def update_transcription_settings(

    payload: TranscriptionSettings,

    db: AsyncSession = Depends(get_db),

):

    value = normalize_transcription_settings(payload.model_dump())

    if value["engine"] == "openai":

        if value["model"] not in OPENAI_MODELS:

            value["model"] = "whisper-1"

    else:

        value["engine"] = "whisper_cpp"

        if value["model"] not in WHISPER_MODELS:

            value["model"] = "medium"

    value = normalize_transcription_settings(value)

    row = await db.get(AppSetting, "transcription")

    if row:

        row.value = value

    else:

        db.add(AppSetting(key="transcription", value=value))

    await db.flush()

    return _response(value)





def _discovery_response(value: dict) -> dict:
    return normalize_discovery_settings(value)





@router.get("/discovery")

async def get_discovery_settings(db: AsyncSession = Depends(get_db)):

    row = await db.get(AppSetting, "discovery")

    return _discovery_response(row.value if row else {})





@router.put("/discovery")

async def update_discovery_settings(

    payload: DiscoverySettings,

    db: AsyncSession = Depends(get_db),

):

    value = _discovery_response(payload.model_dump())

    row = await db.get(AppSetting, "discovery")

    if row:

        row.value = value

    else:

        db.add(AppSetting(key="discovery", value=value))

    await db.flush()

    return value


@router.post("/discovery/url-check-now")
async def run_url_check_now():
    """Retired — source URL check was removed."""
    raise HTTPException(status_code=410, detail="Source URL check has been removed")

