# Redis (local + live)

Celery broker/results use Redis. Local and live share the **same URL shape** — only the host changes.

```
REDIS_URL=redis://HOST:6379/0
CELERY_BROKER_URL=redis://HOST:6379/0
CELERY_RESULT_BACKEND=redis://HOST:6379/1
```

## Local (Windows)

Portable Redis under this folder (binary is gitignored; install once):

```powershell
cd C:\AIProjects\intelligence\v2\infra\redis
.\install-redis.ps1   # first time only
.\start-redis.ps1     # 127.0.0.1:6379
# .\stop-redis.ps1
```

Dev `.env` uses `HOST=127.0.0.1`. This is the stack Redis workers will hit on a live Linux/managed host — not a PHP stack Redis.

## Live server (Linux)

Install distro Redis or a managed service, bind/firewall as you need, then point env at that host:

```
CELERY_BROKER_URL=redis://YOUR_REDIS_HOST:6379/0
CELERY_RESULT_BACKEND=redis://YOUR_REDIS_HOST:6379/1
```

Local Windows Redis is **dev-only**. Production = Linux Redis or managed Redis with the URLs above.
