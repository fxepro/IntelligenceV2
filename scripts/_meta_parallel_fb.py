"""Parallel FB duration/size backfill — many yt-dlp calls at once, not serial hours."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())

WORKERS = int(os.environ.get("META_BACKFILL_WORKERS", "16"))


def _estimate_size(duration: int, info: dict | None = None) -> int:
    if info:
        from app.services.discover_media import _file_size_bytes

        got = _file_size_bytes(info)
        if got:
            return got
    return max(1, int(1200.0 * float(duration) * 1000 / 8))


def _fetch(url: str, opts: dict) -> dict | None:
    import tempfile
    import yt_dlp

    # Don't share one cookiefile across threads — concurrent writes corrupt it.
    local = {**opts, "quiet": True, "no_warnings": True}
    cookie = local.get("cookiefile")
    tmp_path = None
    if cookie and Path(cookie).is_file():
        raw = Path(cookie).read_text(encoding="utf-8", errors="ignore")
        if "Netscape" in raw or "# HttpOnly_" in raw or raw.startswith("#"):
            fd, tmp_path = tempfile.mkstemp(prefix="mi-fb-cookie-", suffix=".txt")
            os.close(fd)
            Path(tmp_path).write_text(raw, encoding="utf-8")
            local["cookiefile"] = tmp_path
        else:
            local.pop("cookiefile", None)
    try:
        with yt_dlp.YoutubeDL(local) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass


def main() -> None:
    from app.services.discover_media import _published_at, _ydl_opts

    name_filter = sys.argv[1] if len(sys.argv) > 1 else None
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    list_sql = text(
        """
        SELECT r.id::text, r.canonical_url, s.name, r.fields
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media'
          AND s.platform = 'facebook'
          AND NULLIF(r.fields->>'duration_seconds','null') IS NULL
          AND (
            CAST(:name AS text) IS NULL
            OR s.name ILIKE '%' || CAST(:name AS text) || '%'
          )
        ORDER BY s.name
        """
    )
    with eng.connect() as c:
        rows = list(c.execute(list_sql, {"name": name_filter}))
    print(f"missing duration: {len(rows)} workers={WORKERS} filter={name_filter!r}", flush=True)
    if not rows:
        return

    opts = _ydl_opts(rows[0].canonical_url, skip_download=True)
    ok = fail = 0
    updates: list[tuple[str, dict]] = []

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(_fetch, row.canonical_url, opts): row for row in rows}
        done_n = 0
        for fut in as_completed(futs):
            row = futs[fut]
            done_n += 1
            info = fut.result()
            if not info or not info.get("duration"):
                fail += 1
            else:
                duration = int(float(info["duration"]))
                fields = dict(row.fields or {})
                fields["duration_seconds"] = duration
                fields["file_size_bytes"] = _estimate_size(duration, info)
                if info.get("view_count") is not None and not fields.get("view_count"):
                    fields["view_count"] = int(info["view_count"])
                pub = _published_at(info)
                if pub and not fields.get("published_at"):
                    fields["published_at"] = pub
                updates.append((row.id, fields))
                ok += 1
            if done_n % 25 == 0 or done_n == len(rows):
                print(f"  … {done_n}/{len(rows)} ok={ok} fail={fail}", flush=True)

    upd = text(
        "UPDATE records SET fields = CAST(:fields AS jsonb) WHERE id = CAST(:id AS uuid)"
    )
    with eng.begin() as c:
        for rid, fields in updates:
            c.execute(upd, {"id": rid, "fields": json.dumps(fields)})
    print(f"wrote {len(updates)} rows (ok={ok} fail={fail})", flush=True)


if __name__ == "__main__":
    main()
