"""Sync DB helpers for Celery workers."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Load v2/.env when worker starts from workers/
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")


def _sync_url() -> str:
    """Use psycopg v3 — psycopg2 is broken on Python 3.14 / Windows."""
    raw = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/intelligence",
    )
    if raw.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+psycopg2://")
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


DATABASE_URL_SYNC = _sync_url()

engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def mark_running(session: Session, job_id: str):
    from app.models.job import Job, JobStatus

    job = session.get(Job, uuid.UUID(job_id))
    if not job:
        raise ValueError(f"Job {job_id} not found")
    job.status = JobStatus.running
    job.started_at = datetime.now(timezone.utc)
    job.attempt = (job.attempt or 0) + 1
    job.progress = 0.05
    session.flush()
    return job


def mark_completed(session: Session, job_id: str, result: dict | None = None):
    from app.models.job import Job, JobStatus

    job = session.get(Job, uuid.UUID(job_id))
    if not job:
        raise ValueError(f"Job {job_id} not found")
    job.status = JobStatus.completed
    job.progress = 1.0
    job.result = result or {}
    job.finished_at = datetime.now(timezone.utc)
    job.error_message = None
    session.flush()
    return job


def mark_failed(session: Session, job_id: str, error: str):
    from app.models.job import Job, JobStatus

    job = session.get(Job, uuid.UUID(job_id))
    if not job:
        return
    job.status = JobStatus.failed
    job.error_message = error[:2000]
    job.finished_at = datetime.now(timezone.utc)
    session.flush()
    return job
