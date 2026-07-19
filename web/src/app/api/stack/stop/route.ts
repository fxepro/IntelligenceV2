import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";

const execFileAsync = promisify(execFile);
const V2_ROOT = path.resolve(process.cwd(), "..");
const REDIS_STOP = path.join(V2_ROOT, "infra", "redis", "stop-redis.ps1");
const WEB_DIR = path.join(V2_ROOT, "web");

async function ps(command: string) {
  const { stdout, stderr } = await execFileAsync(
    "powershell.exe",
    ["-NoProfile", "-Command", command],
    { timeout: 20000, windowsHide: true }
  );
  return { stdout: String(stdout || ""), stderr: String(stderr || "") };
}

/** Kill whoever is listening on a local TCP port (and optional parent). */
async function killPort(port: number) {
  return ps(`
    $pids = @(Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($pid in $pids) {
      if (-not $pid -or $pid -le 4) { continue }
      # Kill process tree (uvicorn --reload has parent + worker)
      taskkill /PID $pid /T /F 2>$null | Out-Null
      Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    'killed_ports=' + ($pids -join ',')
  `);
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const id = String(body.id || "");

  try {
    if (id === "redis") {
      if (fs.existsSync(REDIS_STOP)) {
        await execFileAsync(
          "powershell.exe",
          ["-ExecutionPolicy", "Bypass", "-File", REDIS_STOP],
          { timeout: 15000, windowsHide: true }
        );
      }
      // Also clear :6379 in case stop script missed it
      const r = await killPort(6379);
      return NextResponse.json({ ok: true, stopped: "redis", detail: r.stdout.trim() });
    }

    if (id === "celery" || id === "workers") {
      const r = await ps(`
        $killed = @()
        Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
          Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match 'celery' -and
            $_.CommandLine -match 'worker' -and
            $_.CommandLine -notmatch 'beat'
          } |
          ForEach-Object {
            taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += $_.ProcessId
          }
        'killed_celery=' + ($killed -join ',')
      `);
      return NextResponse.json({ ok: true, stopped: "celery", detail: r.stdout.trim() });
    }

    if (id === "celery_beat" || id === "beat") {
      const r = await ps(`
        $killed = @()
        Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
          Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match 'celery' -and
            $_.CommandLine -match 'beat'
          } |
          ForEach-Object {
            taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += $_.ProcessId
          }
        'killed_celery_beat=' + ($killed -join ',')
      `);
      return NextResponse.json({ ok: true, stopped: "celery_beat", detail: r.stdout.trim() });
    }

    if (id === "api") {
      // 1) Kill anything listening on API port
      const byPort = await killPort(8000);
      // 2) Kill stray uvicorn / app.main processes (reloader orphans)
      const byCmd = await ps(`
        $killed = @()
        Get-CimInstance Win32_Process |
          Where-Object {
            $_.CommandLine -and (
              ($_.CommandLine -match 'uvicorn' -and $_.CommandLine -match 'app\\.main') -or
              ($_.CommandLine -match 'uvicorn' -and $_.CommandLine -match 'port 8000')
            )
          } |
          ForEach-Object {
            taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += $_.ProcessId
          }
        'killed_uvicorn=' + ($killed -join ',')
      `);
      return NextResponse.json({
        ok: true,
        stopped: "api",
        detail: `${byPort.stdout.trim()}; ${byCmd.stdout.trim()}`,
      });
    }

    if (id === "web") {
      const byPort = await killPort(3000);
      const webEsc = WEB_DIR.replace(/'/g, "''");
      const byCmd = await ps(`
        $root = '${webEsc}'
        $killed = @()
        Get-CimInstance Win32_Process |
          Where-Object {
            $_.CommandLine -and
            ($_.CommandLine -match 'next' -or $_.CommandLine -match 'node' -or $_.CommandLine -match 'npm') -and
            $_.CommandLine -like ('*' + $root + '*')
          } |
          ForEach-Object {
            taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += $_.ProcessId
          }
        'killed_web=' + ($killed -join ',')
      `);
      return NextResponse.json({
        ok: true,
        stopped: "web",
        detail: `${byPort.stdout.trim()}; ${byCmd.stdout.trim()}`,
        note: "Stopping web ends the Next server; reopen Settings after Start.",
      });
    }

    return NextResponse.json({ detail: `Unknown process '${id}'` }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ detail: e?.message ?? "Stop failed" }, { status: 500 });
  }
}
