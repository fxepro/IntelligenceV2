"""Local stack status + process helpers (dev control plane)."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.config import get_settings

router = APIRouter()

ROOT = Path(__file__).resolve().parents[3]  # v2/
API_DIR = ROOT / "api"
WORKERS_DIR = ROOT / "workers"
REDIS_START = ROOT / "infra" / "redis" / "start-redis.ps1"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"


class ProcessStatus(BaseModel):
    id: str
    label: str
    status: str  # up | down | unknown | starting
    detail: str | None = None
    docs_url: str | None = None
    can_start: bool = False


class SystemStatusOut(BaseModel):
    processes: list[ProcessStatus]
    control_planes: list[dict]


def _tcp(host: str, port: int, timeout: float = 0.8) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _postgres_ok() -> tuple[bool, str]:
    try:
        from sqlalchemy import create_engine

        settings = get_settings()
        engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "postgresql connected"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _redis_ok() -> tuple[bool, str]:
    try:
        import redis

        settings = get_settings()
        r = redis.from_url(settings.redis_url or settings.celery_broker_url, socket_connect_timeout=1)
        if r.ping():
            return True, "PONG"
        return False, "no PONG"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _celery_ok() -> tuple[bool, str]:
    try:
        from celery import Celery

        settings = get_settings()
        app = Celery("probe", broker=settings.celery_broker_url)
        inspector = app.control.inspect(timeout=1.0)
        ping = inspector.ping() if inspector else None
        if ping:
            n = len(ping)
            return True, f"{n} worker{'s' if n != 1 else ''} responded"
        return False, "no workers responded to ping"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


@router.get("/status", response_model=SystemStatusOut)
async def system_status():
    settings = get_settings()
    api_docs = "http://127.0.0.1:8000/docs"

    pg_ok, pg_detail = _postgres_ok()
    redis_ok, redis_detail = _redis_ok()
    celery_ok, celery_detail = _celery_ok()
    web_ok = _tcp("127.0.0.1", 3000)

    processes = [
        ProcessStatus(
            id="api",
            label="API",
            status="up",
            detail="this process",
            docs_url=api_docs,
            can_start=False,
        ),
        ProcessStatus(
            id="postgres",
            label="PostgreSQL",
            status="up" if pg_ok else "down",
            detail=pg_detail,
            can_start=False,
        ),
        ProcessStatus(
            id="redis",
            label="Redis (Celery broker)",
            status="up" if redis_ok else "down",
            detail=redis_detail,
            can_start=REDIS_START.exists(),
        ),
        ProcessStatus(
            id="celery",
            label="Celery worker",
            status="up" if celery_ok else "down",
            detail=celery_detail,
            can_start=VENV_PY.exists(),
        ),
        ProcessStatus(
            id="web",
            label="Web (Next.js)",
            status="up" if web_ok else "down",
            detail="localhost:3000" if web_ok else "not listening on :3000",
            can_start=False,
        ),
    ]

    # Domain control planes — alphabetical by label (matches docs/domains)
    control_planes = [
        {
            "id": "media",
            "label": "Media",
            "status": "active",
            "blurb": "Social posts, videos, websites, podcasts, newsletters and channels",
            "home": "/research",
            "docs_url": api_docs,
        },
        {
            "id": "finance",
            "label": "Finance",
            "status": "planned",
            "blurb": "Markets, filings, companies, securities and financial signals",
            "home": "/finance",
            "docs_url": None,
        },
        {
            "id": "software",
            "label": "Software",
            "status": "planned",
            "blurb": "Products, vendors, licenses, codebases and digital platforms",
            "home": "/software",
            "docs_url": None,
        },
        {
            "id": "business",
            "label": "Business",
            "status": "planned",
            "blurb": "Companies, ownership, operations, filings and commercial signals",
            "home": "/business",
            "docs_url": None,
        },
        {
            "id": "government",
            "label": "Government",
            "status": "planned",
            "blurb": "Agencies, regulations, procurement, public records and policy",
            "home": "/government",
            "docs_url": None,
        },
        {
            "id": "taxes",
            "label": "Taxes",
            "status": "planned",
            "blurb": "Rules, filings, jurisdictions, incentives and compliance signals",
            "home": "/taxes",
            "docs_url": None,
        },
        {
            "id": "healthcare",
            "label": "Healthcare/Medical",
            "status": "planned",
            "blurb": "Providers, facilities, claims, treatments, pharma and clinical signals",
            "home": "/healthcare",
            "docs_url": None,
        },
        {
            "id": "people",
            "label": "People",
            "status": "planned",
            "blurb": "Individuals, roles, relationships, affiliations and influence signals",
            "home": "/people",
            "docs_url": None,
        },
        {
            "id": "geography",
            "label": "Geography",
            "status": "planned",
            "blurb": "Places, regions, borders, corridors and spatial economic signals",
            "home": "/geography",
            "docs_url": None,
        },
        {
            "id": "politics",
            "label": "Politics",
            "status": "planned",
            "blurb": "Campaigns, officials, legislation, elections and civic power signals",
            "home": "/politics",
            "docs_url": None,
        },
        {
            "id": "nonprofit",
            "label": "Non-profit",
            "status": "planned",
            "blurb": "Orgs, missions, funding, grants, programs and civic initiatives",
            "home": "/nonprofit",
            "docs_url": None,
        },
        {
            "id": "news",
            "label": "News",
            "status": "planned",
            "blurb": "Published events, claims, organizations, people and developing stories",
            "home": None,
            "docs_url": None,
        },
        {
            "id": "real_estate",
            "label": "Real Estate",
            "status": "planned",
            "blurb": "Parcels, buildings, owners, liens, zoning, permits and transactions",
            "home": "/real-estate",
            "docs_url": None,
        },
        {
            "id": "trademarks",
            "label": "Trademarks",
            "status": "active",
            "blurb": "Marks, owners, classes, status, prosecution history and related brands",
            "home": "/trademarks/sources",
            "docs_url": None,
        },
        {
            "id": "domain_names",
            "label": "Domains",
            "status": "active",
            "blurb": "www, .net and other TLDs — registries, WHOIS, DNS, availability and ownership",
            "home": "/domain-names/sources",
            "docs_url": None,
        },
        {
            "id": "patents",
            "label": "Patents",
            "status": "planned",
            "blurb": "Applications, grants, claims, inventors, assignees, citations and legal status",
            "home": None,
            "docs_url": None,
        },
        {
            "id": "songs",
            "label": "Songs",
            "status": "planned",
            "blurb": "Musical compositions and associated writers, publishers and rights",
            "home": None,
            "docs_url": None,
        },
        {
            "id": "music",
            "label": "Music",
            "status": "planned",
            "blurb": "Sound recordings, releases, artists, labels and catalogs",
            "home": None,
            "docs_url": None,
        },
        {
            "id": "books",
            "label": "Books",
            "status": "planned",
            "blurb": "Published works, editions, authors, publishers, rights and sales signals",
            "home": None,
            "docs_url": None,
        },
        {
            "id": "movies",
            "label": "Movies",
            "status": "planned",
            "blurb": "Films, television, video works, production entities and distribution rights",
            "home": None,
            "docs_url": None,
        },
        {
            "id": "fiction",
            "label": "Fiction",
            "status": "planned",
            "blurb": "Unpublished or independently created stories, characters, settings and story worlds",
            "home": None,
            "docs_url": None,
        },
    ]
    control_planes.sort(key=lambda p: p["label"])

    return SystemStatusOut(processes=processes, control_planes=control_planes)


@router.post("/processes/{process_id}/start")
async def start_process(process_id: str):
    """Dev-only: start Redis or Celery in a new console window."""
    settings = get_settings()
    py = str(VENV_PY) if VENV_PY.exists() else sys.executable

    if process_id == "redis":
        if not REDIS_START.exists():
            raise HTTPException(status_code=404, detail="start-redis.ps1 not found")
        subprocess.Popen(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REDIS_START),
            ],
            cwd=str(REDIS_START.parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        return {"ok": True, "started": "redis"}

    if process_id == "celery":
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{WORKERS_DIR};{API_DIR}"
        creation = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        subprocess.Popen(
            [
                py,
                "-m",
                "celery",
                "-A",
                "celery_app.celery_app",
                "worker",
                "-l",
                "info",
                "-Q",
                "discovery,acquisition,transcription,intelligence,default",
                "--pool=solo",
            ],
            cwd=str(WORKERS_DIR),
            env=env,
            creationflags=creation,
        )
        return {"ok": True, "started": "celery"}

    if process_id == "web":
        web = ROOT / "web"
        creation = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(web),
            shell=True,
            creationflags=creation,
        )
        return {"ok": True, "started": "web"}

    raise HTTPException(
        status_code=400,
        detail=f"Cannot start '{process_id}' from API. Start it from .startup / a terminal.",
    )
