# v2 — Media Intelligence (ACTIVE)

**Status: active build.** Implements the v2 architecture:

→ [`../docs/New Intelligence Platform Architecture.md`](../docs/New%20Intelligence%20Platform%20Architecture.md)

## Topology

```text
web (Next.js)
   → api (FastAPI control plane)     # enqueue + CRUD + reads only
        → PostgreSQL (local)
        → Redis (local, for Celery)
             → workers (Celery in same venv)
                  discovery | acquisition | transcription | intelligence
```

**Rule:** long-running work never runs inside an HTTP request. APIs enqueue a job and return `job_id`.

**Local run = Python venv** (same as v1). No Docker required.

## Layout

```text
v2/
├── api/           # FastAPI control plane
├── workers/       # Celery workers
├── web/           # Next.js UI
├── docs/
├── .venv/         # create locally (gitignored)
└── .env.example
```

## Setup (once)

Empty Postgres DB **`intelligence`** (credentials in `.env.local`). First API start creates v2 tables.

> **Python standard: 3.14 only.** Use  
> `C:\Users\fxepro\AppData\Local\Python\pythoncore-3.14-64\python.exe`  
> Do not use OSGeo4W or any other interpreter for v2. Redis: `infra/redis` only (same URL shape as live).

```powershell
cd v2

# Create venv (only if missing):
& "C:\Users\fxepro\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m venv .venv

.\.venv\Scripts\Activate.ps1
python --version   # must be 3.14.x
pip install -r api\requirements.txt
```

## Run (three terminals)

Always activate the venv first (or call `.venv\Scripts\...` directly):

```powershell
cd v2
.\.venv\Scripts\Activate.ps1
```

**API**

```powershell
cd v2\api
$env:PYTHONPATH = "$PWD;$PWD\..\workers"
python -m uvicorn app.main:app --reload --port 8000
# http://localhost:8000/docs
```

**Worker**

```powershell
cd v2\workers
$env:PYTHONPATH = "$PWD;$PWD\..\api"
python -m celery -A celery_app.celery_app worker -l info -Q discovery,acquisition,transcription,intelligence,default
```

**Web**

```powershell
cd v2\web
npm install
npm run dev
# http://localhost:3000
```

## Phase A focus

1. Landing + Research / Sources / Intelligence UI in `web/` (ported from v1)
2. First-class `jobs` + enqueue Discover
3. Wire real discovery connectors into workers next
4. Port full research providers (YouTube / Facebook / web) next
