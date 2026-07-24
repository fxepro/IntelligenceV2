"""Acquisition worker — Library refresh + NameBright portfolio sync."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from celery_app import celery_app
from db import mark_completed, mark_failed, mark_running, session_scope

V2_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = V2_ROOT / "api" / "scripts" / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(f"Script not found: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _refresh_library_course(course_id: str) -> dict:
    key = (course_id or "").strip().lower()
    if key in ("soc-2-compliance", "scytale", "scytale-soc2"):
        return _load_script("download_scytale_soc2").run()
    if key in ("drata-soc-2", "drata", "drata-soc2"):
        return _load_script("download_drata_soc2").run()
    raise ValueError(
        f"No library refresh scraper for course_id={course_id!r} "
        "(supported: soc-2-compliance, drata-soc-2)"
    )


@celery_app.task(name="tasks.acquisition.run_acquire", bind=True, max_retries=1)
def run_acquire(self, job_id: str):
    action = ""
    course_id = ""
    try:
        with session_scope() as session:
            job = mark_running(session, job_id)
            payload = job.payload or {}
            action = (payload.get("action") or "").strip().lower()
            course_id = (payload.get("course_id") or "").strip()

        if action == "library_refresh":
            if not course_id:
                raise ValueError("library_refresh requires course_id")
            result = _refresh_library_course(course_id)
            if not isinstance(result, dict) or result.get("total") is None:
                raise RuntimeError(f"library_refresh returned invalid result: {result!r}")
            with session_scope() as session:
                mark_completed(session, job_id, result)
            return {"job_id": job_id, **result}

        if action == "namebright_portfolio_sync":
            from app.services.namebright_sync import sync_portfolio

            fetch_dns = bool((payload or {}).get("fetch_dns"))
            with session_scope() as session:
                result = sync_portfolio(session, fetch_dns=fetch_dns)
                mark_completed(session, job_id, result)
            return {"job_id": job_id, **result}

        if action == "namebright_dns_sync":
            from app.services.namebright_sync import sync_domain_dns

            domain_name = str((payload or {}).get("domain_name") or "").strip()
            if not domain_name:
                raise ValueError("namebright_dns_sync requires domain_name")
            with session_scope() as session:
                result = sync_domain_dns(session, domain_name)
                mark_completed(session, job_id, result)
            return {"job_id": job_id, **result}

        with session_scope() as session:
            mark_completed(
                session,
                job_id,
                {
                    "note": "acquisition stub",
                    "hint": "Pass payload.action=library_refresh, namebright_portfolio_sync, or namebright_dns_sync",
                },
            )
        return {"job_id": job_id, "ok": True, "note": "acquisition stub"}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        if action in ("library_refresh", "namebright_portfolio_sync", "namebright_dns_sync"):
            return {"job_id": job_id, "ok": False, "error": str(exc)}
        raise self.retry(exc=exc, countdown=60)
