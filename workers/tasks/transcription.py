"""Sequential transcription: download audio → whisper.cpp or OpenAI → record JSONB."""
from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
import yt_dlp

from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "media"
WHISPER_ROOT = ROOT / "infra" / "whisper"
WHISPER_CLI = WHISPER_ROOT / "bin" / "whisper-cli.exe"


def _settings(session) -> dict:
    from app.services.transcription_config import get_transcription_settings_sync

    return get_transcription_settings_sync(session)


def _download_audio(url: str, work_dir: Path) -> Path:
    from app.services.platform_sessions import apply_cookies_to_ydl_opts

    work_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(work_dir / "source.%(ext)s")
    options = apply_cookies_to_ydl_opts(
        {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        },
        url,
        work_dir,
    )
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        path = Path(downloader.prepare_filename(info))
    if not path.exists():
        candidates = sorted(work_dir.glob("source.*"))
        if not candidates:
            raise RuntimeError("yt-dlp completed without an audio file")
        path = candidates[0]
    return path


def _to_wav(source: Path, work_dir: Path) -> Path:
    wav = work_dir / "audio.wav"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return wav


def _prepare_openai_audio(source: Path, work_dir: Path) -> Path:
    if source.stat().st_size <= 25 * 1024 * 1024:
        return source
    mp3 = work_dir / "audio-openai.mp3"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-b:a",
            "64k",
            str(mp3),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if mp3.stat().st_size > 25 * 1024 * 1024:
        raise RuntimeError("Audio exceeds OpenAI 25 MB limit even after compression")
    return mp3


def _run_whisper(wav: Path, model: str, language: str, work_dir: Path) -> dict:
    model_path = WHISPER_ROOT / "models" / f"ggml-{model}.bin"
    if not WHISPER_CLI.exists() or not model_path.exists():
        raise RuntimeError(
            f"Local Whisper is not installed for model '{model}'. Run: "
            f"powershell -ExecutionPolicy Bypass -File "
            f"\"{WHISPER_ROOT / 'install-whisper.ps1'}\" -Model {model}"
        )
    output = work_dir / "transcript"
    command = [
        str(WHISPER_CLI),
        "-m",
        str(model_path),
        "-f",
        str(wav),
        "-oj",
        "-of",
        str(output),
        "-t",
        str(max(1, (os.cpu_count() or 4) - 1)),
    ]
    if language and language != "auto":
        command.extend(["-l", language])
    subprocess.run(command, check=True, capture_output=True, text=True)
    result_path = output.with_suffix(".json")
    if not result_path.exists():
        raise RuntimeError("whisper.cpp completed without transcript JSON")
    return json.loads(result_path.read_text(encoding="utf-8"))


def _normalize_whisper_transcript(raw: dict, model: str) -> dict:
    segments = raw.get("transcription") or raw.get("segments") or []
    text_parts: list[str] = []
    normalized_segments: list[dict] = []
    for segment in segments:
        text = str(segment.get("text") or "").strip()
        if text:
            text_parts.append(text)
        offsets = segment.get("offsets") or {}
        normalized_segments.append(
            {
                "start_ms": offsets.get("from"),
                "end_ms": offsets.get("to"),
                "text": text,
            }
        )
    full_text = " ".join(text_parts).strip()
    result = raw.get("result") or {}
    language = result.get("language") or raw.get("language")
    return {
        "provider": "whisper_cpp",
        "model": model,
        "language": language,
        "text": full_text,
        "full_text": full_text,
        "word_count": len(full_text.split()),
        "segments": normalized_segments,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(name="tasks.transcription.drain_auto_transcribe")
def drain_auto_transcribe():
    """Top up Auto-transcribe pipelines (batch_size at a time) until pending is gone."""
    from app.services.transcription_queue import drain_auto_transcribe_sync

    with session_scope() as session:
        return drain_auto_transcribe_sync(session)


def _kick_auto_drain() -> None:
    """Best-effort: refill the next batch when a job frees a pipeline slot."""
    try:
        celery_app.send_task(
            "tasks.transcription.drain_auto_transcribe",
            queue="transcription",
        )
    except Exception:
        pass


@celery_app.task(name="tasks.transcription.run_transcribe", bind=True, max_retries=3)
def run_transcribe(self, job_id: str):
    try:
        with session_scope() as session:
            job = mark_running(session, job_id)
            if not job.record_id:
                raise ValueError("Transcription job missing record_id")

            from app.models.record import Record, RecordStatus

            record = session.get(Record, job.record_id)
            if not record or not record.canonical_url:
                raise ValueError(f"Media record {job.record_id} is missing")

            settings = _settings(session)
            fields = dict(record.fields or {})
            fields["download_status"] = "running"
            fields["transcription_status"] = "queued"
            record.fields = fields
            record.status = RecordStatus.in_progress
            job.progress = 0.1
            session.commit()

            work_dir = DATA_ROOT / str(record.id)
            source_file = _download_audio(record.canonical_url, work_dir)
            engine = str(settings.get("engine") or "whisper_cpp")

            fields = dict(record.fields or {})
            fields["download_status"] = "completed"
            fields["file_size_bytes"] = source_file.stat().st_size
            fields["local_file_path"] = str(source_file)
            fields["transcription_status"] = "running"
            record.fields = fields
            job.progress = 0.45
            session.commit()

            duration_seconds = fields.get("duration_seconds")

            if engine == "openai":
                from app.services.openai_transcription import (
                    normalize_openai_transcript,
                    transcribe_file,
                )

                audio = _prepare_openai_audio(source_file, work_dir)
                raw = transcribe_file(
                    audio,
                    model=str(settings["model"]),
                    language=str(settings["language"]),
                )
                transcript = normalize_openai_transcript(
                    raw,
                    str(settings["model"]),
                    duration_seconds=duration_seconds,
                )
                provider = "openai"
            else:
                wav = _to_wav(source_file, work_dir)
                raw = _run_whisper(
                    wav,
                    str(settings["model"]),
                    str(settings["language"]),
                    work_dir,
                )
                transcript = _normalize_whisper_transcript(raw, str(settings["model"]))
                provider = "whisper_cpp"
                wav.unlink(missing_ok=True)

            fields = dict(record.fields or {})
            fields["transcript"] = transcript
            fields["transcription_status"] = "completed"
            record.fields = fields
            record.status = RecordStatus.completed
            record.error_message = None

            if not settings.get("keep_audio"):
                for path in work_dir.glob("source.*"):
                    path.unlink(missing_ok=True)
                for path in work_dir.glob("audio-openai.mp3"):
                    path.unlink(missing_ok=True)
                fields = dict(record.fields or {})
                fields["local_file_path"] = None
                record.fields = fields

            mark_completed(
                session,
                job_id,
                {
                    "record_id": str(record.id),
                    "provider": provider,
                    "model": settings["model"],
                    "word_count": transcript["word_count"],
                },
            )
        _kick_auto_drain()
        return {"job_id": job_id, "ok": True}
    except Exception as exc:
        with session_scope() as session:
            from app.models.job import Job
            from app.models.record import Record, RecordStatus

            job = session.get(Job, uuid.UUID(job_id))
            if job and job.record_id:
                record = session.get(Record, job.record_id)
                if record:
                    fields = dict(record.fields or {})
                    fields["transcription_status"] = "failed"
                    record.fields = fields
                    record.status = RecordStatus.failed
                    record.error_message = f"{type(exc).__name__}: {exc}"[:2000]
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        _kick_auto_drain()
        raise self.retry(exc=exc, countdown=60)
