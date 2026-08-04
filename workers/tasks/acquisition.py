"""Acquisition worker — Library refresh + NameBright portfolio sync."""
from __future__ import annotations

import importlib.util
import json
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


def _course_data_dir(course_id: str) -> Path:
    from app.services.library_course_paths import course_data_dir

    return course_data_dir(course_id)


def _acquire_article_bodies(course_id: str) -> dict:
    """Generic manifest-based body fetch for any article_hub destination."""
    from app.services.article_acquire import run_acquire_bodies

    out = _course_data_dir(course_id)
    manifest_path = out / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No manifest at {manifest_path} — run Discover first")
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not any(r.get("url") for r in rows if isinstance(r, dict)):
        raise ValueError("manifest.json has no article URLs — run Discover first")
    return run_acquire_bodies(out_dir=out)


def _refresh_library_course(course_id: str) -> dict:
    """Full re-download for legacy scripted courses, or generic acquire when manifest exists."""
    key = (course_id or "").strip().lower()
    out = _course_data_dir(key)
    manifest_path = out / "manifest.json"

    if manifest_path.is_file():
        try:
            rows = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            rows = []
        if isinstance(rows, list) and any(r.get("url") for r in rows if isinstance(r, dict)):
            return _acquire_article_bodies(key)

    # Legacy full BFS scripts when no discover manifest yet
    if key in ("soc-2-compliance", "scytale", "scytale-soc2"):
        return _load_script("download_scytale_soc2").run()
    if key in ("drata-soc-2", "drata", "drata-soc2", "drata-soc-2-learn"):
        mod = _load_script("download_drata_soc2")
        if hasattr(mod, "run"):
            return mod.run(out_dir=out)
        return mod.run()

    raise ValueError(
        f"No lessons to acquire for course_id={course_id!r} — run Discover first or add a refresh script"
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
            job_source_id = job.source_id

        if action == "library_refresh":
            if not course_id:
                raise ValueError("library_refresh requires course_id")
            result = _refresh_library_course(course_id)
            if not isinstance(result, dict) or result.get("total") is None:
                raise RuntimeError(f"library_refresh returned invalid result: {result!r}")
            with session_scope() as session:
                mark_completed(session, job_id, result)
            return {"job_id": job_id, **result}

        if action == "library_acquire_articles":
            sid = (payload.get("source_id") or "").strip()
            cid = (payload.get("course_id") or course_id or "").strip()
            if not cid:
                raise ValueError("library_acquire_articles requires course_id")
            result = _acquire_article_bodies(cid)
            if not isinstance(result, dict) or result.get("total") is None:
                raise RuntimeError(f"library_acquire_articles returned invalid result: {result!r}")
            if sid:
                from uuid import UUID

                from app.services.library_source_lessons import sync_lessons_from_disk

                with session_scope() as session:
                    sync_lessons_from_disk(session, source_id=UUID(sid), course_id=cid)
                    session.commit()
            with session_scope() as session:
                mark_completed(session, job_id, {**result, "action": action, "source_id": sid})
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

        if action == "sam_gov_opportunities_sync":
            from uuid import UUID

            from app.services.sam_gov_sync import sync_opportunities

            sid = payload.get("source_id") or job_source_id
            if not sid:
                raise ValueError("sam_gov_opportunities_sync requires source_id")
            with session_scope() as session:
                result = sync_opportunities(
                    session,
                    source_id=UUID(str(sid)),
                    posted_from=(payload or {}).get("posted_from"),
                    posted_to=(payload or {}).get("posted_to"),
                    limit=int((payload or {}).get("limit") or 100),
                    max_pages=int((payload or {}).get("max_pages") or 1),
                )
                mark_completed(session, job_id, result)
            return {"job_id": job_id, **result}

        with session_scope() as session:
            mark_completed(
                session,
                job_id,
                {
                    "note": "acquisition stub",
                    "hint": "Pass payload.action=library_refresh, library_acquire_articles, namebright_portfolio_sync, namebright_dns_sync, or sam_gov_opportunities_sync",
                },
            )
        return {"job_id": job_id, "ok": True, "note": "acquisition stub"}
    except Exception as exc:
        with session_scope() as session:
            mark_failed(session, job_id, f"{type(exc).__name__}: {exc}")
        if action in ("library_refresh", "library_acquire_articles", "namebright_portfolio_sync", "namebright_dns_sync", "sam_gov_opportunities_sync"):
            return {"job_id": job_id, "ok": False, "error": str(exc)}
        raise self.retry(exc=exc, countdown=60)
