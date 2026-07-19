import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import os from "os";

const V2_ROOT = path.resolve(process.cwd(), "..");
const VENV_PY = path.join(V2_ROOT, ".venv", "Scripts", "python.exe");
const API_DIR = path.join(V2_ROOT, "api");
const WORKERS_DIR = path.join(V2_ROOT, "workers");
const WEB_DIR = path.join(V2_ROOT, "web");
const REDIS_START = path.join(V2_ROOT, "infra", "redis", "start-redis.ps1");
const PLAYWRIGHT_BROWSERS = path.join(V2_ROOT, "infra", "playwright-browsers");

/** Open a titled cmd window that keeps running (Windows). */
function startInConsole(title: string, cwd: string, lines: string[]) {
  // ASCII-only title — middle-dots/colons confuse `start` / `title` on some shells.
  const safeTitle = title.replace(/[^\w\s.-]/g, " ").replace(/\s+/g, " ").trim() || "MI";
  const batPath = path.join(
    os.tmpdir(),
    `mi-stack-${safeTitle.replace(/\s+/g, "-").toLowerCase()}-${Date.now()}.cmd`
  );
  const body = [
    "@echo off",
    `title ${safeTitle}`,
    `cd /d "${cwd}"`,
    `echo.`,
    `echo === ${safeTitle} ===`,
    `echo.`,
    ...lines,
    "",
  ].join("\r\n");
  fs.writeFileSync(batPath, body, "utf8");

  // `start "title" cmd /k bat` — first quoted arg is always the window title.
  const child = spawn("cmd.exe", ["/c", "start", safeTitle, "cmd.exe", "/k", batPath], {
    cwd,
    detached: true,
    stdio: "ignore",
    windowsHide: false,
  });
  child.unref();
  return child.pid ?? null;
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const id = String(body.id || "");

  if (id === "redis") {
    if (!fs.existsSync(REDIS_START)) {
      return NextResponse.json({ detail: "start-redis.ps1 missing" }, { status: 404 });
    }
    const pid = startInConsole("MI Redis", path.dirname(REDIS_START), [
      `powershell -ExecutionPolicy Bypass -File "${REDIS_START}"`,
    ]);
    return NextResponse.json({ ok: true, started: "redis", pid });
  }

  if (id === "celery" || id === "workers") {
    if (!fs.existsSync(VENV_PY)) {
      return NextResponse.json({ detail: "v2/.venv python missing" }, { status: 404 });
    }
    const pid = startInConsole("MI Celery Worker", WORKERS_DIR, [
      `set PYTHONPATH=${WORKERS_DIR};${API_DIR}`,
      `set PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS}`,
      `"${VENV_PY}" -m celery -A celery_app.celery_app worker -l info -Q discovery,acquisition,transcription,intelligence,default --pool=solo`,
    ]);
    return NextResponse.json({ ok: true, started: "celery", pid });
  }

  if (id === "celery_beat" || id === "beat") {
    if (!fs.existsSync(VENV_PY)) {
      return NextResponse.json({ detail: "v2/.venv python missing" }, { status: 404 });
    }
    const pid = startInConsole("MI Celery Beat", WORKERS_DIR, [
      `set PYTHONPATH=${WORKERS_DIR};${API_DIR}`,
      `"${VENV_PY}" -m celery -A celery_app.celery_app beat -l info`,
    ]);
    return NextResponse.json({ ok: true, started: "celery_beat", pid });
  }

  if (id === "api") {
    if (!fs.existsSync(VENV_PY)) {
      return NextResponse.json({ detail: "v2/.venv python missing" }, { status: 404 });
    }
    const pid = startInConsole("MI API 8000", API_DIR, [
      `set PYTHONPATH=${API_DIR};${WORKERS_DIR}`,
      `"${VENV_PY}" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`,
    ]);
    return NextResponse.json({ ok: true, started: "api", pid });
  }

  if (id === "web") {
    const pid = startInConsole("MI Web 3000", WEB_DIR, ["npm run dev"]);
    return NextResponse.json({ ok: true, started: "web", pid });
  }

  return NextResponse.json({ detail: `Unknown process '${id}'` }, { status: 400 });
}
