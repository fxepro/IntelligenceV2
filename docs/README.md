# v2 local notes

Canonical architecture: [`../../docs/New Intelligence Platform Architecture.md`](../../docs/New%20Intelligence%20Platform%20Architecture.md)

## Run model

**Python venv + local Postgres/Redis** — same as v1. Docker is not part of the day-to-day workflow.

## Phase A checklist

- [x] Repo split: `v1/` backstop, `v2/` active
- [x] FastAPI control plane (health, sources, jobs, records, credentials)
- [x] Enqueue-only discover / process endpoints
- [x] Celery discovery worker with real connectors (YT / RSS / website / Facebook)
- [x] First-class `jobs` + shared `records` / `sources` / `platform_credentials`
- [x] Research providers ported + Settings Access UI
- [x] Minimal web operator UI
- [ ] Acquisition / transcription / intelligence pipeline (still stubs)
- [ ] Alembic migrations (currently `create_all` on API startup)

## Local ports

| Service | Port |
| --- | --- |
| API | 8000 |
| Web | 3000 |
| Postgres | 5432 — empty DB `intelligence` (v2 builds tables here) |
| Redis | 6379 |
